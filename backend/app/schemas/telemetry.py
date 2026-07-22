from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, model_validator


class TelemetryCreate(BaseModel):
    asset_id: UUID
    ts: datetime
    generation_kw: float
    energy_kwh: Optional[float] = None
    power_factor: Optional[float] = Field(None, ge=0, le=1)
    voltage_v: Optional[float] = None
    current_a: Optional[float] = None
    frequency_hz: Optional[float] = None
    temperature_c: Optional[float] = None
    quality_code: int = Field(default=0, ge=0, le=3)


class TelemetryBatchCreate(BaseModel):
    records: list[TelemetryCreate] = Field(max_length=1000)

    @model_validator(mode="after")
    def check_batch_size(self):
        if len(self.records) > 1000:
            raise ValueError("Batch size exceeds maximum of 1000 records")
        return self


class TelemetryResponse(BaseModel):
    ts: datetime
    asset_id: UUID
    generation_kw: float
    energy_kwh: Optional[float] = None
    power_factor: Optional[float] = None
    voltage_v: Optional[float] = None
    current_a: Optional[float] = None
    frequency_hz: Optional[float] = None
    temperature_c: Optional[float] = None
    quality_code: int = 0


class TelemetryLatestResponse(BaseModel):
    asset_id: UUID
    asset_name: str
    asset_type: str
    site_name: str
    ts: datetime
    generation_kw: Optional[float] = None
    energy_kwh: Optional[float] = None
    temperature_c: Optional[float] = None
    health_score: Optional[float] = None
    status: str


class AggregatedTelemetryResponse(BaseModel):
    bucket: datetime
    asset_id: UUID
    avg_kw: Optional[float] = None
    peak_kw: Optional[float] = None
    min_kw: Optional[float] = None
    energy_kwh: Optional[float] = None
    reading_count: int = 0


class TelemetryIngestResponse(BaseModel):
    batch_id: str
    records_accepted: int
    records_rejected: int
    errors: list = []
    status: str = "completed"
