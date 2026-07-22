#!/usr/bin/env python3
"""URJA — Comprehensive Seed Data Script

Populates the database with realistic sample data for a 50MW solar farm
in Rajasthan, India. Designed to give buyers a fully populated dashboard
immediately after deployment.

Usage:
    python scripts/seed.py

Idempotent: deletes all existing data before inserting fresh data.
"""

import asyncio
import hashlib
import json
import math
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

_backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(_backend_dir))

from passlib.context import CryptContext
from sqlalchemy import delete, insert, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory, engine
from app.models import (
    Organization, User, ApiKey,
    AssetSite, Asset, AssetRelationship,
    TelemetryGeneration, TelemetryWeather, GridPrice,
    CurtailmentEvent, DispatchRule, DispatchDecision,
    CarbonCredit, HealthMetric, HealthAlert, MaintenanceWorkOrder,
    Setting,
)
from app.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()

RNG = random.Random(42)
NOW = datetime.now(timezone.utc)

DELETE_ORDER = [
    DispatchDecision, DispatchRule, CurtailmentEvent,
    TelemetryGeneration, TelemetryWeather, GridPrice,
    HealthMetric, HealthAlert, MaintenanceWorkOrder,
    CarbonCredit, AssetRelationship, Asset, AssetSite,
    ApiKey, User, Setting, Organization,
]


def _solar_power_factor(hour: int, minute: int) -> float:
    t = hour + minute / 60.0
    if t < 6.0 or t > 18.0:
        return 0.0
    normalized = (t - 6.0) / 12.0
    return math.sin(normalized * math.pi) ** 2


def _make_timestamps_15min(start: datetime, days: int) -> list[datetime]:
    ts = []
    cursor = start.replace(minute=0, second=0, microsecond=0)
    end = cursor + timedelta(days=days)
    while cursor < end:
        for minute in (0, 15, 30, 45):
            stamp = cursor.replace(minute=minute)
            if stamp >= start:
                ts.append(stamp)
        cursor += timedelta(hours=1)
    return ts


def _make_hourly_timestamps(start: datetime, days: int) -> list[datetime]:
    ts = []
    cursor = start.replace(minute=0, second=0, microsecond=0)
    end = cursor + timedelta(days=days)
    while cursor < end:
        ts.append(cursor)
        cursor += timedelta(hours=1)
    return ts


def _compute_credit_hash(previous_hash: str, credit_data: dict) -> str:
    payload = previous_hash + json.dumps(credit_data, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


async def delete_all_data(session: AsyncSession) -> None:
    for table in DELETE_ORDER:
        await session.execute(delete(table))
    await session.commit()
    print("\u2705 All existing data deleted")


async def create_organization(session: AsyncSession) -> Organization:
    org = Organization(
        name="GreenEnergy Corp",
        slug="greenenergy-corp",
        logo_url="https://example.com/logo.png",
        timezone="Asia/Kolkata",
        currency="INR",
        emission_factor=0.73,
        is_active=True,
        extra_metadata={"founded": "2024", "region": "India"},
    )
    session.add(org)
    await session.flush()
    print(f"\u2705 Organization created: {org.name} (id={org.id})")
    return org


async def create_users(session: AsyncSession, org: Organization) -> dict[str, User]:
    users_data = [
        ("admin@example.com", "admin123", "Admin User", "admin"),
        ("operator@example.com", "operator123", "Operator User", "operator"),
        ("viewer@example.com", "viewer123", "Viewer User", "viewer"),
    ]
    users = {}
    for email, password, display_name, role in users_data:
        user = User(
            organization_id=org.id,
            email=email,
            password_hash=pwd_context.hash(password),
            display_name=display_name,
            role=role,
            is_active=True,
            email_verified_at=NOW,
        )
        session.add(user)
        await session.flush()
        users[role] = user
    print(f"\u2705 Users created: {len(users)} ({', '.join(users.keys())})")
    return users


async def create_api_keys(session: AsyncSession, org: Organization, users: dict) -> list[ApiKey]:
    keys_data = [
        ("Admin API Key", "admin", "urja_adm_", users["admin"]),
        ("Operator API Key", "write", "urja_op_", users["operator"]),
        ("Viewer API Key", "read", "urja_vw_", users["viewer"]),
    ]
    api_keys = []
    for name, scope, prefix, user in keys_data:
        raw_key = f"{prefix}{uuid.uuid4().hex[:24]}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = ApiKey(
            organization_id=org.id,
            key_prefix=raw_key[:12],
            key_hash=key_hash,
            name=name,
            scope=scope,
            is_active=True,
        )
        session.add(api_key)
        await session.flush()
        api_keys.append(api_key)
    print(f"\u2705 API keys created: {len(api_keys)}")
    return api_keys


