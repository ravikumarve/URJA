import logging
from datetime import datetime, timezone

from sqlalchemy import insert, select

from app.models.asset import Asset
from app.models.telemetry import TelemetryGeneration

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = {"asset_id", "timestamp", "generation_kw"}


async def process_telemetry_batch(ctx, batch_id: str, records: list[dict]) -> dict:
    errors = []
    inserted = 0
    rejected = 0
    asset_cache: dict[str, str] = {}

    async with ctx["session_factory"]() as session:
        try:
            for record in records:
                missing = REQUIRED_FIELDS - set(record.keys())
                if missing:
                    rejected += 1
                    errors.append(f"Record missing fields: {missing}")
                    continue

                try:
                    asset_id = str(record["asset_id"])

                    if asset_id not in asset_cache:
                        result = await session.execute(
                            select(Asset.organization_id).where(Asset.id == asset_id)
                        )
                        row = result.one_or_none()
                        if row is None:
                            rejected += 1
                            errors.append(f"Asset {asset_id} not found")
                            continue
                        asset_cache[asset_id] = str(row[0])

                    org_id = asset_cache[asset_id]
                    ts = record["timestamp"]
                    if isinstance(ts, str):
                        ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)

                    stmt = insert(TelemetryGeneration).values(
                        ts=ts,
                        asset_id=asset_id,
                        organization_id=org_id,
                        generation_kw=record["generation_kw"],
                        energy_kwh=record.get("energy_kwh"),
                        power_factor=record.get("power_factor"),
                        voltage_v=record.get("voltage_v"),
                        current_a=record.get("current_a"),
                        frequency_hz=record.get("frequency_hz"),
                        temperature_c=record.get("temperature_c"),
                        is_estimated=record.get("is_estimated", False),
                        quality_code=record.get("quality_code", 0),
                    )
                    await session.execute(stmt)
                    inserted += 1

                except Exception as e:
                    rejected += 1
                    errors.append(f"Record error: {e}")

            await session.commit()

        except Exception as e:
            await session.rollback()
            logger.exception("Telemetry batch commit failed")
            return {
                "batch_id": batch_id,
                "status": "error",
                "inserted": inserted,
                "rejected": rejected + (len(records) - inserted - rejected),
                "errors": [str(e)],
            }

    logger.info("Telemetry batch %s: %d inserted, %d rejected", batch_id, inserted, rejected)
    return {
        "batch_id": batch_id,
        "status": "success",
        "inserted": inserted,
        "rejected": rejected,
        "errors": errors[:100],
    }
