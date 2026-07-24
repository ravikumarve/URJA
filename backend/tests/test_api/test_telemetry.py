from datetime import datetime, timezone, timedelta

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

REGISTER_PAYLOAD = {
    "organization_name": "Telemetry Corp",
    "organization_slug": "telemetry-corp",
    "email": "telemetry@test.com",
    "password": "StrongPass1!",
    "display_name": "Telemetry Admin",
}


async def setup_asset(client: AsyncClient) -> tuple[dict, dict]:
    reg = await client.post("/v1/auth/register", json=REGISTER_PAYLOAD)
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    site = await client.post("/v1/sites", json={
        "name": "Telemetry Site", "code": "tlm-site",
        "capacity_mw": 5.0,
    }, headers=headers)
    asset = await client.post("/v1/assets", json={
        "site_id": site.json()["id"], "asset_type": "solar_panel",
        "name": "TLM-Panel", "code": "TLM-001",
    }, headers=headers)
    return headers, asset.json()


class TestTelemetryIngest:
    async def test_ingest_single_record(self, client: AsyncClient):
        headers, asset = await setup_asset(client)
        now = datetime.now(timezone.utc)
        response = await client.post("/v1/telemetry", json={
            "asset_id": asset["id"],
            "ts": now.isoformat(),
            "generation_kw": 450.0,
            "energy_kwh": 100.0,
            "power_factor": 0.95,
            "temperature_c": 35.2,
        }, headers=headers)
        assert response.status_code == 202
        data = response.json()
        assert data["records_accepted"] == 1
        assert data["records_rejected"] == 0
        assert data["status"] == "completed"

    async def test_ingest_batch(self, client: AsyncClient):
        headers, asset = await setup_asset(client)
        now = datetime.now(timezone.utc)
        records = [
            {
                "asset_id": asset["id"],
                "ts": (now - timedelta(minutes=i)).isoformat(),
                "generation_kw": 400.0 + i * 10,
                "energy_kwh": 90.0 + i,
            }
            for i in range(3)
        ]
        response = await client.post("/v1/telemetry", json={"records": records}, headers=headers)
        assert response.status_code == 202
        data = response.json()
        assert data["records_accepted"] == 3

    async def test_ingest_batch_too_large(self, client: AsyncClient):
        headers, asset = await setup_asset(client)
        now = datetime.now(timezone.utc)
        records = [
            {
                "asset_id": asset["id"],
                "ts": now.isoformat(),
                "generation_kw": 400.0,
            }
            for _ in range(1001)
        ]
        response = await client.post("/v1/telemetry", json={"records": records}, headers=headers)
        assert response.status_code == 413

    async def test_ingest_bad_asset_id(self, client: AsyncClient):
        headers, _ = await setup_asset(client)
        now = datetime.now(timezone.utc)
        response = await client.post("/v1/telemetry", json={
            "asset_id": "00000000-0000-0000-0000-000000000000",
            "ts": now.isoformat(),
            "generation_kw": 450.0,
        }, headers=headers)
        assert response.status_code == 202
        data = response.json()
        assert data["records_accepted"] == 1

    async def test_ingest_requires_auth(self, client: AsyncClient):
        response = await client.post("/v1/telemetry", json={
            "asset_id": "00000000-0000-0000-0000-000000000000",
            "ts": datetime.now(timezone.utc).isoformat(),
            "generation_kw": 100.0,
        })
        assert response.status_code == 401

    async def test_ingest_validation_error(self, client: AsyncClient):
        headers, _ = await setup_asset(client)
        response = await client.post("/v1/telemetry", json={
            "asset_id": "bad-uuid",
            "ts": "invalid-date",
            "generation_kw": "not-a-number",
        }, headers=headers)
        assert response.status_code == 422