async def create_site(session: AsyncSession, org: Organization) -> AssetSite:
    site = AssetSite(
        organization_id=org.id,
        name="Rajasthan Solar Farm",
        code="RJ-SOLAR-001",
        description="50MW solar photovoltaic farm in Rajasthan, India",
        address="Jodhpur District, Rajasthan, India",
        latitude=26.5,
        longitude=73.0,
        capacity_mw=50.0,
        timezone="Asia/Kolkata",
        status="active",
        extra_metadata={"solar_irradiance_avg": 5.5, "commission_year": 2024},
    )
    session.add(site)
    await session.flush()
    print(f"\u2705 Site created: {site.name} ({site.capacity_mw} MW)")
    return site


async def create_assets(
    session: AsyncSession, org: Organization, site: AssetSite,
) -> dict:
    assets = {}
    inverters = []
    panel_strings = []
    battery = None
    meter = None

    for i in range(1, NUM_INVERTERS + 1):
        inv = Asset(
            organization_id=org.id,
            site_id=site.id,
            asset_type="inverter",
            name=f"Inverter INV-{i:03d}",
            code=f"INV-{i:03d}",
            serial_number=f"SN-INV-{i:03d}-{RNG.randint(1000, 9999)}",
            manufacturer="SMA Solar Technology AG",
            model="STP-1000TL-US-10",
            capacity_kw=1000.0,
            latitude=round(SITE_LAT + RNG.uniform(-0.01, 0.01), 6),
            longitude=round(SITE_LNG + RNG.uniform(-0.01, 0.01), 6),
            commissioning_date=(NOW - timedelta(days=730)).date(),
            status="active",
            health_score=round(RNG.uniform(88, 100), 2),
            config={
                "max_power_kw": 1000,
                "efficiency": 0.985,
                "mppt_tracking": True,
                "string_count": PANELS_PER_INVERTER,
            },
        )
        session.add(inv)
        await session.flush()
        inverters.append(inv)

    for inv_idx, inv in enumerate(inverters):
        start = inv_idx * PANELS_PER_INVERTER + 1
        end = start + PANELS_PER_INVERTER - 1
        for p in range(start, end + 1):
            panel = Asset(
                organization_id=org.id,
                site_id=site.id,
                parent_asset_id=inv.id,
                asset_type="solar_panel",
                name=f"String ST-{p:05d}",
                code=f"ST-{p:05d}",
                serial_number=f"SN-STR-{p:05d}-{RNG.randint(1000, 9999)}",
                manufacturer="Trina Solar",
                model="TSM-540DE09.05",
                capacity_kw=10.0,
                commissioning_date=(NOW - timedelta(days=730)).date(),
                status="active",
                health_score=round(RNG.uniform(90, 100), 2),
                config={
                    "wattage": 10000,
                    "tilt_angle": 28,
                    "azimuth": 180,
                    "technology": "monocrystalline",
                },
            )
            session.add(panel)
            await session.flush()
            panel_strings.append(panel)

    battery = Asset(
        organization_id=org.id,
        site_id=site.id,
        asset_type="battery_storage",
        name="Battery Storage System",
        code="BAT-001",
        serial_number=f"SN-BAT-001-{RNG.randint(1000, 9999)}",
        manufacturer="Tesla",
        model="Megapack 2XL",
        capacity_kw=20000.0,
        commissioning_date=(NOW - timedelta(days=365)).date(),
        status="active",
        health_score=97.5,
        config={
            "capacity_mwh": 80,
            "max_charge_rate_mw": 20,
            "max_discharge_rate_mw": 20,
            "chemistry": "LFP",
            "round_trip_efficiency": 0.92,
            "min_soc_pct": 10,
            "max_soc_pct": 95,
        },
    )
    session.add(battery)
    await session.flush()

    meter = Asset(
        organization_id=org.id,
        site_id=site.id,
        asset_type="meter",
        name="Grid Interconnection Meter",
        code="METER-001",
        serial_number=f"SN-MTR-001-{RNG.randint(1000, 9999)}",
        manufacturer="Siemens",
        model="PAC4200",
        commissioning_date=(NOW - timedelta(days=730)).date(),
        status="active",
        health_score=99.0,
        config={
            "phase": "three",
            "accuracy_class": "0.5",
            "protocol": "IEC 61850",
        },
    )
    session.add(meter)
    await session.flush()

    assets["inverters"] = inverters
    assets["panel_strings"] = panel_strings
    assets["battery"] = battery
    assets["meter"] = meter

    total = len(inverters) + len(panel_strings) + 2
    print(f"\u2705 Assets created: {total} ({len(inverters)} inverters, {len(panel_strings)} strings, battery, meter)")
    return assets


