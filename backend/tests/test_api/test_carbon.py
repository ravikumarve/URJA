from datetime import datetime, timezone, timedelta

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

REGISTER_PAYLOAD = {
    "organization_name": "Carbon Corp",
    "organization_slug": "carbon-corp",
    "email": "carbon@test.com",
    "password": "StrongPass1!",
    "display_name": "Carbon Admin",
}


async def setup_asset_with_telemetry(client: AsyncClient) -> tuple[dict, dict]:
    reg = await client.post("/v1/auth/register", json=REGISTER_PAYLOAD)
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    site = await client.post("/v1/sites", json={
        "name": "Carbon Site", "code": "carb-site", "capacity_mw": 10.0,
    }, headers=headers)
    asset = await client.post("/v1/assets", json={
        "site_id": site.json()["id"], "asset_type": "solar_panel",
        "name": "Carbon Panel", "code": "CRB-001",
    }, headers=headers)
    asset_id = asset.json()["id"]

    now = datetime.now(timezone.utc)
    telemetry = [
        {
            "asset_id": asset_id,
            "ts": (now - timedelta(hours=i)).isoformat(),
            "generation_kw": 400.0,
            "energy_kwh": 100.0,
        }
        for i in range(24)
    ]
    await client.post("/v1/telemetry", json={"records": telemetry}, headers=headers)
    return headers, asset.json()


class TestCarbonCredits:
    async def test_list_credits_empty(self, client: AsyncClient):
        headers = await setup_asset_with_telemetry(client)
        response = await client.get("/v1/carbon/credits", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 0

    async def test_list_credits_pagination(self, client: AsyncClient):
        headers, _ = await setup_asset_with_telemetry(client)
        response = await client.get("/v1/carbon/credits?per_page=10", headers=headers)
        assert response.status_code == 200
        assert "pagination" in response.json()

    async def test_get_credit_not_found(self, client: AsyncClient):
        headers, _ = await setup_asset_with_telemetry(client)
        response = await client.get(
            "/v1/carbon/credits/00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        assert response.status_code == 404

    async def test_list_with_filters(self, client: AsyncClient):
        headers, _ = await setup_asset_with_telemetry(client)
        response = await client.get("/v1/carbon/credits?status=active", headers=headers)
        assert response.status_code == 200

    async def test_credits_require_auth(self, client: AsyncClient):
        response = await client.get("/v1/carbon/credits")
        assert response.status_code == 401


class TestCarbonIssue:
    async def test_issue_credits(self, client: AsyncClient):
        headers, asset = await setup_asset_with_telemetry(client)
        now = datetime.now(timezone.utc)
        response = await client.post("/v1/carbon/issue", json={
            "asset_id": asset["id"],
            "generation_start": (now - timedelta(hours=24)).isoformat(),
            "generation_end": now.isoformat(),
            "methodology": "IPMVP_v2.1",
            "notes": "Test issuance",
        }, headers=headers)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "active"
        assert data["credit_count"] >= 1
        assert len(data["credit_ids"]) >= 1
        assert data["total_kwh"] > 0

    async def test_issue_duplicate(self, client: AsyncClient):
        headers, asset = await setup_asset_with_telemetry(client)
        now = datetime.now(timezone.utc)
        payload = {
            "asset_id": asset["id"],
            "generation_start": (now - timedelta(hours=12)).isoformat(),
            "generation_end": now.isoformat(),
        }
        await client.post("/v1/carbon/issue", json=payload, headers=headers)
        response = await client.post("/v1/carbon/issue", json=payload, headers=headers)
        assert response.status_code == 409

    async def test_issue_nonexistent_asset(self, client: AsyncClient):
        headers, _ = await setup_asset_with_telemetry(client)
        now = datetime.now(timezone.utc)
        response = await client.post("/v1/carbon/issue", json={
            "asset_id": "00000000-0000-0000-0000-000000000000",
            "generation_start": (now - timedelta(hours=1)).isoformat(),
            "generation_end": now.isoformat(),
        }, headers=headers)
        assert response.status_code == 404

    async def test_issue_range_too_large(self, client: AsyncClient):
        headers, asset = await setup_asset_with_telemetry(client)
        now = datetime.now(timezone.utc)
        response = await client.post("/v1/carbon/issue", json={
            "asset_id": asset["id"],
            "generation_start": (now - timedelta(days=400)).isoformat(),
            "generation_end": now.isoformat(),
        }, headers=headers)
        assert response.status_code == 400

    async def test_issue_no_telemetry(self, client: AsyncClient):
        headers, asset = await setup_asset_with_telemetry(client)
        now = datetime.now(timezone.utc)
        response = await client.post("/v1/carbon/issue", json={
            "asset_id": asset["id"],
            "generation_start": (now + timedelta(days=1)).isoformat(),
            "generation_end": (now + timedelta(days=2)).isoformat(),
        }, headers=headers)
        assert response.status_code == 400

    async def test_issue_requires_admin(self, client: AsyncClient):
        reg = await client.post("/v1/auth/register", json={
            "organization_name": "NonAdmin",
            "organization_slug": "non-admin",
            "email": "viewer@test.com",
            "password": "StrongPass1!",
            "display_name": "Viewer User",
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        now = datetime.now(timezone.utc)
        response = await client.post("/v1/carbon/issue", json={
            "asset_id": "00000000-0000-0000-0000-000000000000",
            "generation_start": (now - timedelta(hours=1)).isoformat(),
            "generation_end": now.isoformat(),
        }, headers=headers)
        assert response.status_code == 403


class TestPortfolio:
    async def test_portfolio_empty(self, client: AsyncClient):
        headers, _ = await setup_asset_with_telemetry(client)
        response = await client.get("/v1/carbon/portfolio", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_issued"] == 0
        assert data["total_available"] == 0

    async def test_portfolio_after_issuance(self, client: AsyncClient):
        headers, asset = await setup_asset_with_telemetry(client)
        now = datetime.now(timezone.utc)
        await client.post("/v1/carbon/issue", json={
            "asset_id": asset["id"],
            "generation_start": (now - timedelta(hours=24)).isoformat(),
            "generation_end": now.isoformat(),
        }, headers=headers)
        response = await client.get("/v1/carbon/portfolio", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_issued"] >= 1
        assert data["total_available"] >= 1
        assert data["by_status"]["active"] >= 1

    async def test_portfolio_requires_auth(self, client: AsyncClient):
        response = await client.get("/v1/carbon/portfolio")
        assert response.status_code == 401
