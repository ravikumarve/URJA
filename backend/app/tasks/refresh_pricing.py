import logging
import random
from datetime import datetime, timezone

from sqlalchemy import select, insert

from app.models.asset import AssetSite
from app.models.telemetry import GridPrice

logger = logging.getLogger(__name__)


def _generate_simulated_price(site: AssetSite, hour: int) -> dict:
    base_price = 3.5  # INR/kWh — Indian wholesale band (₹2–5 typical, peaks higher)
    peak_multiplier = 1.0
    if 8 <= hour <= 18:
        peak_multiplier = random.uniform(1.5, 3.0)
    elif 0 <= hour <= 5:
        peak_multiplier = random.uniform(0.3, 0.7)
    else:
        peak_multiplier = random.uniform(0.8, 1.2)
    return {
        "price_per_kwh": round(base_price * peak_multiplier, 6),
        "currency": "INR",
        "source": "simulated",
        "market_region": "default",
        "is_forecast": True,
    }


async def refresh_grid_pricing(ctx) -> dict:
    now = datetime.now(timezone.utc)
    inserted = 0
    errors = []

    async with ctx["session_factory"]() as session:
        try:
            result = await session.execute(
                select(AssetSite).where(AssetSite.status == "active")
            )
            sites = result.scalars().all()

            for site in sites:
                try:
                    price = _generate_simulated_price(site, now.hour)
                    stmt = insert(GridPrice).values(
                        ts=now,
                        site_id=site.id,
                        organization_id=site.organization_id,
                        price_per_kwh=price["price_per_kwh"],
                        currency=price["currency"],
                        source=price["source"],
                        market_region=price.get("market_region"),
                        is_forecast=price["is_forecast"],
                    )
                    await session.execute(stmt)
                    inserted += 1

                except Exception as e:
                    errors.append(f"Site {site.id}: {e}")

            if inserted > 0:
                await session.commit()

        except Exception as e:
            await session.rollback()
            logger.exception("Pricing refresh failed")
            return {"status": "error", "inserted": inserted, "errors": [str(e)]}

    logger.info("Pricing refresh: %d sites updated", inserted)
    return {"status": "success", "inserted": inserted, "errors": errors}
