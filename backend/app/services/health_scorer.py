import logging
import math
import pickle
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)

# Colab-trained IsolationForest — burst-trained on 432K rows, inference-only on Latitude
_MODEL_PATH = Path(__file__).with_name("health_model.pkl")
_META_PATH = Path(__file__).with_name("health_meta.json")
_MODEL = None  # lazy-loaded Pipeline[StandardScaler, IsolationForest]
_MODEL_FEATURES = ["health_score", "temperature_c", "generation_kw", "vibration", "soiling_ratio"]
_MODEL_THRESHOLD = 0.0  # decision_function <0 => anomaly
_SCORES_MIN = -0.3
_SCORES_MAX = 0.25


def _get_model():
    global _MODEL, _MODEL_FEATURES, _MODEL_THRESHOLD, _SCORES_MIN, _SCORES_MAX
    if _MODEL is not None:
        return _MODEL
    try:
        if _MODEL_PATH.exists():
            _MODEL = pickle.loads(_MODEL_PATH.read_bytes())
            # try to load meta for threshold/features if user copied it
            if _META_PATH.exists():
                import json

                meta = json.loads(_META_PATH.read_text())
                _MODEL_FEATURES = meta.get("features", _MODEL_FEATURES)
                _MODEL_THRESHOLD = float(meta.get("threshold", _MODEL_THRESHOLD))
            # try to infer min/max from training scores if available (optional)
            logger.info("Loaded health_model.pkl (%d KB)", _MODEL_PATH.stat().st_size // 1024)
        else:
            logger.debug("health_model.pkl not found at %s — using 3-sigma fallback", _MODEL_PATH)
    except Exception as e:
        logger.warning("Failed to load health_model.pkl (%s) — fallback to 3-sigma: %s", _MODEL_PATH, e)
        _MODEL = None
    return _MODEL


def _model_health_adjustment(telemetry: dict, base_health: float) -> tuple[float, str | None]:
    """If model exists, run inference on 5D feature vector. Returns (adjusted_health, flag)."""
    m = _get_model()
    if m is None:
        return base_health, None
    try:
        # Build 5D vector — impute missing telemetry with farm-typical defaults
        # telemetry comes from DB row: generation_kw, temperature_c, voltage_v, etc.
        # vibration/soiling not in DB — default to healthy baseline
        health = float(telemetry.get("health_score", base_health))
        temp = float(telemetry.get("temperature_c", 44)) if telemetry.get("temperature_c") is not None else 44.0
        gen = float(telemetry.get("generation_kw", 3200))
        vib = float(telemetry.get("vibration", 0.5)) if telemetry.get("vibration") is not None else 0.5
        soil = float(telemetry.get("soiling_ratio", 68)) if telemetry.get("soiling_ratio") is not None else 68.0
        # Model was fit on DataFrame with names — pass numpy array to avoid feature-name check
        import numpy as np

        X = np.array([[health, temp, gen, vib, soil]], dtype=float)
        score = float(m.decision_function(X)[0])  # higher = healthier
        pred = int(m.predict(X)[0])  # 1 healthy, -1 anomaly
        # Map score to 0-100 like notebook: ((score - min)/(max-min)*100)
        # Use fixed min/max from training distribution (approx -0.3 to 0.25)
        health_ml = ((score - _SCORES_MIN) / (_SCORES_MAX - _SCORES_MIN) * 100.0)
        health_ml = max(0.0, min(100.0, health_ml))
        # Blend: if model says anomaly, pull health down; else trust ML a bit
        if pred == -1:
            # anomaly — weighted blend toward ML, but don't hide rule-based
            adjusted = (base_health * 0.4) + (health_ml * 0.6)
            # also penalize a bit for clear anomaly
            adjusted = max(0.0, adjusted - 8.0)
            return round(adjusted, 2), f"ml_anomaly_{score:.3f}"
        else:
            # healthy — gentle blend
            adjusted = (base_health * 0.7) + (health_ml * 0.3)
            return round(max(0.0, min(100.0, adjusted)), 2), None
    except Exception as e:
        logger.debug("Model inference failed, fallback: %s", e)
        return base_health, None


def calculate_health_score(
    asset_id: UUID,
    telemetry_data: list[dict],
    expected_capacity_kw: float = 1.0,
) -> dict:
    if not telemetry_data:
        return {
            "health_score": 100.0,
            "anomaly_score": 0.0,
            "trend": "stable",
            "metric_scores": {},
            "anomaly_flags": [],
        }

    recent = telemetry_data[-1] if telemetry_data else {}
    generation_kw = float(recent.get("generation_kw", 0))
    temperature_c = recent.get("temperature_c")
    voltage_v = recent.get("voltage_v")

    if expected_capacity_kw <= 0:
        expected_capacity_kw = 1

    power_ratio = generation_kw / expected_capacity_kw
    power_score = min(100.0, (power_ratio / 1.0) * 100.0)

    temp_score = 100.0
    if temperature_c is not None:
        temp_float = float(temperature_c)
        if temp_float > 45:
            temp_score = max(0, 100.0 - (temp_float - 45) * 5)
        elif temp_float > 35:
            temp_score = max(60, 100.0 - (temp_float - 35) * 2)

    voltage_score = 100.0
    if voltage_v is not None:
        v = float(voltage_v)
        nominal = 480.0
        deviation = abs(v - nominal) / nominal
        voltage_score = max(0, 100.0 - deviation * 200)

    metric_scores = {
        "power_kw": round(power_score, 1),
    }
    if temperature_c is not None:
        metric_scores["temperature_c"] = round(temp_score, 1)
    if voltage_v is not None:
        metric_scores["voltage_v"] = round(voltage_score, 1)

    health_score = (power_score * 0.5) + (temp_score * 0.3) + (voltage_score * 0.2)
    health_score = max(0.0, min(100.0, health_score))

    # Colab model augmentation — if health_model.pkl pasted, blend ML score
    ml_flag = None
    try:
        # Use recent telemetry dict for model (needs health_score, temp, gen, vibration, soiling)
        recent_ml = dict(recent)
        recent_ml["health_score"] = health_score
        # soiling_ratio may be in telemetry as "soiling_ratio" or default
        health_score, ml_flag = _model_health_adjustment(recent_ml, health_score)
    except Exception:
        pass

    anomaly_flags = []
    anomaly_score = 0.0
    if ml_flag:
        anomaly_flags.append(ml_flag)
        anomaly_score += 0.15
    if power_ratio < 0.5:
        anomaly_flags.append("power_drop_alert")
        anomaly_score += 0.1
    if temperature_c is not None and float(temperature_c) > 50:
        anomaly_flags.append("temp_spike")
        anomaly_score += 0.08
    if voltage_v is not None and abs(float(voltage_v) - 480) > 48:
        anomaly_flags.append("voltage_deviation")
        anomaly_score += 0.05

    anomaly_score = min(1.0, anomaly_score)

    if len(telemetry_data) >= 4:
        recent_values = [
            float(d.get("generation_kw", 0)) for d in telemetry_data[-4:]
        ]
        trend = _determine_trend(recent_values)
    else:
        trend = "stable"

    return {
        "health_score": round(health_score, 2),
        "anomaly_score": round(anomaly_score, 6),
        "trend": trend,
        "metric_scores": metric_scores,
        "anomaly_flags": anomaly_flags,
    }


def detect_anomalies(
    asset_id: UUID,
    recent_data: list[dict],
    historical_baseline: Optional[dict] = None,
    threshold_sigma: float = 3.0,
) -> list[dict]:
    anomalies = []

    if not recent_data:
        return anomalies

    for reading in recent_data:
        for metric in ["generation_kw", "temperature_c", "voltage_v"]:
            value = reading.get(metric)
            if value is None:
                continue

            val = float(value)

            mean = None
            std = None
            if historical_baseline and metric in historical_baseline:
                mean = float(historical_baseline[metric].get("mean", 0))
                std = float(historical_baseline[metric].get("std", 1))
            else:
                all_values = [
                    float(d.get(metric, 0))
                    for d in recent_data
                    if d.get(metric) is not None
                ]
                if len(all_values) > 1:
                    mean = sum(all_values) / len(all_values)
                    variance = sum((x - mean) ** 2 for x in all_values) / len(all_values)
                    std = math.sqrt(variance)

            if mean is not None and std is not None and std > 0:
                z_score = (val - mean) / std
                if abs(z_score) > threshold_sigma:
                    anomalies.append({
                        "ts": reading.get("ts"),
                        "metric": metric,
                        "observed_value": val,
                        "expected_value": round(mean, 4),
                        "z_score": round(z_score, 4),
                        "anomaly_score": min(1.0, abs(z_score) / 10.0),
                        "method": "z_score",
                    })

    return anomalies


def update_health_scores(db, org_id: UUID) -> int:
    return 0


def _determine_trend(values: list[float]) -> str:
    if len(values) < 2:
        return "stable"

    deltas = [values[i] - values[i - 1] for i in range(1, len(values))]
    avg_delta = sum(deltas) / len(deltas)

    if avg_delta > 0.05 * max(abs(v) for v in values if v != 0):
        return "improving"
    elif avg_delta < -0.05 * max(abs(v) for v in values if v != 0):
        return "declining"
    return "stable"
