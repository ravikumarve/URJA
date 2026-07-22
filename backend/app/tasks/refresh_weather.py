import logging
import random
from datetime import datetime, timezone

from sqlalchemy import select, insert

from app.models.asset import AssetSite
from app.models.telemetry import TelemetryWeather

logger = logging.getLogger(__name__)


def _generate_simulated_weather(site: AssetSite) -> dict:
    lat = float(site.latitude or 25.0)
    base_temp = 35.0 if abs(lat) < 30 else 20.0
    return {
        "temperature_c": round(base_temp + random.uniform(-5, 5), 2),
        "humidity_pct": round(random.uniform(20, 80), 2),
        "pressure_hpa": round(random.uniform(1000, 1020), 1),
        "wind_speed_ms": round(random.uniform(0, 15), 2),
        "wind_direction_deg": round(random.uniform(0, 360), 1),
        "solar_irradiance_wpm2": round(random.uniform(0, 1000), 2),
        "cloud_cover_pct": round(random.uniform(0, 100), 2),
        "precipitation_mm": round(random.uniform(0, 5) if random.random() > 0.7 else 0, 2),
        "is_forecast": True,
        "source": "simulated",
    }


async def refresh_weather_data(ctx) -> dict:
    now = datetime.now(timezone.utc)
    inserted = 0
    errors = []

    async with ctx["session_factory"]() as session:
        try:
            result = await session.execute(
                select(AssetSite).where(
                    AssetSite.latitude.isnot(None),
                    AssetSite.longitude.isnot(None),
                )
            )
            sites = result.scalars().all()

            for site in sites:
                try:
                    weather = _generate_simulated_weather(site)
                    stmt = insert(TelemetryWeather).values(
                        ts=now,
                        site_id=site.id,
                        organization_id=site.organization_id,
                        temperature_c=weather["temperature_c"],
                        humidity_pct=weather["humidity_pct"],
                        pressure_hpa=weather["pressure_hpa"],
                        wind_speed_ms=weather["wind_speed_ms"],
                        wind_direction_deg=weather["wind_direction_deg"],
                        solar_irradiance_wpm2=weather["solar_irradiance_wpm2"],
                        cloud_cover_pct=weather["cloud_cover_pct"],
                        precipitation_mm=weather["precipitation_mm"],
                        is_forecast=weather["is_forecast"],
                        source=weather["source"],
                    )
                    await session.execute(stmt)
                    inserted += 1

                except Exception as e:
                    errors.append(f"Site {site.id}: {e}")

            if inserted > 0:
                await session.commit()

        except Exception as e:
            await session.rollback()
            logger.exception("Weather refresh failed")
            return {"status": "error", "inserted": inserted, "errors": [str(e)]}

    logger.info("Weather refresh: %d sites updated", inserted)
    return {"status": "success", "inserted": inserted, "errors": errors}