async def create_relationships(
    session: AsyncSession, org: Organization, site: AssetSite, assets: dict,
) -> None:
    rels = []
    for idx, inv in enumerate(assets["inverters"]):
        rels.append(AssetRelationship(
            organization_id=org.id,
            parent_asset_id=site.id,
            child_asset_id=inv.id,
            relationship_type="contains",
            position_index=idx + 1,
        ))

    rels.append(AssetRelationship(
        organization_id=org.id,
        parent_asset_id=site.id,
        child_asset_id=assets["battery"].id,
        relationship_type="contains",
        position_index=51,
    ))
    rels.append(AssetRelationship(
        organization_id=org.id,
        parent_asset_id=site.id,
        child_asset_id=assets["meter"].id,
        relationship_type="monitors",
        position_index=52,
    ))

    for inv_idx, inv in enumerate(assets["inverters"]):
        start = inv_idx * PANELS_PER_INVERTER
        end = start + PANELS_PER_INVERTER
        for pos, panel in enumerate(assets["panel_strings"][start:end], 1):
            rels.append(AssetRelationship(
                organization_id=org.id,
                parent_asset_id=inv.id,
                child_asset_id=panel.id,
                relationship_type="feeds_into",
                position_index=pos,
            ))

    session.add_all(rels)
    await session.flush()
    print(f"\u2705 Asset relationships created: {len(rels)}")


async def insert_telemetry(
    session: AsyncSession, org: Organization, site: AssetSite, assets: dict,
    curtailment_windows: list[dict],
) -> None:
    inverters = assets["inverters"]
    start_ts = (NOW - timedelta(days=DAYS_OF_DATA)).replace(minute=0, second=0, microsecond=0)
    timestamps = _make_timestamps_15min(start_ts, DAYS_OF_DATA)
    total_readings = len(timestamps) * len(inverters)

    print(f"\U0001f331 Generating telemetry: {total_readings:,} readings across {len(inverters)} inverters...")

    curtailment_lookup: dict[tuple, bool] = {}
    for cw in curtailment_windows:
        for inv_id in cw["inverter_ids"]:
            curtailment_lookup[(cw["start_ts"], cw["end_ts"], inv_id)] = True

    def _is_curtailed(ts: datetime, inv_id: uuid.UUID) -> bool:
        for cw in curtailment_windows:
            if cw["start_ts"] <= ts < cw["end_ts"] and inv_id in cw["inverter_ids"]:
                return True
        return False

    telemetry_table = TelemetryGeneration.__table__
    batch_size = 5000
    rows = []
    inserted = 0

    for ts in timestamps:
        hour, minute = ts.hour, ts.minute
        base_factor = _solar_power_factor(hour, minute)
        has_sun = base_factor > 0

        for inv in inverters:
            gen_kw = 0.0
            energy_kwh = 0.0
            power_factor = round(RNG.uniform(0.90, 0.99), 4)
            voltage_v = round(RNG.uniform(390, 410), 2)
            frequency_hz = round(RNG.uniform(49.8, 50.2), 3)
            temp_c = round(RNG.uniform(45, 65), 2)
            quality = 0
            estimated = False

            if has_sun:
                if _is_curtailed(ts, inv.id):
                    gen_kw = round(RNG.uniform(5, 50), 4)
                    quality = 2
                    estimated = True
                else:
                    noise = RNG.gauss(0, 0.06)
                    factor = max(0.0, min(1.0, base_factor + noise))
                    cap = float(inv.capacity_kw or 1000)
                    gen_kw = round(factor * cap * 0.92, 4)
                    gen_kw = min(gen_kw, cap)
                current_a_val = 0.0
                if voltage_v > 0 and power_factor > 0:
                    pf = power_factor
                    current_a_val = round(
                        gen_kw * 1000.0 / (voltage_v * 1.732 * pf), 2
                    )
                energy_kwh = round(gen_kw * 0.25, 4)

            rows.append({
                "ts": ts,
                "asset_id": inv.id,
                "organization_id": org.id,
                "generation_kw": gen_kw,
                "energy_kwh": energy_kwh,
                "power_factor": power_factor if has_sun else 0.0,
                "voltage_v": voltage_v if has_sun else 0.0,
                "current_a": current_a_val if has_sun else 0.0,
                "frequency_hz": frequency_hz,
                "temperature_c": temp_c if has_sun else None,
                "is_estimated": estimated or (not has_sun),
                "quality_code": quality,
            })

            if len(rows) >= batch_size:
                await session.execute(insert(telemetry_table), rows)
                inserted += len(rows)
                rows = []

    if rows:
        await session.execute(insert(telemetry_table), rows)
        inserted += len(rows)

    await session.commit()
    print(f"\U0001f331 Telemetry inserted: {inserted:,} rows")


