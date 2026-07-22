import math
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID


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

    anomaly_flags = []
    anomaly_score = 0.0
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
