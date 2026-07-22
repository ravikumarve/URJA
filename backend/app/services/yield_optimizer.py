import math
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID


def calculate_curtailment_revenue_loss(
    generation_data: list[dict],
    grid_prices: list[dict],
) -> dict:
    total_expected = Decimal("0")
    total_actual = Decimal("0")
    total_revenue_lost = Decimal("0")
    event_count = 0

    price_map: dict[str, Decimal] = {}
    for gp in grid_prices:
        ts_key = gp.get("ts", "").isoformat() if hasattr(gp.get("ts"), "isoformat") else str(gp.get("ts", ""))
        price_map[ts_key] = Decimal(str(gp.get("price_per_kwh", 0)))

    for gen in generation_data:
        expected = Decimal(str(gen.get("expected_kwh", gen.get("generation_kw", 0) * 0.25)))
        actual = Decimal(str(gen.get("actual_kwh", gen.get("energy_kwh", 0))))
        curtailed = expected - actual
        if curtailed <= 0:
            continue

        ts_key = gen.get("ts", "").isoformat() if hasattr(gen.get("ts"), "isoformat") else str(gen.get("ts", ""))
        price = price_map.get(ts_key, Decimal("0"))
        revenue = curtailed * price

        total_expected += expected
        total_actual += actual
        total_revenue_lost += revenue
        event_count += 1

    return {
        "total_expected_kwh": float(total_expected),
        "total_actual_kwh": float(total_actual),
        "total_curtailed_kwh": float(total_expected - total_actual),
        "total_revenue_lost": float(total_revenue_lost),
        "event_count": event_count,
    }


def evaluate_dispatch_rules(
    asset: dict,
    telemetry: dict,
    grid_price: Optional[Decimal] = None,
    battery_soc: Optional[float] = None,
) -> list[dict]:
    results = []
    generation_kw = float(telemetry.get("generation_kw", 0))
    capacity_kw = float(asset.get("capacity_kw", 1))
    if capacity_kw <= 0:
        capacity_kw = 1
    generation_pct = (generation_kw / capacity_kw) * 100

    rules = asset.get("dispatch_rules", [])
    for rule in sorted(rules, key=lambda r: r.get("priority", 100)):
        if not rule.get("is_active", True):
            continue

        condition_type = rule.get("condition_type", "")
        condition_config = rule.get("condition_config", {})
        triggered = False
        triggered_value = None

        if condition_type == "price_above":
            threshold = float(condition_config.get("threshold", 0))
            if grid_price is not None and float(grid_price) > threshold:
                triggered = True
                triggered_value = float(grid_price)

        elif condition_type == "price_below":
            threshold = float(condition_config.get("threshold", 0))
            if grid_price is not None and float(grid_price) < threshold:
                triggered = True
                triggered_value = float(grid_price)

        elif condition_type == "generation_above":
            threshold_pct = float(condition_config.get("threshold_pct", 80))
            if generation_pct > threshold_pct:
                triggered = True
                triggered_value = generation_pct

        elif condition_type == "generation_below":
            threshold_pct = float(condition_config.get("threshold_pct", 20))
            if generation_pct < threshold_pct:
                triggered = True
                triggered_value = generation_pct

        elif condition_type == "soc_above":
            threshold = float(condition_config.get("threshold_pct", 80))
            if battery_soc is not None and battery_soc > threshold:
                triggered = True
                triggered_value = battery_soc

        elif condition_type == "soc_below":
            threshold = float(condition_config.get("threshold_pct", 20))
            if battery_soc is not None and battery_soc < threshold:
                triggered = True
                triggered_value = battery_soc

        elif condition_type == "curtailment_detected":
            if telemetry.get("quality_code", 0) == 3:
                triggered = True
                triggered_value = telemetry.get("quality_code", 0)

        if triggered:
            results.append({
                "rule_id": rule.get("id"),
                "rule_name": rule.get("name"),
                "action": rule.get("action"),
                "action_config": rule.get("action_config", {}),
                "triggered_value": triggered_value,
                "priority": rule.get("priority", 100),
            })

    return results


def estimate_battery_soc(asset: dict) -> float:
    telemetry = asset.get("latest_telemetry", {})
    if not telemetry:
        return 50.0

    generation_kw = float(telemetry.get("generation_kw", 0))
    capacity_kw = float(asset.get("capacity_kw", 1))
    if capacity_kw <= 0:
        capacity_kw = 1

    ratio = generation_kw / capacity_kw
    soc = 50.0 + (ratio * 30.0)
    return max(0.0, min(100.0, soc))
