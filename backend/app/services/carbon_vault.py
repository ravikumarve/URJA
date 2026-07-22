import hashlib
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID


EMISSION_FACTORS: dict[str, float] = {
    "US-CA": 0.28,
    "US-TX": 0.55,
    "US-NY": 0.22,
    "EU": 0.32,
    "IN": 0.92,
    "default": 0.92,
}


def calculate_avoided_emissions(
    total_mwh: Decimal,
    methodology: str = "URJA-VCS-1.0",
    region: str = "default",
) -> Decimal:
    factor = Decimal(str(EMISSION_FACTORS.get(region, EMISSION_FACTORS["default"])))
    return total_mwh * factor


def create_credit_hash(
    previous_credit: Optional[dict],
    org_id: UUID,
    sequence_num: int,
    total_mwh: Decimal,
    timestamp: datetime,
) -> str:
    prev_hash = previous_credit.get("hash", "GENESIS") if previous_credit else "GENESIS"
    raw = f"{prev_hash}|{org_id}|{sequence_num}|{total_mwh}|{timestamp.isoformat()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_mrv_pipeline(
    generation_data: list[dict],
    asset_id: UUID,
    org_id: UUID,
    emission_factor: Decimal,
    methodology: str = "IPMVP_v2.1",
) -> dict:
    if not generation_data:
        return {
            "valid": False,
            "reason": "No generation data provided",
            "total_kwh": Decimal("0"),
            "total_co2e": Decimal("0"),
            "credit_count": 0,
        }

    readings = [g for g in generation_data if g.get("quality_code", 0) <= 1]
    if not readings:
        return {
            "valid": False,
            "reason": "All readings have poor quality (quality_code > 1)",
            "total_kwh": Decimal("0"),
            "total_co2e": Decimal("0"),
            "credit_count": 0,
        }

    data_quality = len(readings) / len(generation_data)
    if data_quality < 0.8:
        return {
            "valid": False,
            "reason": f"Insufficient data quality: {data_quality:.1%} good readings (need ≥80%)",
            "total_kwh": Decimal("0"),
            "total_co2e": Decimal("0"),
            "credit_count": 0,
        }

    total_kwh = sum(
        (Decimal(str(r.get("energy_kwh", r.get("generation_kw", 0)))))
        for r in readings
    )

    total_mwh = total_kwh / Decimal("1000")
    total_co2e = total_mwh * emission_factor
    credit_count = int(total_co2e)

    return {
        "valid": True,
        "total_kwh": total_kwh,
        "total_mwh": total_mwh,
        "total_co2e": total_co2e,
        "emission_factor": emission_factor,
        "credit_count": credit_count,
        "data_quality_pct": round(data_quality * 100, 1),
        "methodology": methodology,
    }
