from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class HealthScoreResponse(BaseModel):
    asset_id: UUID
    asset_name: Optional[str] = None
    asset_type: Optional[str] = None
    site_name: Optional[str] = None
    health_score: float
    anomaly_score: Optional[float] = None
    trend: str = "stable"
    metric_scores: dict[str, float] = {}
    anomaly_flags: list[str] = []
    last_checked_at: Optional[datetime] = None


class HealthAlertResponse(BaseModel):
    id: UUID
    asset_id: UUID
    asset_name: Optional[str] = None
    site_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    severity: str
    status: str
    acknowledged_by: Optional[UUID] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime


class HealthAlertAcknowledgeResponse(BaseModel):
    id: UUID
    status: str
    acknowledged_at: datetime
    acknowledged_by: UUID


class AnomalyResponse(BaseModel):
    id: UUID
    asset_id: UUID
    asset_name: Optional[str] = None
    ts: datetime
    metric: str
    observed_value: float
    expected_value: Optional[float] = None
    z_score: Optional[float] = None
    anomaly_score: Optional[float] = None
    method: str = "z_score"
    window_size: Optional[int] = None
    triggered_alert_id: Optional[UUID] = None
    created_at: datetime


class WorkOrderCreate(BaseModel):
    asset_id: UUID
    alert_id: Optional[UUID] = None
    assigned_to: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    scheduled_start: datetime
    scheduled_end: datetime
    estimated_cost: Optional[float] = None


class WorkOrderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[UUID] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    parts_used: Optional[list[dict[str, Any]]] = None
    resolution_notes: Optional[str] = None


class WorkOrderResponse(BaseModel):
    id: UUID
    asset_id: UUID
    asset_name: Optional[str] = None
    site_name: Optional[str] = None
    alert_id: Optional[UUID] = None
    assigned_to: Optional[UUID] = None
    assigned_to_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    priority: str
    status: str
    scheduled_start: datetime
    scheduled_end: datetime
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    parts_used: list = []
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