async def insert_weather(
    session: AsyncSession, org: Organization, site: AssetSite,
) -> None:
    start_ts = (NOW - timedelta(days=DAYS_OF_DATA)).replace(minute=0, second=0, microsecond=0)
    timestamps = _make_hourly_timestamps(start_ts, DAYS_OF_DATA)
    weather_table = TelemetryWeather.__table__
    rows = []

    for ts in timestamps:
        hour = ts.hour
        base_temp = 28.0 + 12.0 * math.sin(math.pi * (hour - 6) / 14)
        base_temp = max(25.0, min(45.0, base_temp))
        temp_c = round(base_temp + RNG.gauss(0, 2), 2)

        irradiance = _solar_power_factor(hour, 0) * RNG.uniform(700, 1050)
        irradiance = round(max(0, irradiance), 2)

        wind_speed = round(RNG.uniform(5, 25), 2)
        humidity = round(max(10, min(90, 60 - irradiance / 30 + RNG.gauss(0, 8))), 2)
        pressure = round(RNG.uniform(1005, 1015), 1)
        wind_dir = round(RNG.uniform(0, 359), 1)
        cloud_cover = round(max(0, min(100, 20 - irradiance / 50 + RNG.gauss(0, 12))), 2)
        precipitation = 0.0 if cloud_cover < 60 else round(RNG.uniform(0, 2), 2)

        rows.append({
            "ts": ts,
            "site_id": site.id,
            "organization_id": org.id,
            "temperature_c": temp_c,
            "humidity_pct": humidity,
            "pressure_hpa": pressure,
            "wind_speed_ms": wind_speed,
            "wind_direction_deg": wind_dir,
            "solar_irradiance_wpm2": irradiance,
            "cloud_cover_pct": cloud_cover,
            "precipitation_mm": precipitation,
            "is_forecast": False,
            "source": "openweather",
        })

    await session.execute(insert(weather_table), rows)
    await session.commit()
    print(f"\U0001f326 Weather data inserted: {len(rows):,} rows")


async def insert_grid_prices(
    session: AsyncSession, org: Organization, site: AssetSite,
) -> None:
    start_ts = (NOW - timedelta(days=DAYS_OF_DATA)).replace(minute=0, second=0, microsecond=0)
    timestamps = _make_hourly_timestamps(start_ts, DAYS_OF_DATA)
    price_table = GridPrice.__table__
    rows = []

    for ts in timestamps:
        hour = ts.hour
        peak_hours = 17 <= hour <= 22
        solar_hours = 8 <= hour <= 16
        off_hours = 23 <= hour or hour <= 5

        if peak_hours:
            base_price = RNG.uniform(5.5, 7.5)
        elif solar_hours:
            base_price = RNG.uniform(2.0, 4.0)
        else:
            base_price = RNG.uniform(1.5, 3.0)

        price = round(base_price + RNG.gauss(0, 0.3), 6)

        rows.append({
            "ts": ts,
            "site_id": site.id,
            "organization_id": org.id,
            "price_per_kwh": max(0.5, price),
            "currency": "INR",
            "source": "day_ahead",
            "market_region": "India-Rajasthan",
            "is_forecast": False,
        })

    await session.execute(insert(price_table), rows)
    await session.commit()
    print(f"\U0001f4b0 Grid prices inserted: {len(rows):,} rows")


async def insert_curtailment_events(
    session: AsyncSession, org: Organization, assets: dict,
    curtailment_windows: list[dict],
) -> list:
    inverters = assets["inverters"]
    events = []

    for cw in curtailment_windows:
        duration_hours = cw["duration_hours"]
        duration_minutes = int(duration_hours * 60)
        actual_kwh_total = 0.0
        expected_kwh_total = 0.0

        for inv in inverters:
            if inv.id in cw["inverter_ids"]:
                hour = cw["start_ts"].hour
                minute = cw["start_ts"].minute
                for h_offset in range(int(duration_hours)):
                    check_hour = hour + h_offset
                    if check_hour >= 24:
                        check_hour -= 24
                    factor = _solar_power_factor(check_hour, minute)
                    cap = float(inv.capacity_kw or 1000)
                    expected_per_hour = factor * cap * 0.92
                    expected_kwh_total += expected_per_hour
                    actual_kwh_total += RNG.uniform(2, 20)

        inv_target = inv
        for inv in inverters:
            if inv.id in cw["inverter_ids"]:
                inv_target = inv
                break

        curtailed_kwh = expected_kwh_total - actual_kwh_total
        price = round(RNG.uniform(3.5, 6.0), 4)
        revenue_lost = round(curtailed_kwh * price, 4)

        event = CurtailmentEvent(
            ts=cw["start_ts"],
            asset_id=inv_target.id,
            organization_id=org.id,
            duration_minutes=duration_minutes,
            expected_kwh=round(expected_kwh_total, 4),
            actual_kwh=round(actual_kwh_total, 4),
            curtailed_kwh=round(curtailed_kwh, 4),
            price_per_kwh=price,
            revenue_lost=revenue_lost,
            grid_price_source="day_ahead",
            is_resolved=cw["resolved"],
            resolved_at=cw["resolved_at"] if cw["resolved"] else None,
        )
        session.add(event)
        await session.flush()
        events.append(event)

    print(f"\u2705 Curtailment events created: {len(events)}")
    return events


