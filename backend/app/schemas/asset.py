from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, Any
from app.models.enums import AssetType, AssetStatus


class AssetCreate(BaseModel):
    site_id: str
    parent_asset_id: Optional[str] = None
    asset_type: AssetType
    name: str
    code: str
    serial_number: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    capacity_kw: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    commissioning_date: Optional[date] = None
    config: Optional[dict] = None
    metadata: Optional[dict] = None


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    serial_number: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    capacity_kw: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    commissioning_date: Optional[date] = None
    status: Optional[AssetStatus] = None
    config: Optional[dict] = None
    metadata: Optional[dict] = None
    parent_asset_id: Optional[str] = None


class AssetBrief(BaseModel):
    id: str
    name: str
    asset_type: str
    capacity_kw: Optional[float] = None
    status: str

    class Config:
        from_attributes = True


class AssetResponse(BaseModel):
    id: str
    site_id: str
    parent_asset_id: Optional[str] = None
    asset_type: str
    name: str
    code: str
    serial_number: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    capacity_kw: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    commissioning_date: Optional[date] = None
    status: str
    health_score: Optional[float] = None
    config: Optional[Any] = None
    metadata: Optional[Any] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssetDetailResponse(BaseModel):
    id: str
    site: Optional[dict] = None
    parent_asset: Optional[dict] = None
    children: list[AssetBrief] = []
    asset_type: str
    name: str
    code: str
    serial_number: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    capacity_kw: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    commissioning_date: Optional[date] = None
    status: str
    health_score: Optional[float] = None
    config: Optional[Any] = None
    metadata: Optional[Any] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssetSiteCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    capacity_mw: float
    timezone: str = "UTC"
    metadata: Optional[dict] = None


class AssetSiteResponse(BaseModel):
    id: str
    name: str
    code: str
    description: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    capacity_mw: float
    timezone: str
    status: str
    asset_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssetSiteDetailResponse(BaseModel):
    id: str
    name: str
    code: str
    description: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    capacity_mw: float
    timezone: str
    status: str
    asset_summary: Optional[dict] = None
    recent_generation_kwh: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int

    class Config:
        arbitrary_types_allowed = True
