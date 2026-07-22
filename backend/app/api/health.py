from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.auth import User
from app.models.health import HealthAlert, MaintenanceWorkOrder
from app.schemas.health import (
    HealthScoreResponse,
    HealthAlertResponse,
    HealthAlertAcknowledgeResponse,
    AnomalyResponse,
    WorkOrderCreate,
    WorkOrderUpdate,
    WorkOrderResponse,
)
from app.schemas.dispatch import PaginationMeta

router = APIRouter()
maintenance_router = APIRouter()


@router.get("/scores")
async def list_health_scores(
    site_id: Optional[str] = Query(None),
    asset_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    health_max: Optional[float] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = current_user.organization_id
    conditions = ["hm.organization_id = :org_id"]
    params: dict = {"org_id": org_id}

    if asset_id:
        conditions.append("hm.asset_id = :asset_id")
        params["asset_id"] = asset_id
    if site_id:
        conditions.append("a.site_id = :site_id")
        params["site_id"] = site_id
    if status_filter:
        conditions.append("a.status = :asset_status")
        params["asset_status"] = status_filter
    if health_max is not None:
        conditions.append("hm.health_score <= :health_max")
        params["health_max"] = health_max

    where = " AND ".join(conditions)
    stmt = text(f"""
        SELECT DISTINCT ON (hm.asset_id)
            hm.asset_id, a.name AS asset_name, a.asset_type,
            s.name AS site_name, hm.health_score, hm.anomaly_score,
            hm.metric_scores, hm.anomaly_flags, hm.ts
        FROM health_metrics hm
        JOIN assets a ON a.id = hm.asset_id
        JOIN asset_sites s ON s.id = a.site_id
        WHERE {where}
        ORDER BY hm.asset_id, hm.ts DESC
    """)
    cursor = await db.execute(stmt, params)
    rows = cursor.fetchall()

    data = [
        HealthScoreResponse(
            asset_id=r[0], asset_name=r[1], asset_type=r[2],
            site_name=r[3], health_score=r[4], anomaly_score=r[5],
            trend="stable",
            metric_scores=r[6] or {},
            anomaly_flags=r[7] or [],
            last_checked_at=r[8],
        ) for r in rows
    ]
    return {"data": data}


@router.get("/alerts")
async def list_alerts(
    status_filter: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = Query(None),
    asset_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    cursor: Optional[str] = Query(None),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = current_user.organization_id
    conditions = ["ha.organization_id = :org_id"]
    params: dict = {"org_id": org_id, "limit": per_page + 1}

    if status_filter:
        conditions.append("ha.status = :status")
        params["status"] = status_filter
    if severity:
        conditions.append("ha.severity = :severity")
        params["severity"] = severity
    if asset_id:
        conditions.append("ha.asset_id = :asset_id")
        params["asset_id"] = asset_id
    if start_date:
        conditions.append("ha.created_at >= :start_date")
        params["start_date"] = start_date

    where = " AND ".join(conditions)
    stmt = text(f"""
        SELECT ha.id, ha.asset_id, a.name AS asset_name, s.name AS site_name,
               ha.title, ha.description, ha.severity, ha.status,
               ha.acknowledged_by, ha.acknowledged_at, ha.resolved_at, ha.created_at
        FROM health_alerts ha
        LEFT JOIN assets a ON a.id = ha.asset_id
        LEFT JOIN asset_sites s ON s.id = a.site_id
        WHERE {where}
        ORDER BY ha.created_at DESC
        LIMIT :limit
    """)
    cursor = await db.execute(stmt, params)
    rows = cursor.fetchall()
    has_more = len(rows) > per_page
    if has_more:
        rows = rows[:per_page]

    data = [
        HealthAlertResponse(
            id=r[0], asset_id=r[1], asset_name=r[2], site_name=r[3],
            title=r[4], description=r[5], severity=r[6], status=r[7],
            acknowledged_by=r[8], acknowledged_at=r[9], resolved_at=r[10],
            created_at=r[11],
        ) for r in rows
    ]
    return {
        "data": data,
        "pagination": PaginationMeta(has_more=has_more, total=len(data)),
    }


@router.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = current_user.organization_id
    result = await db.execute(
        text("""
            SELECT id, status FROM health_alerts
            WHERE id = :id AND organization_id = :org_id
            FOR UPDATE
        """),
        {"id": alert_id, "org_id": org_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    if row[1] != "open":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Alert already {row[1]}",
        )

    now = datetime.now(timezone.utc)
    await db.execute(
        text("""
            UPDATE health_alerts
            SET status = 'acknowledged', acknowledged_by = :user_id, acknowledged_at = :now
            WHERE id = :id
        """),
        {"id": alert_id, "user_id": current_user.id, "now": now},
    )
    await db.flush()

    return HealthAlertAcknowledgeResponse(
        id=alert_id,
        status="acknowledged",
        acknowledged_at=now,
        acknowledged_by=current_user.id,
    )


@router.get("/anomalies")
async def list_anomalies(
    asset_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    min_score: Optional[float] = Query(None),
    cursor: Optional[str] = Query(None),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = current_user.organization_id
    conditions = ["ae.organization_id = :org_id"]
    params: dict = {"org_id": org_id, "limit": per_page + 1}

    if asset_id:
        conditions.append("ae.asset_id = :asset_id")
        params["asset_id"] = asset_id
    if start_date:
        conditions.append("ae.ts >= :start_date")
        params["start_date"] = start_date
    if end_date:
        conditions.append("ae.ts < :end_date")
        params["end_date"] = end_date

    where = " AND ".join(conditions)

    stmt = text(f"""
        SELECT ae.id, ae.asset_id, a.name AS asset_name,
               ae.ts::timestamptz AS ts,
               'generation_kw' AS metric,
               ae.anomaly_score AS anomaly_score_n,
               0 AS observed, 0 AS expected, 0 AS z_score_n
        FROM health_metrics ae
        LEFT JOIN assets a ON a.id = ae.asset_id
        WHERE {where}
          AND ae.anomaly_score IS NOT NULL
          AND (ae.anomaly_score >= :min_score OR :min_score IS NULL)
        ORDER BY ae.ts DESC
        LIMIT :limit
    """)
    params["min_score"] = min_score or 0
    cursor = await db.execute(stmt, params)
    rows = cursor.fetchall()
    has_more = len(rows) > per_page
    if has_more:
        rows = rows[:per_page]

    data = []
    for r in rows:
        anomaly_id = r[0]
        alert_result = await db.execute(
            text("""
                SELECT id FROM health_alerts
                WHERE asset_id = :asset_id AND score_id = :score_id
                LIMIT 1
            """),
            {"asset_id": r[1], "score_id": anomaly_id},
        )
        alert_row = alert_result.fetchone()

        data.append(AnomalyResponse(
            id=anomaly_id, asset_id=r[1], asset_name=r[2],
            ts=r[3], metric="anomaly_score",
            observed_value=float(r[5]) if r[5] else 0.0,
            anomaly_score=r[5],
            method="z_score",
            triggered_alert_id=alert_row[0] if alert_row else None,
            created_at=r[3],
        ))

    return {
        "data": data,
        "pagination": PaginationMeta(has_more=has_more, total=len(data)),
    }


@maintenance_router.get("/work-orders")
async def list_work_orders(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = Query(None),
    asset_id: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    overdue: Optional[bool] = Query(None),
    cursor: Optional[str] = Query(None),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = current_user.organization_id
    conditions = ["wo.organization_id = :org_id"]
    params: dict = {"org_id": org_id, "limit": per_page + 1}

    if status_filter:
        conditions.append("wo.status = :status")
        params["status"] = status_filter
    if priority:
        conditions.append("wo.priority = :priority")
        params["priority"] = priority
    if asset_id:
        conditions.append("wo.asset_id = :asset_id")
        params["asset_id"] = asset_id
    if assigned_to:
        conditions.append("wo.assigned_to = :assigned_to")
        params["assigned_to"] = assigned_to
    if overdue:
        conditions.append("wo.scheduled_end < now() AND wo.status IN ('scheduled', 'in_progress')")
    where = " AND ".join(conditions)

    stmt = text(f"""
        SELECT wo.id, wo.asset_id, a.name AS asset_name, s.name AS site_name,
               wo.alert_id, wo.assigned_to, u.display_name AS assigned_to_name,
               wo.title, wo.description, wo.priority, wo.status,
               wo.scheduled_start, wo.scheduled_end, wo.actual_start, wo.actual_end,
               wo.estimated_cost, wo.actual_cost, wo.parts_used,
               wo.resolution_notes, wo.created_at, wo.updated_at
        FROM maintenance_work_orders wo
        LEFT JOIN assets a ON a.id = wo.asset_id
        LEFT JOIN asset_sites s ON s.id = a.site_id
        LEFT JOIN users u ON u.id = wo.assigned_to
        WHERE {where}
        ORDER BY wo.created_at DESC
        LIMIT :limit
    """)
    cursor = await db.execute(stmt, params)
    rows = cursor.fetchall()
    has_more = len(rows) > per_page
    if has_more:
        rows = rows[:per_page]

    data = [
        WorkOrderResponse(
            id=r[0], asset_id=r[1], asset_name=r[2], site_name=r[3],
            alert_id=r[4], assigned_to=r[5], assigned_to_name=r[6],
            title=r[7], description=r[8], priority=r[9], status=r[10],
            scheduled_start=r[11], scheduled_end=r[12],
            actual_start=r[13], actual_end=r[14],
            estimated_cost=r[15], actual_cost=r[16],
            parts_used=r[17] or [], resolution_notes=r[18],
            created_at=r[19], updated_at=r[20],
        ) for r in rows
    ]
    return {
        "data": data,
        "pagination": PaginationMeta(has_more=has_more, total=len(data)),
    }


@maintenance_router.post("/work-orders", status_code=status.HTTP_201_CREATED)
async def create_work_order(
    wo: WorkOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    org_id = current_user.organization_id

    asset_check = await db.execute(
        text("SELECT id FROM assets WHERE id = :id AND organization_id = :org_id"),
        {"id": wo.asset_id, "org_id": org_id},
    )
    if not asset_check.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    row = MaintenanceWorkOrder(
        organization_id=org_id,
        asset_id=wo.asset_id,
        alert_id=wo.alert_id,
        assigned_to=wo.assigned_to,
        title=wo.title,
        description=wo.description,
        priority=wo.priority,
        scheduled_start=wo.scheduled_start,
        scheduled_end=wo.scheduled_end,
        estimated_cost=wo.estimated_cost,
    )
    db.add(row)
    await db.flush()

    result = await db.execute(
        text("""
            SELECT wo.id, wo.asset_id, a.name AS asset_name, s.name AS site_name,
                   wo.alert_id, wo.assigned_to, u.display_name,
                   wo.title, wo.description, wo.priority, wo.status,
                   wo.scheduled_start, wo.scheduled_end, wo.actual_start, wo.actual_end,
                   wo.estimated_cost, wo.actual_cost, wo.parts_used,
                   wo.resolution_notes, wo.created_at, wo.updated_at
            FROM maintenance_work_orders wo
            LEFT JOIN assets a ON a.id = wo.asset_id
            LEFT JOIN asset_sites s ON s.id = a.site_id
            LEFT JOIN users u ON u.id = wo.assigned_to
            WHERE wo.id = :id
        """),
        {"id": row.id},
    )
    r = result.fetchone()
    return WorkOrderResponse(
        id=r[0], asset_id=r[1], asset_name=r[2], site_name=r[3],
        alert_id=r[4], assigned_to=r[5], assigned_to_name=r[6],
        title=r[7], description=r[8], priority=r[9], status=r[10],
        scheduled_start=r[11], scheduled_end=r[12],
        actual_start=r[13], actual_end=r[14],
        estimated_cost=r[15], actual_cost=r[16],
        parts_used=r[17] or [], resolution_notes=r[18],
        created_at=r[19], updated_at=r[20],
    )


@maintenance_router.put("/work-orders/{work_order_id}")
async def update_work_order(
    work_order_id: UUID,
    wo: WorkOrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    org_id = current_user.organization_id
    result = await db.execute(
        text("SELECT id FROM maintenance_work_orders WHERE id = :id AND organization_id = :org_id"),
        {"id": work_order_id, "org_id": org_id},
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order not found")

    updates = {}
    for field in ("title", "description", "priority", "status", "assigned_to",
                  "scheduled_start", "scheduled_end", "actual_start", "actual_end",
                  "estimated_cost", "actual_cost", "resolution_notes"):
        val = getattr(wo, field, None)
        if val is not None:
            updates[field] = val
    if wo.parts_used is not None:
        updates["parts_used"] = wo.parts_used

    if updates:
        updates["id"] = work_order_id
        set_parts = ", ".join(f"{k} = :{k}" for k in updates if k != "id")
        await db.execute(
            text(f"UPDATE maintenance_work_orders SET {set_parts}, updated_at = now() WHERE id = :id"),
            updates,
        )
        await db.flush()

    result = await db.execute(
        text("""
            SELECT wo.id, wo.asset_id, a.name AS asset_name, s.name AS site_name,
                   wo.alert_id, wo.assigned_to, u.display_name,
                   wo.title, wo.description, wo.priority, wo.status,
                   wo.scheduled_start, wo.scheduled_end, wo.actual_start, wo.actual_end,
                   wo.estimated_cost, wo.actual_cost, wo.parts_used,
                   wo.resolution_notes, wo.created_at, wo.updated_at
            FROM maintenance_work_orders wo
            LEFT JOIN assets a ON a.id = wo.asset_id
            LEFT JOIN asset_sites s ON s.id = a.site_id
            LEFT JOIN users u ON u.id = wo.assigned_to
            WHERE wo.id = :id
        """),
        {"id": work_order_id},
    )
    r = result.fetchone()
    return WorkOrderResponse(
        id=r[0], asset_id=r[1], asset_name=r[2], site_name=r[3],
        alert_id=r[4], assigned_to=r[5], assigned_to_name=r[6],
        title=r[7], description=r[8], priority=r[9], status=r[10],
        scheduled_start=r[11], scheduled_end=r[12],
        actual_start=r[13], actual_end=r[14],
        estimated_cost=r[15], actual_cost=r[16],
        parts_used=r[17] or [], resolution_notes=r[18],
        created_at=r[19], updated_at=r[20],
    )