async def insert_dispatch_rules(session: AsyncSession, org: Organization) -> list:
    rules_data = [
        {
            "name": "Battery Charge on Low Price",
            "description": "Charge battery when grid prices are below INR 2.5/kWh",
            "priority": 10,
            "condition_type": "price_below",
            "condition_config": {"threshold": 2.5, "currency": "INR"},
            "action": "charge_battery",
            "action_config": {"target_soc_pct": 90, "max_rate_kw": 5000},
            "target_asset_type": "battery_storage",
            "cooldown_minutes": 30,
        },
        {
            "name": "Battery Dispatch on Peak",
            "description": "Discharge battery to grid when prices exceed INR 7.0/kWh and SOC > 20%",
            "priority": 20,
            "condition_type": "price_above",
            "condition_config": {"threshold": 7.0, "currency": "INR"},
            "action": "discharge_battery",
            "action_config": {"min_soc_pct": 20, "max_rate_kw": 10000},
            "target_asset_type": "battery_storage",
            "cooldown_minutes": 15,
        },
        {
            "name": "Curtailment Shield",
            "description": "Route curtailed generation to compute load when curtailment detected",
            "priority": 5,
            "condition_type": "curtailment_detected",
            "condition_config": {"detection_window_min": 30},
            "action": "route_to_compute",
            "action_config": {"target_load_kw": 5000},
            "target_asset_type": "inverter",
            "cooldown_minutes": 10,
        },
    ]

    rules = []
    for rd in rules_data:
        rule = DispatchRule(organization_id=org.id, **rd)
        session.add(rule)
        await session.flush()
        rules.append(rule)

    print(f"\u2705 Dispatch rules created: {len(rules)}")
    return rules


async def insert_carbon_credits(
    session: AsyncSession, org: Organization, assets: dict, users: dict,
) -> None:
    num_months = 3
    credits = []
    previous_hash = "genesis"
    inverter_list = assets["inverters"]

    for month_offset in range(num_months, 0, -1):
        month_start = (NOW.replace(day=1) - timedelta(days=month_offset * 30)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1)

        days_in_month = (month_end - month_start).days
        daily_kwh_per_inverter = float(inverter_list[0].capacity_kw or 1000) * 7.5
        total_kwh = daily_kwh_per_inverter * days_in_month * len(inverter_list) * 0.92
        emission_factor = 0.73
        total_co2 = round(total_kwh / 1000.0 * emission_factor, 4)

        batch_id = uuid.uuid4()

        credit_data = {
            "quantity": total_co2,
            "total_kwh": total_kwh,
            "generation_start": month_start.isoformat(),
            "generation_end": month_end.isoformat(),
            "emission_factor": emission_factor,
        }
        current_hash = _compute_credit_hash(previous_hash, credit_data)

        credit = CarbonCredit(
            ts=month_start,
            organization_id=org.id,
            asset_id=inverter_list[0].id,
            batch_id=batch_id,
            status="active",
            quantity=total_co2,
            unit="tCO2e",
            methodology="IPMVP_v2.1",
            generation_start=month_start,
            generation_end=month_end,
            total_kwh=round(total_kwh, 4),
            emission_factor=emission_factor,
            registry_tx_id=current_hash,
            registry_url=f"https://registry.example.com/credits/{current_hash[:16]}",
            issued_by=users["admin"].id,
            notes=json.dumps({
                "previous_hash": previous_hash,
                "chain_index": 4 - month_offset,
                "methodology_version": "URJA-VCS-1.0",
            }),
            extra_metadata={
                "chain_hash": current_hash,
                "previous_hash": previous_hash,
                "batch_month": month_start.strftime("%Y-%m"),
            },
        )
        session.add(credit)
        await session.flush()
        credits.append(credit)
        previous_hash = current_hash

    print(f"\u2705 Carbon credits created: {len(credits)} batches ({sum(float(c.quantity) for c in credits):,.1f} tCO2e)")
    return credits


