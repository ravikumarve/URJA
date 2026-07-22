"""Async API client for URJA backend with mock data fallback."""

from __future__ import annotations

import random
from datetime import datetime

import httpx

from config import settings


class UrajaAPIClient:
    def __init__(self) -> None:
        self.base_url = settings.API_URL
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=5.0)
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def _fetch(self, path: str, mock_fn, **kwargs) -> dict | list:
        try:
            resp = await self.client.get(path, params=kwargs)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return mock_fn()

    async def get_latest_telemetry(self) -> dict:
        return await self._fetch("/telemetry/latest", self._mock_telemetry)

    async def get_assets(self) -> list:
        return await self._fetch("/assets", self._mock_assets)

    async def get_curtailment_events(self) -> list:
        return await self._fetch("/dispatch/curtailment", self._mock_curtailment)

    async def get_carbon_credits(self) -> list:
        return await self._fetch("/carbon/credits", self._mock_carbon, limit=10)

    async def get_health_scores(self) -> list:
        return await self._fetch("/health/scores", self._mock_health)

    async def get_alerts(self) -> list:
        return await self._fetch("/health/alerts", self._mock_alerts, status="active")

    async def get_dispatch_decisions(self) -> list:
        return await self._fetch("/dispatch/decisions", self._mock_dispatch, limit=5)

    @staticmethod
    def _mock_telemetry() -> dict:
        return {
            "current_mw": round(random.uniform(15, 22), 1),
            "wind_speed": round(random.uniform(30, 55), 1),
            "soiling_ratio": round(random.uniform(60, 85)),
            "revenue_lost": random.randint(200000, 300000),
            "temperature": round(random.uniform(38, 48)),
            "irradiance": round(random.uniform(400, 900)),
        }

    @staticmethod
    def _mock_assets() -> list:
        now = datetime.utcnow()
        return [
            {"id": "INV-01", "type": "INVERTER", "health": 98, "temp": 42, "status": "NOMINAL", "last_seen": now.isoformat()},
            {"id": "INV-02", "type": "INVERTER", "health": 62, "temp": 61, "status": "THERMAL_THROTTLE", "last_seen": now.isoformat()},
            {"id": "MET-01", "type": "ANEMOMETER", "health": 99, "temp": None, "status": "NOMINAL", "last_seen": now.isoformat()},
            {"id": "ARR-A1", "type": "PANEL_ARRAY", "health": 41, "temp": 48, "status": "HEAVY_SOILING", "last_seen": now.isoformat()},
            {"id": "INV-03", "type": "INVERTER", "health": 97, "temp": 43, "status": "NOMINAL", "last_seen": now.isoformat()},
            {"id": "INV-04", "type": "INVERTER", "health": 95, "temp": 45, "status": "NOMINAL", "last_seen": now.isoformat()},
            {"id": "INV-05", "type": "INVERTER", "health": 96, "temp": 44, "status": "NOMINAL", "last_seen": now.isoformat()},
            {"id": "INV-06", "type": "INVERTER", "health": 94, "temp": 46, "status": "NOMINAL", "last_seen": now.isoformat()},
            {"id": "INV-07", "type": "INVERTER", "health": 62, "temp": 78, "status": "OVERHEAT", "last_seen": now.isoformat()},
            {"id": "INV-08", "type": "INVERTER", "health": 97, "temp": 43, "status": "NOMINAL", "last_seen": now.isoformat()},
            {"id": "STR-01", "type": "STRING", "health": 82, "temp": None, "status": "LOW_YIELD", "last_seen": now.isoformat()},
            {"id": "STM-01", "type": "PANEL_ARRAY", "health": 99, "temp": 48, "status": "NOMINAL", "last_seen": now.isoformat()},
        ]

    @staticmethod
    def _mock_curtailment() -> list:
        return [
            {"time": "10:15-11:45", "duration": 90, "curtailed": 42.5, "price": 2.8, "revenue_lost": 119000, "severity": "critical"},
            {"time": "13:00-14:30", "duration": 90, "curtailed": 38.2, "price": 2.5, "revenue_lost": 95500, "severity": "critical"},
            {"time": "16:00-16:45", "duration": 45, "curtailed": 15.8, "price": 3.1, "revenue_lost": 48980, "severity": "warning"},
            {"time": "18:30-19:00", "duration": 30, "curtailed": 8.2, "price": 2.9, "revenue_lost": 23780, "severity": "dim"},
        ]

    @staticmethod
    def _mock_carbon() -> list:
        return [
            {"batch_id": "batch_240701", "date": "2026-07-01", "co2e": 8212.5, "credits": 8212, "status": "active"},
            {"batch_id": "batch_240702", "date": "2026-07-08", "co2e": 8150.0, "credits": 8150, "status": "active"},
            {"batch_id": "batch_240703", "date": "2026-07-15", "co2e": 8300.0, "credits": 8300, "status": "active"},
            {"batch_id": "batch_240704", "date": "2026-07-22", "co2e": 8188.0, "credits": 8188, "status": "pending"},
        ]

    @staticmethod
    def _mock_health() -> list:
        return [
            {"asset": "INV-01", "score": 98, "trend": "→", "anomalies": "None"},
            {"asset": "INV-02", "score": 97, "trend": "→", "anomalies": "None"},
            {"asset": "INV-03", "score": 99, "trend": "→", "anomalies": "None"},
            {"asset": "INV-04", "score": 95, "trend": "→", "anomalies": "None"},
            {"asset": "INV-05", "score": 96, "trend": "→", "anomalies": "None"},
            {"asset": "INV-06", "score": 94, "trend": "→", "anomalies": "None"},
            {"asset": "INV-07", "score": 62, "trend": "↓", "anomalies": "Temp 78°C (z=4.2) ⚠"},
            {"asset": "INV-08", "score": 97, "trend": "→", "anomalies": "None"},
            {"asset": "INV-09", "score": 98, "trend": "→", "anomalies": "None"},
            {"asset": "INV-10", "score": 96, "trend": "→", "anomalies": "None"},
            {"asset": "STR-01", "score": 82, "trend": "↓", "anomalies": "Power drop 18% ⚠"},
        ]

    @staticmethod
    def _mock_alerts() -> list:
        return [
            {"severity": "critical", "asset": "INV-07", "message": "Temperature anomaly (78°C) — Check fans"},
            {"severity": "warning", "asset": "ST-142", "message": "Power drop 18% below expected — Check panels"},
            {"severity": "warning", "asset": "ARR-A1", "message": "Heavy soiling detected — Schedule wash"},
            {"severity": "critical", "asset": "INV-02", "message": "Thermal throttle active — Output limited"},
        ]

    @staticmethod
    def _mock_dispatch() -> list:
        return [
            {"time": "14:30", "action": "Charged battery (12.4 MW → 78% SOC)"},
            {"time": "14:32", "action": "Curtailment resolved — grid price recovered"},
            {"time": "13:15", "action": "Issued curtailment — grid congestion"},
            {"time": "12:00", "action": "Battery discharged (45 MW → 22% SOC)"},
            {"time": "10:15", "action": "Issued curtailment — DNI dropped 56%"},
        ]
