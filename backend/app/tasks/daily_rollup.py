import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import text, select, func, and_

from app.config import get_settings
from app.models.asset import Asset
from app.models.telemetry import TelemetryGeneration

logger = logging.getLogger(__name__)

settings = get_settings()

CREATE_DAILY_SUMMARY_TABLE = text("""
    CREATE TABLE IF NOT EXISTS asset_daily_summary (
        date DATE NOT NULL,
        asset_id UUID NOT NULL,
        organization_id UUID NOT NULL,
        avg_kw NUMERIC(12, 4),
        peak_kw NUMERIC(12, 4),
        min_kw NUMERIC(12, 4),
        total_kwh NUMERIC(14, 4),
        capacity_factor_pct NUMERIC(6, 2),
        reading_count INTEGER,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        PRIMARY KEY (date, asset_id)
    )
""")


async def daily_rollup(ctx) -> dict:
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    results = {}
    errors = []

    async with ctx["session_factory"]() as session:
        try:
            await session.execute(CREATE_DAILY_SUMMARY_TABLE)

            compress_after = f"{settings.TELEMETRY_COMPRESS_AFTER_DAYS} days"
            try:
                await session.execute(
                    text("""
                        SELECT add_compression_policy(
                            'telemetry_generation',
                            INTERVAL :compress_after,
                            if_not_exists => true
                        )
                    """),
                    {"compress_after": compress_after},
                )
                results["compression_policy"] = "ensured"
            except Exception as e:
                errors.append(f"Compression policy: {e}")
                results["compression_policy"] = "skipped"

            compressed = 0
            for table in ["telemetry_generation", "telemetry_weather", "grid_prices", "health_metrics"]:
                try:
                    result = await session.execute(
                        text("SELECT compress_chunk(c) FROM show_chunks(:table) c WHERE c < now() - INTERVAL '30 days'"),
                        {"table": table},
                    )
                    compressed += len(result.all())
                except Exception:
                    pass
            results["chunks_compressed"] = compressed

            asset_result = await session.execute(
                select(Asset.id, Asset.organization_id, Asset.capacity_kw).where(
                    Asset.status == "active"
                )
            )
            assets = asset_result.all()
            daily_summaries = 0

            for asset_id, org_id, cap_kw in assets:
                try:
                    agg = await session.execute(
                        select(
                            func.avg(TelemetryGeneration.generation_kw).label("avg_kw"),
                            func.max(TelemetryGeneration.generation_kw).label("peak_kw"),
                            func.min(TelemetryGeneration.generation_kw).label("min_kw"),
                            func.sum(TelemetryGeneration.energy_kwh).label("total_kwh"),
                            func.count(TelemetryGeneration.ts).label("reading_count"),
                        ).where(
                            and_(
                                TelemetryGeneration.asset_id == asset_id,
                                TelemetryGeneration.ts >= yesterday,
                                TelemetryGeneration.ts < now,
                            )
                        )
                    )
                    row = agg.one_or_none()
                    if row and row.reading_count and row.reading_count > 0:
                        capacity = float(cap_kw or 1.0)
                        capacity_factor = (float(row.avg_kw or 0) / capacity) * 100 if capacity > 0 else 0
                        await session.execute(
                            text("""
                                INSERT INTO asset_daily_summary
                                    (date, asset_id, organization_id, avg_kw, peak_kw, min_kw,
                                     total_kwh, capacity_factor_pct, reading_count, created_at)
                                VALUES
                                    (:date, :asset_id, :org_id, :avg_kw, :peak_kw, :min_kw,
                                     :total_kwh, :capacity_factor, :reading_count, :created_at)
                                ON CONFLICT (date, asset_id) DO UPDATE SET
                                    avg_kw = EXCLUDED.avg_kw,
                                    peak_kw = EXCLUDED.peak_kw,
                                    min_kw = EXCLUDED.min_kw,
                                    total_kwh = EXCLUDED.total_kwh,
                                    capacity_factor_pct = EXCLUDED.capacity_factor_pct,
                                    reading_count = EXCLUDED.reading_count,
                                    updated_at = EXCLUDED.created_at
                            """),
                            {
                                "date": yesterday.date(),
                                "asset_id": asset_id,
                                "org_id": org_id,
                                "avg_kw": float(row.avg_kw or 0),
                                "peak_kw": float(row.peak_kw or 0),
                                "min_kw": float(row.min_kw or 0),
                                "total_kwh": float(row.total_kwh or 0),
                                "capacity_factor": round(capacity_factor, 2),
                                "reading_count": row.reading_count,
                                "created_at": now,
                            },
                        )
                        daily_summaries += 1

                except Exception as e:
                    errors.append(f"Asset daily summary {asset_id}: {e}")

            try:
                retention = f"{settings.TELEMETRY_RETENTION_DAYS} days"
                await session.execute(
                    text("DELETE FROM telemetry_generation WHERE ts < now() - INTERVAL :retention"),
                    {"retention": retention},
                )
                results["old_data_pruned"] = True
            except Exception as e:
                results["old_data_pruned"] = str(e)

            results["daily_summaries"] = daily_summaries
            await session.commit()

        except Exception as e:
            await session.rollback()
            logger.exception("Daily rollup failed")
            return {
                "status": "error",
                "date": yesterday.date().isoformat(),
                "results": results,
                "errors": [str(e)],
            }

    logger.info(
        "Daily rollup %s: %d summaries, %d chunks compressed",
        yesterday.date(), daily_summaries, compressed,
    )
    return {
        "status": "success",
        "date": yesterday.date().isoformat(),
        "results": results,
        "errors": errors,
    }
