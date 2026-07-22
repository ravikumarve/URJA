from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class PaginationMeta(BaseModel):
    next_cursor: Optional[str] = None
    has_more: bool = False
    total: int = 0


class DispatchRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    priority: int = Field(default=100, ge=0)
    condition_type: str
    condition_config: dict[str, Any] = {}
    action: str
    action_config: dict[str, Any] = {}
    target_asset_type: Optional[str] = None
    cooldown_minutes: int = Field(default=15, ge=0)


class DispatchRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0)
    condition_type: Optional[str] = None
    condition_config: Optional[dict[str, Any]] = None
    action: Optional[str] = None
    action_config: Optional[dict[str, Any]] = None
    target_asset_type: Optional[str] = None
    cooldown_minutes: Optional[int] = Field(None, ge=0)


class DispatchRuleResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    is_active: bool = True
    priority: int = 100
    condition_type: str
    condition_config: dict[str, Any] = {}
    action: str
    action_config: dict[str, Any] = {}
    target_asset_type: Optional[str] = None
    cooldown_minutes: int = 15
    last_triggered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class DispatchDecisionResponse(BaseModel):
    id: UUID
    rule_name: Optional[str] = None
    asset_name: Optional[str] = None
    status: str
    action_taken: str
    action_params: dict[str, Any] = {}
    triggered_value: Optional[float] = None
    expected_outcome: Optional[float] = None
    actual_outcome: Optional[float] = None
    duration_seconds: Optional[int] = None
    executed_at: Optional[datetime] = None
    created_at: datetime


class CurtailmentEventResponse(BaseModel):
    event_id: UUID
    asset_id: UUID
    asset_name: Optional[str] = None
    site_name: Optional[str] = None
    ts: datetime
    duration_minutes: int
    expected_kwh: float
    actual_kwh: float
    curtailed_kwh: float
    price_per_kwh: float
    revenue_lost: float
    grid_price_source: Optional[str] = None
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None


class RevenueLostResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    total_curtailed_kwh: float
    total_revenue_lost: float
    currency: str = "USD"
    event_count: int = 0
    avg_price_per_kwh: Optional[float] = None
    by_site: list[dict] = []


class Envelope(BaseModel):
    data: Any
    pagination: Optional[PaginationMeta] = None
