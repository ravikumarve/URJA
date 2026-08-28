import logging
import pickle
import random
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select, insert

from app.models.asset import AssetSite
from app.models.telemetry import GridPrice

logger = logging.getLogger(__name__)

# Colab LSTM — burst-trained price_forecast.pt + scaler.pkl, inference on Latitude
_FORECAST_MODEL_PATH = Path(__file__).with_name("price_forecast.pt")
_SCALER_PATH = Path(__file__).with_name("scaler.pkl")
# also check services folder (where Colab tells to mv)
_ALT_MODEL = Path(__file__).parent.parent / "services" / "price_forecast.pt"
_ALT_SCALER = Path(__file__).parent.parent / "services" / "scaler.pkl"
_FORECAST_MODEL = None
_SCALER = None


def _load_forecast():
    global _FORECAST_MODEL, _SCALER
    if _FORECAST_MODEL is not None and _SCALER is not None:
        return _FORECAST_MODEL, _SCALER
    # find files in either location
    m_path = _FORECAST_MODEL_PATH if _FORECAST_MODEL_PATH.exists() else _ALT_MODEL
    s_path = _SCALER_PATH if _SCALER_PATH.exists() else _ALT_SCALER
    if not m_path.exists() or not s_path.exists():
        return None, None
    try:
        import torch
        import torch.nn as nn

        class LSTM(nn.Module):
            def __init__(self):
                super().__init__()
                self.lstm = nn.LSTM(3, 32, batch_first=True)
                self.fc = nn.Linear(32, 24)

            def forward(self, x):
                _, (h, _) = self.lstm(x)
                return self.fc(h[-1])

        _SCALER = pickle.loads(s_path.read_bytes())
        _FORECAST_MODEL = LSTM()
        _FORECAST_MODEL.load_state_dict(__import__("torch").load(str(m_path), map_location="cpu"))
        _FORECAST_MODEL.eval()
        logger.info("Loaded price_forecast.pt + scaler.pkl (%.1f KB)", m_path.stat().st_size / 1024)
    except Exception as e:
        logger.warning("Forecast model load failed (%s) — fallback to sin mock: %s", m_path, e)
        _FORECAST_MODEL, _SCALER = None, None
    return _FORECAST_MODEL, _SCALER


def _forecast_price_lstm(hour: int, dow: int) -> float | None:
    """Try LSTM 24h forecast, return price for current hour. None on any failure."""
    try:
        model, scaler = _load_forecast()
        if model is None or scaler is None:
            return None
        import numpy as np
        import torch

        # Build dummy 24h history using sin mock (or could query DB last 24)
        # history hour/dow/price for last 24
        hist = []
        now = datetime.now(timezone.utc)
        for i in range(24):
            h = (hour - 24 + i) % 24
            d = dow
            # use sin mock as history price
            base = 3.5 * (0.5 + 2.0 * max(0.0, __import__("math").sin((h - 6) * 3.14159 / 13)) if 6 <= h <= 19 else 0.5)
            price = round(base, 2)
            hist.append([price, h, d])
        scaled = scaler.transform(np.array(hist, dtype=float))
        X = torch.tensor(scaled, dtype=torch.float32).unsqueeze(0)  # [1,24,3]
        with torch.no_grad():
            pred_scaled = model(X).numpy()[0]  # 24 values
        # inverse: need price column
        dummy = np.zeros((24, 3))
        dummy[:, 0] = pred_scaled
        pred_inv = scaler.inverse_transform(dummy)[:, 0]
        # first predicted hour corresponds to 'hour'
        return float(round(pred_inv[0], 2))
    except Exception as e:
        logger.debug("LSTM forecast failed, fallback: %s", e)
        return None


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
                    # Try LSTM first (if price_forecast.pt + scaler.pkl pasted from Colab)
                    lstm_price = _forecast_price_lstm(now.hour, now.weekday())
                    if lstm_price is not None:
                        price = {
                            "price_per_kwh": lstm_price,
                            "currency": "INR",
                            "source": "lstm_forecast",
                            "market_region": "default",
                            "is_forecast": True,
                        }
                    else:
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