class TestTelemetryQuery:
    async def seed_telemetry(self, client: AsyncClient, headers: dict, asset_id: str, count: int = 5):
        now = datetime.now(timezone.utc)
        records = [
            {
                "asset_id": asset_id,
                "ts": (now - timedelta(hours=i)).isoformat(),
                "generation_kw": float(300 + i * 20),
                "energy_kwh": float(70 + i * 5),
            }
            for i in range(count)
        ]
        await client.post("/v1/telemetry", json={"records": records}, headers=headers)

    async def test_query_raw(self, client: AsyncClient):
        headers, asset = await setup_asset(client)
        await self.seed_telemetry(client, headers, asset["id"])
        now = datetime.now(timezone.utc)
        response = await client.get(
            f"/v1/telemetry?asset_id={asset['id']}&start_date={(now - timedelta(days=1)).isoformat()}&aggregation=raw",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 1

    async def test_query_hourly(self, client: AsyncClient):
        headers, asset = await setup_asset(client)
        await self.seed_telemetry(client, headers, asset["id"])
        now = datetime.now(timezone.utc)
        response = await client.get(
            f"/v1/telemetry?asset_id={asset['id']}&start_date={(now - timedelta(days=1)).isoformat()}&aggregation=hourly",
            headers=headers,
        )
        assert response.status_code == 200

    async def test_query_daily(self, client: AsyncClient):
        headers, asset = await setup_asset(client)
        await self.seed_telemetry(client, headers, asset["id"])
        now = datetime.now(timezone.utc)
        response = await client.get(
            f"/v1/telemetry?asset_id={asset['id']}&start_date={(now - timedelta(days=1)).isoformat()}&aggregation=daily",
            headers=headers,
        )
        assert response.status_code in (200, 422)

    async def test_query_bad_aggregation(self, client: AsyncClient):
        headers, asset = await setup_asset(client)
        now = datetime.now(timezone.utc)
        response = await client.get(
            f"/v1/telemetry?asset_id={asset['id']}&start_date={(now - timedelta(days=1)).isoformat()}&aggregation=invalid",
            headers=headers,
        )
        assert response.status_code == 422

    async def test_query_start_after_end(self, client: AsyncClient):
        headers, asset = await setup_asset(client)
        now = datetime.now(timezone.utc)
        response = await client.get(
            f"/v1/telemetry?asset_id={asset['id']}&start_date={(now + timedelta(days=1)).isoformat()}&end_date={now.isoformat()}",
            headers=headers,
        )
        assert response.status_code == 400

    async def test_query_requires_auth(self, client: AsyncClient):
        response = await client.get(
            "/v1/telemetry?asset_id=00000000-0000-0000-0000-000000000000&start_date=2024-01-01T00:00:00Z"
        )
        assert response.status_code == 401

    async def test_query_empty_result(self, client: AsyncClient):
        headers, _ = await setup_asset(client)
        now = datetime.now(timezone.utc)
        response = await client.get(
            f"/v1/telemetry?asset_id=00000000-0000-0000-0000-000000000001&start_date={(now - timedelta(hours=1)).isoformat()}",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 0


class TestTelemetryLatest:
    async def test_latest_all(self, client: AsyncClient):
        headers, asset = await setup_asset(client)
        now = datetime.now(timezone.utc)
        await client.post("/v1/telemetry", json={
            "asset_id": asset["id"], "ts": now.isoformat(), "generation_kw": 500.0,
        }, headers=headers)
        response = await client.get("/v1/telemetry/latest", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 1

    async def test_latest_by_asset(self, client: AsyncClient):
        headers, asset = await setup_asset(client)
        now = datetime.now(timezone.utc)
        await client.post("/v1/telemetry", json={
            "asset_id": asset["id"], "ts": now.isoformat(), "generation_kw": 500.0,
        }, headers=headers)
        response = await client.get(f"/v1/telemetry/latest?asset_id={asset['id']}", headers=headers)
        assert response.status_code == 200

    async def test_latest_by_site(self, client: AsyncClient):
        headers, asset = await setup_asset(client)
        now = datetime.now(timezone.utc)
        await client.post("/v1/telemetry", json={
            "asset_id": asset["id"], "ts": now.isoformat(), "generation_kw": 500.0,
        }, headers=headers)
        site_resp = await client.get("/v1/sites", headers=headers)
        site_id = site_resp.json()["items"][0]["id"]
        response = await client.get(f"/v1/telemetry/latest?site_id={site_id}", headers=headers)
        assert response.status_code == 200

    async def test_latest_empty(self, client: AsyncClient):
        headers, _ = await setup_asset(client)
        response = await client.get("/v1/telemetry/latest", headers=headers)
        assert response.status_code == 200
        assert len(response.json()["data"]) == 0
