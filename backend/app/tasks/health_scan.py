import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select, func, and_

from app.config import get_settings
from app.models.asset import Asset
from app.models.health import HealthMetric, HealthAlert
from app.models.telemetry import TelemetryGeneration
from app.services.health_scorer import calculate_health_score, detect_anomalies

logger = logging.getLogger(__name__)

settings = get_settings()


async def health_scan(ctx) -> dict:
    run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    scanned = 0
    alerts_created = 0
    errors = []

    async with ctx["session_factory"]() as session:
        try:
            result = await session.execute(
                select(Asset).where(Asset.status == "active")
            )
            assets = result.scalars().all()

            one_hour_ago = now - timedelta(hours=1)
            thirty_days_ago = now - timedelta(days=30)

            for asset in assets:
                try:
                    asset_id = asset.id
                    org_id = asset.organization_id
                    capacity_kw = float(asset.capacity_kw or 1.0)

                    telemetry_result = await session.execute(
                        select(TelemetryGeneration).where(
                            and_(
                                TelemetryGeneration.asset_id == asset_id,
                                TelemetryGeneration.ts >= one_hour_ago,
                            )
                        ).order_by(TelemetryGeneration.ts.asc())
                    )
                    recent_telemetry = telemetry_result.scalars().all()

                    if not recent_telemetry:
                        continue

                    telemetry_data = [
                        {
                            "ts": row.ts,
                            "generation_kw": float(row.generation_kw) if row.generation_kw else 0,
                            "temperature_c": float(row.temperature_c) if row.temperature_c else None,
                            "voltage_v": float(row.voltage_v) if row.voltage_v else None,
                            "quality_code": row.quality_code,
                        }
                        for row in recent_telemetry
                    ]

                    health_result = calculate_health_score(
                        asset_id=asset_id,
                        telemetry_data=telemetry_data,
                        expected_capacity_kw=capacity_kw,
                    )

                    baseline_result = await session.execute(
                        select(
                            func.avg(TelemetryGeneration.generation_kw).label("gen_mean"),
                            func.stddev(TelemetryGeneration.generation_kw).label("gen_std"),
                            func.avg(TelemetryGeneration.temperature_c).label("temp_mean"),
                            func.stddev(TelemetryGeneration.temperature_c).label("temp_std"),
                            func.avg(TelemetryGeneration.voltage_v).label("volt_mean"),
                            func.stddev(TelemetryGeneration.voltage_v).label("volt_std"),
                        ).where(
                            and_(
                                TelemetryGeneration.asset_id == asset_id,
                                TelemetryGeneration.ts >= thirty_days_ago,
                                TelemetryGeneration.ts < one_hour_ago,
                            )
                        )
                    )
                    baseline_row = baseline_result.one_or_none()

                    historical_baseline = None
                    if baseline_row and baseline_row.gen_mean is not None:
                        historical_baseline = {
                            "generation_kw": {
                                "mean": float(baseline_row.gen_mean),
                                "std": float(baseline_row.gen_std or 0),
                            },
                            "temperature_c": {
                                "mean": float(baseline_row.temp_mean or 0),
                                "std": float(baseline_row.temp_std or 0),
                            },
                            "voltage_v": {
                                "mean": float(baseline_row.volt_mean or 0),
                                "std": float(baseline_row.volt_std or 0),
                            },
                        }

                    anomalies = detect_anomalies(
                        asset_id=asset_id,
                        recent_data=telemetry_data,
                        historical_baseline=historical_baseline,
                        threshold_sigma=3.0,
                    )

                    anomaly_flags = health_result.get("anomaly_flags", [])
                    anomaly_score = Decimal(str(health_result["anomaly_score"]))

                    alert_ids = []
                    for anomaly in anomalies:
                        title = f"Anomaly detected: {anomaly['metric']}"
                        description = (
                            f"Observed {anomaly['metric']}={anomaly['observed_value']:.2f}, "
                            f"expected {anomaly['expected_value']:.2f}, "
                            f"z-score={anomaly['z_score']:.2f}"
                        )
                        severity = "critical" if anomaly["anomaly_score"] > settings.HEALTH_ANOMALY_THRESHOLD else "warning"

                        alert = HealthAlert(
                            organization_id=org_id,
                            asset_id=asset_id,
                            title=title,
                            description=description,
                            severity=severity,
                            status="open",
                        )
                        session.add(alert)
                        await session.flush()
                        alert_ids.append(str(alert.id))
                        alerts_created += 1

                        if anomaly["metric"] not in anomaly_flags:
                            anomaly_flags.append(anomaly["metric"])

                    metric = HealthMetric(
                        ts=now,
                        asset_id=asset_id,
                        organization_id=org_id,
                        health_score=Decimal(str(health_result["health_score"])),
                        anomaly_score=anomaly_score,
                        metric_scores=health_result.get("metric_scores", {}),
                        anomaly_flags=anomaly_flags,
                        alert_ids=alert_ids,
                        run_id=uuid.UUID(run_id),
                    )
                    session.add(metric)
                    scanned += 1

                except Exception as e:
                    errors.append(f"Asset {asset.id}: {e}")
                    logger.warning("Health scan failed for asset %s: %s", asset.id, e)

            await session.commit()

        except Exception as e:
            await session.rollback()
            logger.exception("Health scan transaction failed")
            return {
                "status": "error",
                "run_id": run_id,
                "scanned": scanned,
                "alerts_created": alerts_created,
                "errors": [str(e)],
            }

    logger.info(
        "Health scan %s: %d assets scanned, %d alerts created",
        run_id, scanned, alerts_created,
    )
    return {
        "status": "success",
        "run_id": run_id,
        "scanned": scanned,
        "alerts_created": alerts_created,
        "errors": errors,
    }
