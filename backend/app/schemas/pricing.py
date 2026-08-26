from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class PricePointResponse(BaseModel):
    """Raw grid price reading (one row per ts/site/source)."""

    ts: datetime
    site_id: UUID
    price_per_kwh: float
    currency: str
    source: str
    is_forecast: bool
    market_region: Optional[str] = None


class AggregatedPriceResponse(BaseModel):
    """Time-bucketed grid price (hourly/daily aggregation)."""

    bucket: datetime
    site_id: UUID
    avg_price: float
    min_price: float
    max_price: float
    currency: str
    reading_count: int
