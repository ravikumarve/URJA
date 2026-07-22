import uuid
from typing import Optional

from sqlalchemy import select, func, or_, and_, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.asset import Asset, AssetSite


async def get_assets(
    db: AsyncSession,
    org_id: str,
    page: int = 1,
    page_size: int = 20,
    site_id: Optional[str] = None,
    asset_type: Optional[str] = None,
    status: Optional[str] = None,
    q: Optional[str] = None,
    min_capacity: Optional[float] = None,
    max_capacity: Optional[float] = None,
    health_min: Optional[float] = None,
    sort_by: str = "name",
    sort_order: str = "asc",
) -> tuple[list[Asset], int]:
    query = select(Asset).where(
        Asset.organization_id == org_id,
    )

    count_query = select(func.count(Asset.id)).where(
        Asset.organization_id == org_id,
    )

    if site_id:
        query = query.where(Asset.site_id == site_id)
        count_query = count_query.where(Asset.site_id == site_id)
    if asset_type:
        query = query.where(Asset.asset_type == asset_type)
        count_query = count_query.where(Asset.asset_type == asset_type)
    if status:
        query = query.where(Asset.status == status)
        count_query = count_query.where(Asset.status == status)
    if q:
        pattern = f"%{q}%"
        query = query.where(or_(Asset.name.ilike(pattern), Asset.code.ilike(pattern)))
        count_query = count_query.where(or_(Asset.name.ilike(pattern), Asset.code.ilike(pattern)))
    if min_capacity is not None:
        query = query.where(Asset.capacity_kw >= min_capacity)
        count_query = count_query.where(Asset.capacity_kw >= min_capacity)
    if max_capacity is not None:
        query = query.where(Asset.capacity_kw <= max_capacity)
        count_query = count_query.where(Asset.capacity_kw <= max_capacity)
    if health_min is not None:
        query = query.where(Asset.health_score >= health_min)
        count_query = count_query.where(Asset.health_score >= health_min)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    sort_column = getattr(Asset, sort_by, Asset.name)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    items = list(result.scalars().all())
    return items, total


async def get_asset(db: AsyncSession, org_id: str, asset_id: str) -> Optional[Asset]:
    result = await db.execute(
        select(Asset)
        .where(Asset.id == asset_id, Asset.organization_id == org_id)
        .options(joinedload(Asset.site), joinedload(Asset.children))
    )
    return result.unique().scalar_one_or_none()


async def create_asset(db: AsyncSession, org_id: str, data: dict) -> Asset:
    site_id = data.pop("site_id")
    asset = Asset(organization_id=org_id, site_id=site_id, **data)
    db.add(asset)
    await db.flush()
    await db.refresh(asset)
    return asset


async def update_asset(db: AsyncSession, org_id: str, asset_id: str, data: dict) -> Optional[Asset]:
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.organization_id == org_id)
    )
    asset = result.scalar_one_or_none()
    if asset is None:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(asset, key, value)
    await db.flush()
    await db.refresh(asset)
    return asset


async def delete_asset(db: AsyncSession, org_id: str, asset_id: str) -> bool:
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.organization_id == org_id)
    )
    asset = result.scalar_one_or_none()
    if asset is None:
        return False
    asset.status = "retired"
    await db.flush()
    return True


async def get_sites(
    db: AsyncSession, org_id: str, page: int = 1, page_size: int = 20,
    status: Optional[str] = None, q: Optional[str] = None,
) -> tuple[list[AssetSite], int]:
    query = select(AssetSite).where(AssetSite.organization_id == org_id)
    count_query = select(func.count(AssetSite.id)).where(AssetSite.organization_id == org_id)

    if status:
        query = query.where(AssetSite.status == status)
        count_query = count_query.where(AssetSite.status == status)
    if q:
        pattern = f"%{q}%"
        query = query.where(or_(AssetSite.name.ilike(pattern), AssetSite.code.ilike(pattern)))
        count_query = count_query.where(or_(AssetSite.name.ilike(pattern), AssetSite.code.ilike(pattern)))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(AssetSite.name.asc())
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    items = list(result.scalars().all())
    return items, total


async def get_site(db: AsyncSession, org_id: str, site_id: str) -> Optional[AssetSite]:
    result = await db.execute(
        select(AssetSite).where(
            AssetSite.id == site_id, AssetSite.organization_id == org_id
        )
    )
    return result.scalar_one_or_none()


async def get_site_asset_summary(db: AsyncSession, org_id: str, site_id: str) -> dict:
    result = await db.execute(
        select(
            func.count(Asset.id).label("total"),
            Asset.asset_type,
            Asset.status,
            func.sum(
                case((Asset.status == "active", Asset.capacity_kw), else_=0)
            ).label("active_capacity"),
        ).where(
            Asset.organization_id == org_id,
            Asset.site_id == site_id,
        ).group_by(Asset.asset_type, Asset.status)
    )
    rows = result.all()
    total = 0
    by_type = {}
    by_status = {}
    active_capacity = 0.0
    for row in rows:
        total += row.total
        by_type[row.asset_type] = by_type.get(row.asset_type, 0) + row.total
        by_status[row.status] = by_status.get(row.status, 0) + row.total
        if row.status == "active" and row.active_capacity:
            active_capacity += float(row.active_capacity)
    return {
        "total": total,
        "by_type": by_type,
        "by_status": by_status,
        "active_capacity_kw": active_capacity,
    }


async def create_site(db: AsyncSession, org_id: str, data: dict) -> AssetSite:
    site = AssetSite(organization_id=org_id, **data)
    db.add(site)
    await db.flush()
    await db.refresh(site)
    return site


async def check_asset_code_exists(db: AsyncSession, org_id: str, code: str, exclude_id: Optional[str] = None) -> bool:
    query = select(Asset).where(Asset.organization_id == org_id, Asset.code == code)
    if exclude_id:
        query = query.where(Asset.id != exclude_id)
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None


async def check_site_code_exists(db: AsyncSession, org_id: str, code: str) -> bool:
    result = await db.execute(
        select(AssetSite).where(AssetSite.organization_id == org_id, AssetSite.code == code)
    )
    return result.scalar_one_or_none() is not None


async def check_site_exists(db: AsyncSession, org_id: str, site_id: str) -> bool:
    result = await db.execute(
        select(AssetSite).where(AssetSite.id == site_id, AssetSite.organization_id == org_id)
    )
    return result.scalar_one_or_none() is not None
