from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.auth import User
from app.schemas.dispatch import PaginationMeta
from app.schemas.pricing import AggregatedPriceResponse, PricePointResponse

router = APIRouter()

_AGG_BUCKETS = {"hourly": "1 hour", "daily": "1 day"}


@router.get("")
async def query_grid_prices(
    site_id: UUID = Query(..., description="Site UUID"),
    start_date: datetime = Query(..., description="Start of time range"),
    end_date: Optional[datetime] = Query(None, description="End of time range"),
    aggregation: str = Query("hourly", description="raw, hourly, daily"),
    per_page: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Grid price time-series for a site, sourced from the grid_prices hypertable."""
    org_id = current_user.organization_id
    if end_date is None:
        end_date = datetime.now(timezone.utc)
    if start_date >= end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before end_date",
        )

    params = {
        "site_id": str(site_id),
        "org_id": org_id,
        "start_date": start_date,
        "end_date": end_date,
        "limit": per_page,
    }

    if aggregation == "raw":
        stmt = text("""
            SELECT ts, site_id, price_per_kwh, currency, source, is_forecast, market_region
            FROM grid_prices
            WHERE site_id = :site_id
              AND organization_id = :org_id
              AND ts >= :start_date
              AND ts < :end_date
            ORDER BY ts DESC
            LIMIT :limit
        """)
        cursor = await db.execute(stmt, params)
        rows = cursor.fetchall()
        data = [
            PricePointResponse(
                ts=r[0], site_id=r[1], price_per_kwh=float(r[2]),
                currency=r[3], source=r[4], is_forecast=r[5],
                market_region=r[6],
            )
            for r in rows
        ]
    elif aggregation in _AGG_BUCKETS:
        bucket = _AGG_BUCKETS[aggregation]
        stmt = text(f"""
            SELECT
                time_bucket('{bucket}', ts) AS bucket,
                site_id,
                AVG(price_per_kwh) AS avg_price,
                MIN(price_per_kwh) AS min_price,
                MAX(price_per_kwh) AS max_price,
                (ARRAY_AGG(currency ORDER BY ts DESC))[1] AS currency,
                COUNT(*) AS reading_count
            FROM grid_prices
            WHERE site_id = :site_id
              AND organization_id = :org_id
              AND ts >= :start_date
              AND ts < :end_date
            GROUP BY bucket, site_id
            ORDER BY bucket DESC
            LIMIT :limit
        """)
        cursor = await db.execute(stmt, params)
        rows = cursor.fetchall()
        data = [
            AggregatedPriceResponse(
                bucket=r[0], site_id=r[1], avg_price=float(r[2]),
                min_price=float(r[3]), max_price=float(r[4]),
                currency=r[5] or "USD", reading_count=r[6],
            )
            for r in rows
        ]
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid aggregation: {aggregation}",
        )

    return {"data": data, "pagination": PaginationMeta(total=len(data), has_more=False)}


@router.get("/latest")
async def latest_grid_price(
    site_id: UUID = Query(..., description="Site UUID"),
    max_age_minutes: int = Query(120, ge=1, le=1440),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Most recent grid price for a site; 404 if stale beyond max_age_minutes."""
    org_id = current_user.organization_id
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)

    stmt = text("""
        SELECT ts, site_id, price_per_kwh, currency, source, is_forecast, market_region
        FROM grid_prices
        WHERE site_id = :site_id
          AND organization_id = :org_id
          AND ts >= :cutoff
        ORDER BY ts DESC
        LIMIT 1
    """)
    cursor = await db.execute(
        stmt, {"site_id": str(site_id), "org_id": org_id, "cutoff": cutoff}
    )
    r = cursor.fetchone()
    if r is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recent grid price available",
        )
    return PricePointResponse(
        ts=r[0], site_id=r[1], price_per_kwh=float(r[2]),
        currency=r[3], source=r[4], is_forecast=r[5], market_region=r[6],
    )