async def insert_health_metrics(
    session: AsyncSession, org: Organization, assets: dict,
) -> None:
    inverters = assets["inverters"]
    start_ts = (NOW - timedelta(days=DAYS_OF_DATA)).replace(hour=0, minute=0, second=0, microsecond=0)
    health_table = HealthMetric.__table__
    rows = []
    batch_size = 2000

    degrading_indices = {7, 23, 41}
    critical_index = 7

    for day_offset in range(DAYS_OF_DATA):
        day_ts = start_ts + timedelta(days=day_offset)
        progress = day_offset / DAYS_OF_DATA

        for idx, inv in enumerate(inverters):
            base_score = 95.0
            if idx in degrading_indices:
                base_score -= progress * 30
            if idx == critical_index and day_offset > 60:
                base_score -= 35 * max(0, (day_offset - 60) / 30)

            noise = RNG.gauss(0, 3)
            health = max(0, min(100, base_score + noise))
            anomaly = 0.0
            flags = []

            if health < 60:
                anomaly = round(RNG.uniform(0.2, 0.8), 6)
                flags.append("critical_anomaly")
            elif health < 80:
                anomaly = round(RNG.uniform(0.05, 0.2), 6)
                flags.append("performance_degradation")

            metric_scores = {
                "power_kw": round(min(100, health + RNG.gauss(0, 2)), 2),
                "temperature_c": round(min(100, health + RNG.gauss(0, 3)), 2),
                "voltage_v": round(min(100, health + RNG.gauss(0, 1)), 2),
            }

            rows.append({
                "ts": day_ts,
                "asset_id": inv.id,
                "organization_id": org.id,
                "health_score": round(health, 2),
                "anomaly_score": anomaly,
                "metric_scores": json.dumps(metric_scores),
                "anomaly_flags": flags,
                "alert_ids": [],
                "run_id": uuid.uuid4(),
            })

            if len(rows) >= batch_size:
                await session.execute(insert(health_table), rows)
                rows = []

    if rows:
        await session.execute(insert(health_table), rows)
    await session.commit()
    print(f"\U0001fa7a Health metrics inserted: {DAYS_OF_DATA * len(inverters):,} rows")


async def insert_health_alerts(
    session: AsyncSession, org: Organization, assets: dict, users: dict,
) -> list:
    inverters = assets["inverters"]
    alerts_data = [
        {
            "asset": inverters[2],
            "title": "Efficiency drop detected on INV-003",
            "description": "Power output efficiency declined by 12% over 7 days. Possible dust accumulation or soiling.",
            "severity": "warning",
            "status": "acknowledged",
            "acknowledged_by": users["operator"].id,
            "acknowledged_at": NOW - timedelta(days=5),
        },
        {
            "asset": inverters[14],
            "title": "Temperature elevation on INV-015",
            "description": "Operating temperature 8\u00b0C above baseline. Check cooling system and airflow.",
            "severity": "warning",
            "status": "acknowledged",
            "acknowledged_by": users["operator"].id,
            "acknowledged_at": NOW - timedelta(days=10),
        },
        {
            "asset": inverters[21],
            "title": "Efficiency drop detected on INV-022",
            "description": "Panel string mismatch detected. Efficiency reduced by 9%. Schedule inspection.",
            "severity": "warning",
            "status": "acknowledged",
            "acknowledged_by": users["admin"].id,
            "acknowledged_at": NOW - timedelta(days=2),
        },
        {
            "asset": inverters[6],
            "title": "Temperature anomaly on INV-007",
            "description": "Critical temperature spike detected (92\u00b0C). Immediate inspection required. Possible thermal runaway risk.",
            "severity": "critical",
            "status": "open",
            "acknowledged_by": None,
            "acknowledged_at": None,
        },
        {
            "asset": inverters[29],
            "title": "Power output anomaly on INV-030",
            "description": "Sudden power drop detected. Grid frequency disturbance likely cause.",
            "severity": "critical",
            "status": "resolved",
            "acknowledged_by": users["admin"].id,
            "acknowledged_at": NOW - timedelta(days=20),
            "resolved_at": NOW - timedelta(days=18),
        },
    ]

    alerts = []
    for ad in alerts_data:
        asset = ad.pop("asset")
        alert = HealthAlert(
            organization_id=org.id,
            asset_id=asset.id,
            **ad,
        )
        session.add(alert)
        await session.flush()
        alerts.append(alert)

    print(f"\u2705 Health alerts created: {len(alerts)}")
    return alerts


