import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.auth import User
from app.models.carbon import CarbonCredit
from app.schemas.carbon import (
    CarbonCreditResponse,
    CarbonCreditDetailResponse,
    CarbonIssueRequest,
    CarbonIssueResponse,
    PortfolioSummaryResponse,
    AuditTrailEntry,
)
from app.schemas.dispatch import PaginationMeta
from app.services.carbon_vault import calculate_avoided_emissions, build_mrv_pipeline

router = APIRouter()


@router.get("/credits")
async def list_carbon_credits(
    status_filter: Optional[str] = Query(None, alias="status"),
    asset_id: Optional[str] = Query(None),
    batch_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    cursor: Optional[str] = Query(None),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = current_user.organization_id
    conditions = ["c.organization_id = :org_id"]
    params: dict = {"org_id": org_id, "limit": per_page + 1}

    if status_filter:
        conditions.append("c.status = :status")
        params["status"] = status_filter
    if asset_id:
        conditions.append("c.asset_id = :asset_id")
        params["asset_id"] = asset_id
    if batch_id:
        conditions.append("c.batch_id = :batch_id")
        params["batch_id"] = batch_id
    if start_date:
        conditions.append("c.generation_start >= :start_date")
        params["start_date"] = start_date
    if end_date:
        conditions.append("c.generation_end <= :end_date")
        params["end_date"] = end_date

    where = " AND ".join(conditions)
    stmt = text(f"""
        SELECT c.credit_id, c.batch_id, c.asset_id, a.name AS asset_name,
               c.status, c.quantity, c.unit, c.methodology,
               c.generation_start, c.generation_end, c.total_kwh,
               c.emission_factor, c.registry_tx_id, c.registry_url,
               c.issued_by, c.retired_at, c.notes, c.ts
        FROM carbon_credits c
        LEFT JOIN assets a ON a.id = c.asset_id
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
        CarbonCreditResponse(
            credit_id=r[0], batch_id=r[1], asset_id=r[2],
            asset_name=r[3], status=r[4], quantity=r[5],
            unit=r[6], methodology=r[7], generation_start=r[8],
            generation_end=r[9], total_kwh=r[10], emission_factor=r[11],
            registry_tx_id=r[12], registry_url=r[13], issued_by=r[14],
            retired_at=r[15], notes=r[16], created_at=r[17],
        ) for r in rows
    ]
    return {
        "data": data,
        "pagination": PaginationMeta(has_more=has_more, total=len(data)),
    }


@router.get("/credits/{credit_id}")
async def get_carbon_credit(
    credit_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = current_user.organization_id
    stmt = text("""
        SELECT c.credit_id, c.batch_id, c.asset_id, a.name AS asset_name,
               a.code AS asset_code, c.organization_id,
               c.status, c.quantity, c.unit, c.methodology,
               c.generation_start, c.generation_end, c.total_kwh,
               c.emission_factor, c.registry_tx_id, c.registry_url,
               c.issued_by, c.retired_at, c.notes, c.ts
        FROM carbon_credits c
        LEFT JOIN assets a ON a.id = c.asset_id
        WHERE c.credit_id = :credit_id AND c.organization_id = :org_id
    """)
    cursor = await db.execute(stmt, {"credit_id": credit_id, "org_id": org_id})
    r = cursor.fetchone()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credit not found")

    audit = await db.execute(
        text("""
            SELECT action, actor_id, created_at, extra_metadata->>'details' AS details
            FROM audit_log
            WHERE target_type = 'carbon_credit' AND target_id = :credit_id
            ORDER BY created_at ASC
        """),
        {"credit_id": str(credit_id)},
    )
    audit_trail = [
        AuditTrailEntry(action=row[0], actor=row[1], timestamp=row[2], details=row[3])
        for row in audit.fetchall()
    ]

    if not audit_trail:
        audit_trail = [
            AuditTrailEntry(
                action="credit.created",
                actor=str(r[16]) if r[16] else "system",
                timestamp=r[19],
                details=f"Credit created from batch {r[1]}",
            ),
        ]

    return CarbonCreditDetailResponse(
        credit_id=r[0], batch_id=r[1], asset_id=r[2],
        asset_name=r[3], organization_id=r[5],
        status=r[6], quantity=r[7], unit=r[8], methodology=r[9],
        generation_start=r[10], generation_end=r[11], total_kwh=r[12],
        emission_factor=r[13], registry_tx_id=r[14], registry_url=r[15],
        issued_by=r[16], retired_at=r[17], notes=r[18], created_at=r[19],
        audit_trail=audit_trail,
    )


@router.post("/issue", status_code=status.HTTP_201_CREATED)
async def issue_carbon_credits(
    req: CarbonIssueRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    org_id = current_user.organization_id
    user_id = current_user.id

    asset_check = await db.execute(
        text("SELECT id, organization_id FROM assets WHERE id = :id"),
        {"id": req.asset_id},
    )
    asset = asset_check.fetchone()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    if asset[1] != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    if (req.generation_end - req.generation_start).days > 365:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Generation range exceeds 1 year")

    existing = await db.execute(
        text("""
            SELECT COUNT(*) FROM carbon_credits
            WHERE asset_id = :asset_id
              AND generation_start = :g_start
              AND generation_end = :g_end
              AND organization_id = :org_id
        """),
        {"asset_id": req.asset_id, "g_start": req.generation_start, "g_end": req.generation_end, "org_id": org_id},
    )
    if existing.scalar() > 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Credits already issued for this range")

    org = await db.execute(
        text("SELECT emission_factor FROM organizations WHERE id = :org_id"),
        {"org_id": org_id},
    )
    ef = org.scalar() or Decimal("0.92")

    gen_stmt = text("""
        SELECT ts, generation_kw, energy_kwh, quality_code
        FROM telemetry_generation
        WHERE asset_id = :asset_id
          AND organization_id = :org_id
          AND ts >= :start_date
          AND ts < :end_date
        ORDER BY ts ASC
    """)
    gen_cursor = await db.execute(gen_stmt, {
        "asset_id": req.asset_id,
        "org_id": org_id,
        "start_date": req.generation_start,
        "end_date": req.generation_end,
    })
    gen_rows = [dict(zip(("ts", "generation_kw", "energy_kwh", "quality_code"), r)) for r in gen_cursor.fetchall()]

    pipeline = build_mrv_pipeline(gen_rows, req.asset_id, org_id, ef, req.methodology)
    if not pipeline["valid"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=pipeline["reason"])

    batch_id = uuid.uuid4()
    credit_ids = []
    now = datetime.now(timezone.utc)

    total_co2e = pipeline["total_co2e"]
    credit_count = pipeline["credit_count"]

    for i in range(max(1, credit_count)):
        credit = CarbonCredit(
            ts=now,
            asset_id=req.asset_id,
            organization_id=org_id,
            batch_id=batch_id,
            status="active",
            quantity=Decimal("1"),
            unit="tCO2e",
            methodology=req.methodology,
            generation_start=req.generation_start,
            generation_end=req.generation_end,
            total_kwh=pipeline["total_kwh"],
            emission_factor=ef,
            issued_by=user_id,
            notes=req.notes,
        )
        db.add(credit)
        credit_ids.append(credit.credit_id)

    await db.flush()

    return CarbonIssueResponse(
        batch_id=batch_id,
        total_kwh=pipeline["total_kwh"],
        emission_factor=ef,
        total_co2e=total_co2e,
        credit_count=len(credit_ids),
        credit_ids=credit_ids,
        methodology=req.methodology,
        status="active",
        created_at=now,
    )


@router.get("/portfolio")
async def get_portfolio(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = current_user.organization_id

    stmt = text("""
        SELECT
            COALESCE(COUNT(*), 0) AS total,
            COALESCE(SUM(quantity), 0) AS total_co2e,
            COALESCE(SUM(quantity) FILTER (WHERE status = 'active'), 0) AS active_co2e,
            COALESCE(COUNT(*) FILTER (WHERE status = 'active'), 0) AS active_count,
            COALESCE(SUM(quantity) FILTER (WHERE status = 'retired'), 0) AS retired_co2e,
            COALESCE(COUNT(*) FILTER (WHERE status = 'retired'), 0) AS retired_count,
            COALESCE(COUNT(*) FILTER (WHERE status = 'cancelled'), 0) AS cancelled_count,
            COALESCE(COUNT(*) FILTER (WHERE status = 'pending'), 0) AS pending_count
        FROM carbon_credits
        WHERE organization_id = :org_id
    """)
    cursor = await db.execute(stmt, {"org_id": org_id})
    r = cursor.fetchone()

    total_issued = r[0]
    total_co2e_issued = float(r[1]) if r[1] else 0.0
    active_co2e = float(r[2]) if r[2] else 0.0
    active_count = r[3]
    retired_co2e = float(r[4]) if r[4] else 0.0
    retired_count = r[5]
    cancelled_count = r[6]
    pending_count = r[7]
    available = active_count

    by_status = {
        "active": active_count,
        "retired": retired_count,
        "cancelled": cancelled_count,
        "pending": pending_count,
    }

    methodology_stmt = text("""
        SELECT methodology, COUNT(*) AS cnt
        FROM carbon_credits
        WHERE organization_id = :org_id
        GROUP BY methodology
    """)
    meth_cursor = await db.execute(methodology_stmt, {"org_id": org_id})
    by_methodology = {row[0]: row[1] for row in meth_cursor.fetchall()}

    last = await db.execute(
        text("SELECT MAX(ts) FROM carbon_credits WHERE organization_id = :org_id"),
        {"org_id": org_id},
    )
    last_issuance = last.scalar()

    return PortfolioSummaryResponse(
        total_issued=total_issued,
        total_retired=retired_count,
        total_cancelled=cancelled_count,
        total_available=available,
        total_co2e_issued=total_co2e_issued,
        total_co2e_retired=retired_co2e,
        by_status=by_status,
        by_methodology=by_methodology,
        last_issuance=last_issuance,
        next_eligible_date=datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0),
    )
