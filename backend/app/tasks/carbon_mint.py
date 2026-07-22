import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, and_

from app.config import get_settings
from app.models.carbon import CarbonCredit
from app.models.supporting import AuditLog
from app.models.telemetry import TelemetryGeneration
from app.services.carbon_vault import build_mrv_pipeline, create_credit_hash

logger = logging.getLogger(__name__)

settings = get_settings()


async def mint_carbon_credits(
    ctx, org_id: str, asset_ids: list[str], from_date: str, to_date: str
) -> dict:
    batch_id = str(uuid.uuid4())
    credits_created = []
    errors = []
    total_co2e = Decimal("0")

    from_dt = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
    to_dt = datetime.fromisoformat(to_date.replace("Z", "+00:00"))

    async with ctx["session_factory"]() as session:
        try:
            for asset_id in asset_ids:
                result = await session.execute(
                    select(TelemetryGeneration).where(
                        and_(
                            TelemetryGeneration.asset_id == asset_id,
                            TelemetryGeneration.ts >= from_dt,
                            TelemetryGeneration.ts < to_dt,
                        )
                    ).order_by(TelemetryGeneration.ts.asc())
                )
                telemetry_rows = result.scalars().all()

                if not telemetry_rows:
                    errors.append(f"No telemetry for asset {asset_id} in range")
                    continue

                generation_data = [
                    {
                        "ts": row.ts,
                        "generation_kw": float(row.generation_kw) if row.generation_kw else 0,
                        "energy_kwh": float(row.energy_kwh) if row.energy_kwh else float(row.generation_kw) * 0.25,
                        "quality_code": row.quality_code,
                    }
                    for row in telemetry_rows
                ]

                pipeline = build_mrv_pipeline(
                    generation_data=generation_data,
                    asset_id=uuid.UUID(asset_id),
                    org_id=uuid.UUID(org_id),
                    emission_factor=Decimal(str(settings.CARBON_CREDIT_PER_MWH)),
                    methodology=settings.MRV_METHODOLOGY_VERSION,
                )

                if not pipeline["valid"]:
                    errors.append(f"MRV pipeline failed for asset {asset_id}: {pipeline.get('reason')}")
                    continue

                previous_result = await session.execute(
                    select(CarbonCredit).where(
                        CarbonCredit.organization_id == org_id
                    ).order_by(CarbonCredit.ts.desc()).limit(1)
                )
                previous_credit = previous_result.scalar_one_or_none()
                prev_dict = None
                if previous_credit:
                    prev_dict = {"hash": str(previous_credit.registry_tx_id or "")}

                sequence_num = (previous_credit and 1) or 0
                tx_hash = create_credit_hash(
                    previous_credit=prev_dict,
                    org_id=uuid.UUID(org_id),
                    sequence_num=sequence_num,
                    total_mwh=pipeline["total_mwh"],
                    timestamp=datetime.now(timezone.utc),
                )

                now = datetime.now(timezone.utc)
                credit = CarbonCredit(
                    ts=now,
                    asset_id=uuid.UUID(asset_id),
                    organization_id=uuid.UUID(org_id),
                    batch_id=uuid.UUID(batch_id),
                    status="active",
                    quantity=pipeline["total_co2e"],
                    unit="tCO2e",
                    methodology=settings.MRV_METHODOLOGY_VERSION,
                    generation_start=from_dt,
                    generation_end=to_dt,
                    total_kwh=pipeline["total_kwh"],
                    emission_factor=Decimal(str(settings.CARBON_CREDIT_PER_MWH)),
                    registry_tx_id=tx_hash,
                )
                session.add(credit)
                await session.flush()

                audit = AuditLog(
                    organization_id=uuid.UUID(org_id),
                    actor_type="system",
                    actor_id="task:carbon_mint",
                    action="carbon.credit_minted",
                    target_type="CarbonCredit",
                    target_id=str(credit.credit_id),
                    changes={
                        "batch_id": batch_id,
                        "asset_id": asset_id,
                        "total_kwh": str(pipeline["total_kwh"]),
                        "co2e": str(pipeline["total_co2e"]),
                        "tx_hash": tx_hash,
                    },
                )
                session.add(audit)

                credits_created.append({
                    "credit_id": str(credit.credit_id),
                    "asset_id": asset_id,
                    "total_kwh": float(pipeline["total_kwh"]),
                    "total_mwh": float(pipeline["total_mwh"]),
                    "co2_eq_tonnes": float(pipeline["total_co2e"]),
                    "tx_hash": tx_hash,
                })
                total_co2e += pipeline["total_co2e"]

            await session.commit()

        except Exception as e:
            await session.rollback()
            logger.exception("Carbon mint transaction failed")
            return {
                "status": "error",
                "batch_id": batch_id,
                "credits_created": credits_created,
                "errors": [str(e)],
            }

    logger.info(
        "Carbon mint batch %s: %d credits, %.2f tCO2e",
        batch_id, len(credits_created), float(total_co2e),
    )
    return {
        "status": "success",
        "batch_id": batch_id,
        "credits_created": credits_created,
        "total_co2_eq_tonnes": float(total_co2e),
        "errors": errors,
    }
