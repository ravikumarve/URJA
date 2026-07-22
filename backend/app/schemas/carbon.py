from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class AuditTrailEntry(BaseModel):
    action: str
    actor: str
    timestamp: datetime
    details: Optional[str] = None


class CarbonCreditResponse(BaseModel):
    credit_id: UUID
    batch_id: UUID
    asset_id: UUID
    asset_name: Optional[str] = None
    status: str
    quantity: float
    unit: str = "tCO2e"
    methodology: str = "IPMVP_v2.1"
    generation_start: datetime
    generation_end: datetime
    total_kwh: float
    emission_factor: float
    registry_tx_id: Optional[str] = None
    registry_url: Optional[str] = None
    issued_by: Optional[UUID] = None
    retired_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime


class CarbonCreditDetailResponse(CarbonCreditResponse):
    organization_id: UUID
    audit_trail: list[AuditTrailEntry] = []


class CarbonIssueRequest(BaseModel):
    asset_id: UUID
    generation_start: datetime
    generation_end: datetime
    methodology: str = "IPMVP_v2.1"
    notes: Optional[str] = None


class CarbonIssueResponse(BaseModel):
    batch_id: UUID
    total_kwh: float
    emission_factor: float
    total_co2e: float
    credit_count: int
    credit_ids: list[UUID]
    methodology: str
    registry_tx_id: Optional[str] = None
    status: str = "active"
    created_at: datetime


class PortfolioSummaryResponse(BaseModel):
    total_issued: int = 0
    total_retired: int = 0
    total_cancelled: int = 0
    total_available: int = 0
    total_co2e_issued: float = 0.0
    total_co2e_retired: float = 0.0
    currency: str = "USD"
    estimated_value: float = 0.0
    price_per_credit: float = 50.0
    by_status: dict[str, int] = {}
    by_methodology: dict[str, int] = {}
    last_issuance: Optional[datetime] = None
    next_eligible_date: Optional[datetime] = None
