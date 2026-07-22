import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.auth import User
from app.models.telemetry import TelemetryGeneration
from app.models.asset import Asset
from app.schemas.telemetry import (
    TelemetryCreate,
    TelemetryBatchCreate,
    TelemetryResponse,
    TelemetryLatestResponse,
    TelemetryIngestResponse,
    AggregatedTelemetryResponse,
)
from app.schemas.dispatch import PaginationMeta

router = APIRouter()


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def ingest_telemetry(
    payload: TelemetryCreate | TelemetryBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = current_user.organization_id
    batch_id = f"batch_{uuid.uuid4().hex[:8]}"
    records_accepted = 0
    records_rejected = 0
    errors = []

    records = payload.records if isinstance(payload, TelemetryBatchCreate) else [payload]
    if len(records) > 1000:
        raise HTTPException(status_code=status.HTTP_413_ENTITY_TOO_LARGE, detail="Batch too large, max 1000 records")

    for r in records:
        try:
            row = TelemetryGeneration(
                ts=r.ts,
                asset_id=r.asset_id,
                organization_id=org_id,
                generation_kw=r.generation_kw,
                energy_kwh=r.energy_kwh,
                power_factor=r.power_factor,
                voltage_v=r.voltage_v,
                current_a=r.current_a,
                frequency_hz=r.frequency_hz,
                temperature_c=r.temperature_c,
                quality_code=r.quality_code,
            )
            db.add(row)
            records_accepted += 1
        except Exception as e:
            records_rejected += 1
            errors.append({"record": str(r.asset_id), "error": str(e)})

    if records_accepted > 0:
        await db.flush()

    return TelemetryIngestResponse(
        batch_id=batch_id,
        records_accepted=records_accepted,
        records_rejected=records_rejected,
        errors=errors,
        status="completed",
    )


@router.get("")
async def query_telemetry(
    asset_id: str = Query(..., description="Asset UUID"),
    start_date: datetime = Query(..., description="Start of time range"),
    end_date: Optional[datetime] = Query(None, description="End of time range"),
    aggregation: str = Query("raw", description="raw, hourly, daily"),
    granularity: Optional[str] = Query(None, description="15m, 1h, 1d"),
    metrics: str = Query("generation_kw", description="Comma-separated metrics"),
    per_page: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = current_user.organization_id
    if end_date is None:
        end_date = datetime.now(timezone.utc)

    if start_date >= end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must be before end_date")

    agg = granularity or aggregation

    if agg == "raw":
        stmt = text("""
            SELECT ts, asset_id, generation_kw, energy_kwh, power_factor,
                   voltage_v, current_a, frequency_hz, temperature_c, quality_code
            FROM telemetry_generation
            WHERE asset_id = :asset_id
              AND organization_id = :org_id
              AND ts >= :start_date
              AND ts < :end_date
            ORDER BY ts DESC
            LIMIT :limit
        """)
        cursor = await db.execute(stmt, {
            "asset_id": asset_id,
            "org_id": org_id,
            "start_date": start_date,
            "end_date": end_date,
            "limit": per_page,
        })
        rows = cursor.fetchall()
        data = [TelemetryResponse(
            ts=r[0], asset_id=r[1], generation_kw=r[2],
            energy_kwh=r[3], power_factor=r[4], voltage_v=r[5],
            current_a=r[6], frequency_hz=r[7], temperature_c=r[8],
            quality_code=r[9],
        ) for r in rows]
    elif agg in ("hourly", "1h"):
        stmt = text("""
            SELECT
                time_bucket('1 hour', ts) AS bucket,
                asset_id,
                AVG(generation_kw) AS avg_kw,
                MAX(generation_kw) AS peak_kw,
                MIN(generation_kw) AS min_kw,
                SUM(energy_kwh) AS energy_kwh,
                COUNT(*) AS reading_count
            FROM telemetry_generation
            WHERE asset_id = :asset_id
              AND organization_id = :org_id
              AND ts >= :start_date
              AND ts < :end_date
            GROUP BY bucket, asset_id
            ORDER BY bucket DESC
            LIMIT :limit
        """)
        cursor = await db.execute(stmt, {
            "asset_id": asset_id,
            "org_id": org_id,
            "start_date": start_date,
            "end_date": end_date,
            "limit": per_page,
        })
        rows = cursor.fetchall()
        data = [AggregatedTelemetryResponse(
            bucket=r[0], asset_id=r[1], avg_kw=r[2],
            peak_kw=r[3], min_kw=r[4], energy_kwh=r[5],
            reading_count=r[6],
        ) for r in rows]
    elif agg in ("daily", "1d"):
        stmt = text("""
            SELECT
                time_bucket('1 day', ts) AS bucket,
                asset_id,
                AVG(generation_kw) AS avg_kw,
                MAX(generation_kw) AS peak_kw,
                MIN(generation_kw) AS min_kw,
                SUM(energy_kwh) AS energy_kwh,
                COUNT(*) AS reading_count
            FROM telemetry_generation
            WHERE asset_id = :asset_id
              AND organization_id = :org_id
              AND ts >= :start_date
              AND ts < :end_date
            GROUP BY bucket, asset_id
            ORDER BY bucket DESC
            LIMIT :limit
        """)
        cursor = await db.execute(stmt, {
            "asset_id": asset_id,
            "org_id": org_id,
            "start_date": start_date,
            "end_date": end_date,
            "limit": per_page,
        })
        rows = cursor.fetchall()
        data = [AggregatedTelemetryResponse(
            bucket=r[0], asset_id=r[1], avg_kw=r[2],
            peak_kw=r[3], min_kw=r[4], energy_kwh=r[5],
            reading_count=r[6],
        ) for r in rows]
    else:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid aggregation: {agg}")

    return {"data": data, "pagination": PaginationMeta(total=len(data), has_more=False)}


@router.get("/latest")
async def get_latest_telemetry(
    asset_id: Optional[str] = Query(None, description="Specific asset UUID"),
    site_id: Optional[str] = Query(None, description="Filter by site"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = current_user.organization_id

    if asset_id:
        stmt = text("""
            SELECT DISTINCT ON (t.asset_id)
                t.asset_id, a.name AS asset_name, a.asset_type,
                s.name AS site_name, t.ts, t.generation_kw,
                t.energy_kwh, t.temperature_c, a.health_score, a.status
            FROM telemetry_generation t
            JOIN assets a ON a.id = t.asset_id
            JOIN asset_sites s ON s.id = a.site_id
            WHERE t.asset_id = :asset_id
              AND t.organization_id = :org_id
            ORDER BY t.asset_id, t.ts DESC
        """)
        cursor = await db.execute(stmt, {"asset_id": asset_id, "org_id": org_id})
    elif site_id:
        stmt = text("""
            SELECT DISTINCT ON (t.asset_id)
                t.asset_id, a.name AS asset_name, a.asset_type,
                s.name AS site_name, t.ts, t.generation_kw,
                t.energy_kwh, t.temperature_c, a.health_score, a.status
            FROM telemetry_generation t
            JOIN assets a ON a.id = t.asset_id
            JOIN asset_sites s ON s.id = a.site_id
            WHERE s.id = :site_id
              AND t.organization_id = :org_id
            ORDER BY t.asset_id, t.ts DESC
        """)
        cursor = await db.execute(stmt, {"site_id": site_id, "org_id": org_id})
    else:
        stmt = text("""
            SELECT DISTINCT ON (t.asset_id)
                t.asset_id, a.name AS asset_name, a.asset_type,
                s.name AS site_name, t.ts, t.generation_kw,
                t.energy_kwh, t.temperature_c, a.health_score, a.status
            FROM telemetry_generation t
            JOIN assets a ON a.id = t.asset_id AND a.organization_id = :org_id
            JOIN asset_sites s ON s.id = a.site_id
            WHERE t.organization_id = :org_id
            ORDER BY t.asset_id, t.ts DESC
        """)
        cursor = await db.execute(stmt, {"org_id": org_id})

    rows = cursor.fetchall()
    data = [
        TelemetryLatestResponse(
            asset_id=r[0], asset_name=r[1], asset_type=r[2],
            site_name=r[3], ts=r[4], generation_kw=r[5],
            energy_kwh=r[6], temperature_c=r[7],
            health_score=r[8], status=r[9],
        ) for r in rows
    ]
    return {"data": data}