async def insert_maintenance_work_orders(
    session: AsyncSession, org: Organization, assets: dict, alerts: list, users: dict,
) -> None:
    inverters = assets["inverters"]
    work_orders = [
        MaintenanceWorkOrder(
            organization_id=org.id,
            asset_id=inverters[2].id,
            alert_id=alerts[0].id,
            assigned_to=users["operator"].id,
            title="INV-003 Panel Cleaning & Inspection",
            description="Schedule robotic cleaning and inspect for soiling. Estimated 4 hours.",
            priority="medium",
            status="scheduled",
            scheduled_start=NOW + timedelta(days=2),
            scheduled_end=NOW + timedelta(days=2, hours=4),
            estimated_cost=15000.00,
        ),
        MaintenanceWorkOrder(
            organization_id=org.id,
            asset_id=inverters[14].id,
            alert_id=alerts[1].id,
            assigned_to=users["operator"].id,
            title="INV-015 Cooling System Check",
            description="Inspect cooling fans, clean heat sinks, verify coolant levels.",
            priority="medium",
            status="scheduled",
            scheduled_start=NOW + timedelta(days=5),
            scheduled_end=NOW + timedelta(days=5, hours=3),
            estimated_cost=8000.00,
        ),
        MaintenanceWorkOrder(
            organization_id=org.id,
            asset_id=inverters[21].id,
            alert_id=alerts[2].id,
            assigned_to=users["operator"].id,
            title="INV-022 String Inspection",
            description="Investigate panel string mismatch. Check bypass diodes and connections.",
            priority="low",
            status="scheduled",
            scheduled_start=NOW + timedelta(days=10),
            scheduled_end=NOW + timedelta(days=10, hours=5),
            estimated_cost=12000.00,
        ),
        MaintenanceWorkOrder(
            organization_id=org.id,
            asset_id=inverters[6].id,
            alert_id=alerts[3].id,
            assigned_to=users["admin"].id,
            title="URGENT: INV-007 Thermal Inspection",
            description="CRITICAL: Investigate temperature spike. Possible thermal runaway. Shut down inverter before inspection.",
            priority="critical",
            status="scheduled",
            scheduled_start=NOW + timedelta(hours=2),
            scheduled_end=NOW + timedelta(hours=6),
            estimated_cost=45000.00,
        ),
        MaintenanceWorkOrder(
            organization_id=org.id,
            asset_id=inverters[29].id,
            alert_id=alerts[4].id,
            assigned_to=users["operator"].id,
            title="INV-030 Post-Event Inspection",
            description="Post-grid-disturbance inspection. Verify all protection systems functioned correctly.",
            priority="high",
            status="completed",
            scheduled_start=NOW - timedelta(days=18),
            scheduled_end=NOW - timedelta(days=17),
            actual_start=NOW - timedelta(days=18),
            actual_end=NOW - timedelta(days=17, hours=-3),
            estimated_cost=10000.00,
            actual_cost=8500.00,
            parts_used=[
                {"name": "Fuse Link 32A", "qty": 3, "cost": 120},
                {"name": "Thermal Paste", "qty": 1, "cost": 450},
            ],
            resolution_notes="Grid disturbance logged. Inverter protection relays operated correctly. No physical damage found.",
        ),
    ]

    session.add_all(work_orders)
    await session.flush()
    print(f"\u2705 Maintenance work orders created: {len(work_orders)}")


async def insert_dispatch_decisions(
    session: AsyncSession, org: Organization, assets: dict,
    dispatch_rules: list, curtailment_events: list,
) -> None:
    battery = assets["battery"]
    inverters = assets["inverters"]
    start_ts = (NOW - timedelta(days=DAYS_OF_DATA)).replace(hour=0, minute=0, second=0, microsecond=0)

    charge_rule = dispatch_rules[0]
    discharge_rule = dispatch_rules[1]
    shield_rule = dispatch_rules[2]

    decisions = []
    charge_times = []
    discharge_times = []

    for day_offset in range(DAYS_OF_DATA):
        day_start = start_ts + timedelta(days=day_offset)
        for hour in range(0, 24):
            ts = day_start.replace(hour=hour)
            hour = ts.hour
            if 1 <= hour <= 4 and RNG.random() < 0.28:
                charge_times.append(ts)
            if 18 <= hour <= 22 and RNG.random() < 0.32:
                discharge_times.append(ts)

    for ts in charge_times[:25]:
        price = round(RNG.uniform(1.5, 2.4), 4)
        decisions.append(DispatchDecision(
            organization_id=org.id,
            rule_id=charge_rule.id,
            asset_id=battery.id,
            status="executed",
            action_taken="charge_battery",
            action_params={"target_soc_pct": 90, "charge_rate_kw": 5000},
            triggered_value=price,
            expected_outcome=round(RNG.uniform(200, 500), 4),
            actual_outcome=round(RNG.uniform(180, 480), 4),
            executed_at=ts,
            duration_seconds=RNG.randint(1800, 3600),
        ))

    for ts in discharge_times[:25]:
        price = round(RNG.uniform(7.1, 8.5), 4)
        soc = round(RNG.uniform(40, 85), 2)
        decisions.append(DispatchDecision(
            organization_id=org.id,
            rule_id=discharge_rule.id,
            asset_id=battery.id,
            status="executed",
            action_taken="discharge_battery",
            action_params={
                "discharge_rate_kw": 8000,
                "soc_at_trigger": soc,
            },
            triggered_value=price,
            expected_outcome=round(RNG.uniform(500, 1200), 4),
            actual_outcome=round(RNG.uniform(450, 1150), 4),
            executed_at=ts,
            duration_seconds=RNG.randint(1200, 3600),
        ))

    for ce in curtailment_events[:12]:
        target_inv = RNG.choice(inverters)
        decisions.append(DispatchDecision(
            organization_id=org.id,
            rule_id=shield_rule.id,
            asset_id=target_inv.id,
            curtailment_event_id=ce.event_id,
            status="executed",
            action_taken="route_to_compute",
            action_params={
                "routed_kw": 5000,
                "target_load": "compute_cluster",
            },
            triggered_value=round(float(ce.curtailed_kwh), 4),
            expected_outcome=round(float(ce.revenue_lost) * 0.3, 4),
            actual_outcome=round(float(ce.revenue_lost) * 0.25, 4),
            executed_at=ce.ts + timedelta(minutes=15),
            duration_seconds=ce.duration_minutes * 60,
        ))

    session.add_all(decisions)
    await session.flush()
    print(f"\u2705 Dispatch decisions created: {len(decisions)}")


