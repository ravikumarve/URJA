from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.auth import User
from app.models.asset import Asset, AssetSite
from app.models.telemetry import TelemetryGeneration
from app.schemas.asset import (
    AssetCreate, AssetUpdate, AssetResponse, AssetDetailResponse,
    AssetBrief, AssetSiteCreate, AssetSiteResponse,
    AssetSiteDetailResponse,
)
from app.services.asset import (
    get_assets, get_asset, create_asset, update_asset, delete_asset,
    get_sites, get_site, create_site,
    check_asset_code_exists, check_site_code_exists, check_site_exists,
    get_site_asset_summary,
)

router = APIRouter()


@router.get("")
async def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    site_id: str | None = None,
    asset_type: str | None = None,
    status: str | None = None,
    q: str | None = None,
    min_capacity: float | None = None,
    max_capacity: float | None = None,
    health_min: float | None = None,
    sort_by: str = "name",
    sort_order: str = "asc",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await get_assets(
        db, str(current_user.organization_id), page, page_size,
        site_id=site_id, asset_type=asset_type, status=status,
        q=q, min_capacity=min_capacity, max_capacity=max_capacity,
        health_min=health_min, sort_by=sort_by, sort_order=sort_order,
    )
    return {
        "items": [
            AssetResponse(
                id=str(a.id),
                site_id=str(a.site_id),
                parent_asset_id=str(a.parent_asset_id) if a.parent_asset_id else None,
                asset_type=a.asset_type,
                name=a.name,
                code=a.code,
                serial_number=a.serial_number,
                manufacturer=a.manufacturer,
                model=a.model,
                capacity_kw=float(a.capacity_kw) if a.capacity_kw else None,
                latitude=float(a.latitude) if a.latitude else None,
                longitude=float(a.longitude) if a.longitude else None,
                commissioning_date=a.commissioning_date,
                status=a.status,
                health_score=float(a.health_score) if a.health_score else None,
                config=a.config,
                metadata=a.extra_metadata,
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
            for a in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_asset_endpoint(
    body: AssetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = str(current_user.organization_id)

    site_exists = await check_site_exists(db, org_id, body.site_id)
    if not site_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

    code_exists = await check_asset_code_exists(db, org_id, body.code)
    if code_exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Asset code already exists")

    data = body.model_dump(exclude_unset=True)
    extra_metadata = data.pop("metadata", None)

    asset = Asset(
        organization_id=org_id,
        site_id=body.site_id,
        asset_type=data.get("asset_type"),
        name=data.get("name"),
        code=data.get("code"),
        serial_number=data.get("serial_number"),
        manufacturer=data.get("manufacturer"),
        model=data.get("model"),
        capacity_kw=data.get("capacity_kw"),
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        commissioning_date=data.get("commissioning_date"),
        config=data.get("config"),
        extra_metadata=extra_metadata,
    )
    if data.get("parent_asset_id"):
        asset.parent_asset_id = data["parent_asset_id"]

    db.add(asset)
    await db.flush()
    await db.refresh(asset)

    return AssetResponse(
        id=str(asset.id),
        site_id=str(asset.site_id),
        parent_asset_id=str(asset.parent_asset_id) if asset.parent_asset_id else None,
        asset_type=asset.asset_type,
        name=asset.name,
        code=asset.code,
        serial_number=asset.serial_number,
        manufacturer=asset.manufacturer,
        model=asset.model,
        capacity_kw=float(asset.capacity_kw) if asset.capacity_kw else None,
        latitude=float(asset.latitude) if asset.latitude else None,
        longitude=float(asset.longitude) if asset.longitude else None,
        commissioning_date=asset.commissioning_date,
        status=asset.status,
        health_score=float(asset.health_score) if asset.health_score else None,
        config=asset.config,
        metadata=asset.extra_metadata,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


@router.get("/{asset_id}")
async def get_asset_endpoint(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    asset = await get_asset(db, str(current_user.organization_id), asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    site_data = None
    if asset.site:
        site_data = {"id": str(asset.site.id), "name": asset.site.name, "code": asset.site.code}

    children_data = []
    for child in asset.children:
        children_data.append(AssetBrief(
            id=str(child.id),
            name=child.name,
            asset_type=child.asset_type,
            capacity_kw=float(child.capacity_kw) if child.capacity_kw else None,
            status=child.status,
        ))

    return AssetDetailResponse(
        id=str(asset.id),
        site=site_data,
        parent_asset={"id": str(asset.parent.id), "name": asset.parent.name} if asset.parent else None,
        children=children_data,
        asset_type=asset.asset_type,
        name=asset.name,
        code=asset.code,
        serial_number=asset.serial_number,
        manufacturer=asset.manufacturer,
        model=asset.model,
        capacity_kw=float(asset.capacity_kw) if asset.capacity_kw else None,
        latitude=float(asset.latitude) if asset.latitude else None,
        longitude=float(asset.longitude) if asset.longitude else None,
        commissioning_date=asset.commissioning_date,
        status=asset.status,
        health_score=float(asset.health_score) if asset.health_score else None,
        config=asset.config,
        metadata=asset.extra_metadata,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


@router.put("/{asset_id}")
async def update_asset_endpoint(
    asset_id: str,
    body: AssetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = str(current_user.organization_id)

    if body.code is not None:
        code_exists = await check_asset_code_exists(db, org_id, body.code, exclude_id=asset_id)
        if code_exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Asset code already exists")

    data = body.model_dump(exclude_unset=True)
    if "metadata" in data:
        data["extra_metadata"] = data.pop("metadata")

    asset = await update_asset(db, org_id, asset_id, data)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    return AssetResponse(
        id=str(asset.id),
        site_id=str(asset.site_id),
        parent_asset_id=str(asset.parent_asset_id) if asset.parent_asset_id else None,
        asset_type=asset.asset_type,
        name=asset.name,
        code=asset.code,
        serial_number=asset.serial_number,
        manufacturer=asset.manufacturer,
        model=asset.model,
        capacity_kw=float(asset.capacity_kw) if asset.capacity_kw else None,
        latitude=float(asset.latitude) if asset.latitude else None,
        longitude=float(asset.longitude) if asset.longitude else None,
        commissioning_date=asset.commissioning_date,
        status=asset.status,
        health_score=float(asset.health_score) if asset.health_score else None,
        config=asset.config,
        metadata=asset.extra_metadata,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


@router.delete("/{asset_id}", status_code=status.HTTP_200_OK)
async def decommission_asset(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = str(current_user.organization_id)

    children_result = await db.execute(
        select(func.count(Asset.id)).where(
            Asset.parent_asset_id == asset_id,
            Asset.organization_id == org_id,
            Asset.status != "retired",
        )
    )
    active_children = children_result.scalar() or 0
    if active_children > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot decommission asset with active children. Remove or retire children first.",
        )

    success = await delete_asset(db, org_id, asset_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    return {"message": "Asset decommissioned successfully", "asset_id": asset_id, "status": "retired"}


# --- Sites ---

sites_router = APIRouter()


@sites_router.get("")
async def list_sites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    q: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await get_sites(
        db, str(current_user.organization_id), page, page_size,
        status=status, q=q,
    )

    response_items = []
    for site in items:
        count_result = await db.execute(
            select(func.count(Asset.id)).where(
                Asset.site_id == site.id,
                Asset.organization_id == str(current_user.organization_id),
            )
        )
        asset_count = count_result.scalar() or 0
        response_items.append(AssetSiteResponse(
            id=str(site.id),
            name=site.name,
            code=site.code,
            description=site.description,
            address=site.address,
            latitude=float(site.latitude) if site.latitude else None,
            longitude=float(site.longitude) if site.longitude else None,
            capacity_mw=float(site.capacity_mw),
            timezone=site.timezone,
            status=site.status,
            asset_count=asset_count,
            created_at=site.created_at,
            updated_at=site.updated_at,
        ))

    return {
        "items": response_items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@sites_router.post("", status_code=status.HTTP_201_CREATED)
async def create_site_endpoint(
    body: AssetSiteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = str(current_user.organization_id)

    code_exists = await check_site_code_exists(db, org_id, body.code)
    if code_exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Site code already exists")

    data = body.model_dump()
    extra_metadata = data.pop("metadata", None)
    data["extra_metadata"] = extra_metadata

    site = AssetSite(organization_id=org_id, **data)
    db.add(site)
    await db.flush()
    await db.refresh(site)

    return AssetSiteResponse(
        id=str(site.id),
        name=site.name,
        code=site.code,
        description=site.description,
        address=site.address,
        latitude=float(site.latitude) if site.latitude else None,
        longitude=float(site.longitude) if site.longitude else None,
        capacity_mw=float(site.capacity_mw),
        timezone=site.timezone,
        status=site.status,
        asset_count=0,
        created_at=site.created_at,
        updated_at=site.updated_at,
    )


@sites_router.get("/{site_id}")
async def get_site_endpoint(
    site_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = str(current_user.organization_id)
    site = await get_site(db, org_id, site_id)
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

    asset_summary = await get_site_asset_summary(db, org_id, site_id)

    asset_ids_subq = select(Asset.id).where(
        Asset.site_id == site_id,
        Asset.organization_id == org_id,
    ).subquery()
    recent_gen_result = await db.execute(
        select(func.sum(TelemetryGeneration.energy_kwh)).where(
            TelemetryGeneration.asset_id.in_(select(asset_ids_subq.c.id)),
            TelemetryGeneration.ts >= func.now() - timedelta(days=1),
        )
    )
    recent_generation = recent_gen_result.scalar()
    recent_generation_kwh = float(recent_generation) if recent_generation else 0.0

    return AssetSiteDetailResponse(
        id=str(site.id),
        name=site.name,
        code=site.code,
        description=site.description,
        address=site.address,
        latitude=float(site.latitude) if site.latitude else None,
        longitude=float(site.longitude) if site.longitude else None,
        capacity_mw=float(site.capacity_mw),
        timezone=site.timezone,
        status=site.status,
        asset_summary=asset_summary,
        recent_generation_kwh=recent_generation_kwh,
        created_at=site.created_at,
        updated_at=site.updated_at,
    )
