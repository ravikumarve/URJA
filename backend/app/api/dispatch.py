import math
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.auth import User
from app.models.dispatch import DispatchRule, DispatchDecision
from app.schemas.dispatch import (
    DispatchRuleCreate,
    DispatchRuleUpdate,
    DispatchRuleResponse,
    DispatchDecisionResponse,
    CurtailmentEventResponse,
    RevenueLostResponse,
    PaginationMeta,
)

router = APIRouter()
curtailment_router = APIRouter()


@router.get("/rules")
async def list_dispatch_rules(
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = current_user.organization_id
    stmt = text("""
        SELECT id, name, description, is_active, priority,
               condition_type, condition_config, action, action_config,
               target_asset_type, cooldown_minutes, last_triggered_at,
               created_at, updated_at
        FROM dispatch_rules
        WHERE organization_id = :org_id
        ORDER BY priority ASC, created_at DESC
    """)
    cursor = await db.execute(stmt, {"org_id": org_id})
    rows = cursor.fetchall()
    data = [
        DispatchRuleResponse(
            id=r[0], name=r[1], description=r[2], is_active=r[3],
            priority=r[4], condition_type=r[5], condition_config=r[6] or {},
            action=r[7], action_config=r[8] or {},
            target_asset_type=r[9], cooldown_minutes=r[10],
            last_triggered_at=r[11], created_at=r[12], updated_at=r[13],
        ) for r in rows
    ]
    return {"data": data}


@router.post("/rules", status_code=status.HTTP_201_CREATED)
async def create_dispatch_rule(
    rule: DispatchRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    org_id = current_user.organization_id
    existing = await db.execute(
        text("SELECT id FROM dispatch_rules WHERE organization_id = :org_id AND name = :name"),
        {"org_id": org_id, "name": rule.name},
    )
    if existing.scalar():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Rule name already exists")

    row = DispatchRule(
        organization_id=org_id,
        name=rule.name,
        description=rule.description,
        priority=rule.priority,
        condition_type=rule.condition_type,
        condition_config=rule.condition_config,
        action=rule.action,
        action_config=rule.action_config,
        target_asset_type=rule.target_asset_type,
        cooldown_minutes=rule.cooldown_minutes,
    )
    db.add(row)
    await db.flush()

    return DispatchRuleResponse(
        id=row.id, name=row.name, description=row.description,
        is_active=row.is_active, priority=row.priority,
        condition_type=row.condition_type, condition_config=row.condition_config,
        action=row.action, action_config=row.action_config,
        target_asset_type=row.target_asset_type, cooldown_minutes=row.cooldown_minutes,
        last_triggered_at=row.last_triggered_at, created_at=row.created_at, updated_at=row.updated_at,
    )


@router.put("/rules/{rule_id}")
async def update_dispatch_rule(
    rule_id: UUID,
    rule: DispatchRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    org_id = current_user.organization_id
    result = await db.execute(
        text("SELECT * FROM dispatch_rules WHERE id = :id AND organization_id = :org_id"),
        {"id": rule_id, "org_id": org_id},
    )
    existing = result.fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    updates = {}
    for field in ("name", "description", "is_active", "priority", "condition_type", "action", "target_asset_type", "cooldown_minutes"):
        val = getattr(rule, field, None)
        if val is not None:
            updates[field] = val
    if rule.condition_config is not None:
        updates["condition_config"] = rule.condition_config
    if rule.action_config is not None:
        updates["action_config"] = rule.action_config

    if updates:
        set_parts = ", ".join(f"{k} = :{k}" for k in updates)
        updates["id"] = rule_id
        await db.execute(
            text(f"UPDATE dispatch_rules SET {set_parts}, updated_at = now() WHERE id = :id"),
            updates,
        )
        await db.flush()

    cursor = await db.execute(
        text("SELECT id, name, description, is_active, priority, condition_type, condition_config, action, action_config, target_asset_type, cooldown_minutes, last_triggered_at, created_at, updated_at FROM dispatch_rules WHERE id = :id"),
        {"id": rule_id},
    )
    r = cursor.fetchone()
    return DispatchRuleResponse(
        id=r[0], name=r[1], description=r[2], is_active=r[3],
        priority=r[4], condition_type=r[5], condition_config=r[6] or {},
        action=r[7], action_config=r[8] or {},
        target_asset_type=r[9], cooldown_minutes=r[10],
        last_triggered_at=r[11], created_at=r[12], updated_at=r[13],
    )


@router.delete("/rules/{rule_id}")
async def delete_dispatch_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    org_id = current_user.organization_id
    result = await db.execute(
        text("DELETE FROM dispatch_rules WHERE id = :id AND organization_id = :org_id RETURNING id"),
        {"id": rule_id, "org_id": org_id},
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    await db.flush()
    return {"data": {"message": "Rule deleted successfully"}}


@router.get("/decisions")
async def list_dispatch_decisions(
    rule_id: Optional[str] = Query(None),
    asset_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    cursor: Optional[str] = Query(None),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = current_user.organization_id
    conditions = ["d.organization_id = :org_id"]
    params: dict = {"org_id": org_id, "limit": per_page + 1}

    if rule_id:
        conditions.append("d.rule_id = :rule_id")
        params["rule_id"] = rule_id
    if asset_id:
        conditions.append("d.asset_id = :asset_id")
        params["asset_id"] = asset_id
    if status_filter:
        conditions.append("d.status = :status")
        params["status"] = status_filter
    if start_date:
        conditions.append("d.created_at >= :start_date")
        params["start_date"] = start_date
    if end_date:
        conditions.append("d.created_at < :end_date")
        params["end_date"] = end_date

    where = " AND ".join(conditions)
    stmt = text(f"""
        SELECT d.id, r.name AS rule_name, a.name AS asset_name,
               d.status, d.action_taken, d.action_params,
               d.triggered_value, d.expected_outcome, d.actual_outcome,
               d.duration_seconds, d.executed_at, d.created_at
        FROM dispatch_decisions d
        LEFT JOIN dispatch_rules r ON r.id = d.rule_id
        LEFT JOIN assets a ON a.id = d.asset_id
        WHERE {where}
        ORDER BY d.created_at DESC
        LIMIT :limit
    """)
    cursor = await db.execute(stmt, params)
    rows = cursor.fetchall()
    has_more = len(rows) > per_page
    if has_more:
        rows = rows[:per_page]

    data = [
        DispatchDecisionResponse(
            id=r[0], rule_name=r[1], asset_name=r[2],
            status=r[3], action_taken=r[4], action_params=r[5] or {},
            triggered_value=r[6], expected_outcome=r[7], actual_outcome=r[8],
            duration_seconds=r[9], executed_at=r[10], created_at=r[11],
        ) for r in rows
    ]
    return {
        "data": data,
        "pagination": PaginationMeta(has_more=has_more, total=len(data)),
    }


@curtailment_router.get("/events")
async def list_curtailment_events(
    asset_id: Optional[str] = Query(None),
    site_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    is_resolved: Optional[bool] = Query(None),
    cursor: Optional[str] = Query(None),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = current_user.organization_id
    conditions = ["c.organization_id = :org_id"]
    params: dict = {"org_id": org_id, "limit": per_page + 1}

    if asset_id:
        conditions.append("c.asset_id = :asset_id")
        params["asset_id"] = asset_id
    if site_id:
        conditions.append("a.site_id = :site_id")
        params["site_id"] = site_id
    if start_date:
        conditions.append("c.ts >= :start_date")
        params["start_date"] = start_date
    if end_date:
        conditions.append("c.ts < :end_date")
        params["end_date"] = end_date
    if is_resolved is not None:
        conditions.append("c.is_resolved = :is_resolved")
        params["is_resolved"] = is_resolved

    where = " AND ".join(conditions)
    stmt = text(f"""
        SELECT c.event_id, c.asset_id, a.name AS asset_name,
               s.name AS site_name, c.ts, c.duration_minutes,
               c.expected_kwh, c.actual_kwh, c.curtailed_kwh,
               c.price_per_kwh, c.revenue_lost, c.grid_price_source,
               c.is_resolved, c.resolved_at
        FROM curtailment_events c
        JOIN assets a ON a.id = c.asset_id
        JOIN asset_sites s ON s.id = a.site_id
        WHERE {where}
        ORDER BY c.ts DESC
        LIMIT :limit
    """)
    cursor = await db.execute(stmt, params)
    rows = cursor.fetchall()
    has_more = len(rows) > per_page
    if has_more:
        rows = rows[:per_page]

    data = [
        CurtailmentEventResponse(
            event_id=r[0], asset_id=r[1], asset_name=r[2],
            site_name=r[3], ts=r[4], duration_minutes=r[5],
            expected_kwh=r[6], actual_kwh=r[7], curtailed_kwh=r[8],
            price_per_kwh=r[9], revenue_lost=r[10],
            grid_price_source=r[11], is_resolved=r[12], resolved_at=r[13],
        ) for r in rows
    ]
    return {
        "data": data,
        "pagination": PaginationMeta(has_more=has_more, total=len(data)),
    }


@curtailment_router.get("/revenue-lost")
async def get_revenue_lost(
    start_date: datetime = Query(...),
    end_date: Optional[datetime] = Query(None),
    site_id: Optional[str] = Query(None),
    asset_id: Optional[str] = Query(None),
    granularity: str = Query("total", regex="^(total|daily|monthly|by_asset)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = current_user.organization_id
    if end_date is None:
        end_date = datetime.now(timezone.utc)

    conditions = ["c.organization_id = :org_id", "c.ts >= :start_date", "c.ts < :end_date"]
    params: dict = {"org_id": org_id, "start_date": start_date, "end_date": end_date}

    if site_id:
        conditions.append("a.site_id = :site_id")
        params["site_id"] = site_id
    if asset_id:
        conditions.append("c.asset_id = :asset_id")
        params["asset_id"] = asset_id

    where = " AND ".join(conditions)

    stmt = text(f"""
        SELECT
            COALESCE(SUM(c.curtailed_kwh), 0) AS total_curtailed,
            COALESCE(SUM(c.revenue_lost), 0) AS total_revenue,
            COUNT(*) AS event_count,
            CASE WHEN COUNT(*) > 0 THEN SUM(c.revenue_lost) / NULLIF(SUM(c.curtailed_kwh), 0) ELSE 0 END AS avg_price
        FROM curtailment_events c
        JOIN assets a ON a.id = c.asset_id
        WHERE {where}
    """)
    cursor = await db.execute(stmt, params)
    row = cursor.fetchone()

    by_site = []
    if granularity != "total":
        site_stmt = text(f"""
            SELECT a.site_id, s.name AS site_name,
                   SUM(c.curtailed_kwh) AS curtailed_kwh,
                   SUM(c.revenue_lost) AS revenue_lost
            FROM curtailment_events c
            JOIN assets a ON a.id = c.asset_id
            JOIN asset_sites s ON s.id = a.site_id
            WHERE {where}
            GROUP BY a.site_id, s.name
            ORDER BY revenue_lost DESC
        """)
        site_cursor = await db.execute(site_stmt, params)
        by_site = [
            {"site_id": str(r[0]), "site_name": r[1], "curtailed_kwh": float(r[2]), "revenue_lost": float(r[3])}
            for r in site_cursor.fetchall()
        ]

    return RevenueLostResponse(
        start_date=start_date,
        end_date=end_date,
        total_curtailed_kwh=float(row[0]) if row[0] else 0.0,
        total_revenue_lost=float(row[1]) if row[1] else 0.0,
        event_count=row[2] or 0,
        avg_price_per_kwh=float(row[3]) if row[3] else 0.0,
        by_site=by_site,
    )