async def insert_settings(session: AsyncSession, org: Organization) -> None:
    settings_data = [
        ("branding.logo_url", "https://example.com/logo.png", "string", "Company logo URL for dashboard branding"),
        ("branding.primary_color", "#10b981", "string", "Primary brand color (hex)"),
        ("branding.farm_name", "GreenEnergy Corp - Rajasthan", "string", "Display name for dashboard header"),
        ("alerts.curtailment_threshold_pct", "20", "number", "Percentage drop threshold for curtailment detection"),
        ("alerts.health_drop_threshold", "20", "number", "Health score drop threshold for alerting"),
        ("alerts.consecutive_readings", "3", "number", "Consecutive readings before alert triggers"),
        ("dispatch.price_threshold", "0.08", "number", "Default price threshold for dispatch (USD)"),
        ("dispatch.default_cooldown_min", "15", "number", "Default cooldown between dispatch actions"),
        ("carbon.default_methodology", "IPMVP_v2.1", "string", "Default carbon credit methodology"),
        ("notifications.email_enabled", "true", "boolean", "Enable email notifications"),
        ("notifications.alert_recipients", "admin@example.com,operator@example.com", "string", "Comma-separated alert recipients"),
    ]

    for key, value, value_type, description in settings_data:
        setting = Setting(
            organization_id=org.id,
            key=key,
            value=value,
            value_type=value_type,
            description=description,
        )
        session.add(setting)

    await session.flush()
    print(f"\u2705 Settings created: {len(settings_data)}")


def _generate_curtailment_windows(
    inverters: list,
    num_events: int = 15,
) -> list[dict]:
    windows = []
    start_ts = (NOW - timedelta(days=DAYS_OF_DATA)).replace(minute=0, second=0, microsecond=0)

    used_days = set()
    attempts = 0
    while len(windows) < num_events and attempts < 200:
        attempts += 1
        day_offset = RNG.randint(3, DAYS_OF_DATA - 3)
        if day_offset in used_days:
            continue

        event_day = start_ts + timedelta(days=day_offset)
        start_hour = RNG.randint(9, 14)
        duration_hours = RNG.choice([2, 3, 4, 5, 6])
        end_hour = min(start_hour + duration_hours, 17)
        if end_hour - start_hour < 2:
            continue

        num_affected = RNG.randint(1, 5)
        affected_ids = [RNG.choice(inverters).id for _ in range(num_affected)]

        event_start = event_day.replace(hour=start_hour)
        event_end = event_day.replace(hour=end_hour)

        used_days.add(day_offset)
        windows.append({
            "start_ts": event_start,
            "end_ts": event_end,
            "duration_hours": end_hour - start_hour,
            "inverter_ids": list(set(affected_ids)),
            "resolved": RNG.random() < 0.85,
            "resolved_at": event_end + timedelta(hours=RNG.randint(2, 24))
                if RNG.random() < 0.85 else None,
        })

    return windows


NUM_INVERTERS = 50
PANELS_PER_INVERTER = 100
DAYS_OF_DATA = 90


async def main() -> None:
    print("=" * 60)
    print("  URJA Seed Data Generator")
    print("  Populating 50MW solar farm...")
    print("=" * 60)
    print()

    async with async_session_factory() as session:
        await delete_all_data(session)

        org = await create_organization(session)
        users = await create_users(session, org)
        await create_api_keys(session, org, users)
        site = await create_site(session, org)
        assets = await create_assets(session, org, site)
        await create_relationships(session, org, site, assets)

        print()

        inverters = assets["inverters"]
        curtailment_windows = _generate_curtailment_windows(inverters, 15)
        print(f"\u26a1 Curtailment windows generated: {len(curtailment_windows)} (seed days)")

        await insert_telemetry(session, org, site, assets, curtailment_windows)
        await insert_weather(session, org, site)
        await insert_grid_prices(session, org, site)

        print()

        curtailment_events = await insert_curtailment_events(
            session, org, assets, curtailment_windows,
        )
        dispatch_rules = await insert_dispatch_rules(session, org)
        await insert_carbon_credits(session, org, assets, users)
        await insert_health_metrics(session, org, assets)
        alerts = await insert_health_alerts(session, org, assets, users)
        await insert_maintenance_work_orders(session, org, assets, alerts, users)
        await insert_dispatch_decisions(
            session, org, assets, dispatch_rules, curtailment_events,
        )
        await insert_settings(session, org)

        await session.commit()
        print()
        print("=" * 60)
        print("  Seed data complete!")
        print("  Login: admin@example.com / admin123")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
