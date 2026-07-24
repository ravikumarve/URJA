from datetime import datetime, timezone, timedelta

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

REGISTER_PAYLOAD = {
    "organization_name": "Health Corp",
    "organization_slug": "health-corp",
    "email": "health@test.com",
    "password": "StrongPass1!",
    "display_name": "Health Admin",
}


async def setup_asset(client: AsyncClient) -> tuple[dict, dict]:
    reg = await client.post("/v1/auth/register", json=REGISTER_PAYLOAD)
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    site = await client.post("/v1/sites", json={
        "name": "Health Site", "code": "hlth-site", "capacity_mw": 5.0,
    }, headers=headers)
    asset = await client.post("/v1/assets", json={
        "site_id": site.json()["id"], "asset_type": "solar_panel",
        "name": "Health Panel", "code": "HLTH-001",
    }, headers=headers)
    return headers, asset.json()


class TestHealthScores:
    async def test_list_scores_empty(self, client: AsyncClient):
        headers, _ = await setup_asset(client)
        response = await client.get("/v1/health/scores", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 0

    async def test_list_scores_with_asset_filter(self, client: AsyncClient):
        headers, asset = await setup_asset(client)
        response = await client.get(f"/v1/health/scores?asset_id={asset['id']}", headers=headers)
        assert response.status_code == 200

    async def test_scores_require_auth(self, client: AsyncClient):
        response = await client.get("/v1/health/scores")
        assert response.status_code == 401


class TestAlerts:
    async def test_list_alerts_empty(self, client: AsyncClient):
        headers, _ = await setup_asset(client)
        response = await client.get("/v1/health/alerts", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 0

    async def test_list_alerts_pagination(self, client: AsyncClient):
        headers, _ = await setup_asset(client)
        response = await client.get("/v1/health/alerts?per_page=10", headers=headers)
        assert response.status_code == 200
        assert "pagination" in response.json()

    async def test_acknowledge_alert_not_found(self, client: AsyncClient):
        headers, _ = await setup_asset(client)
        response = await client.put(
            "/v1/health/alerts/00000000-0000-0000-0000-000000000000/acknowledge",
            headers=headers,
        )
        assert response.status_code == 404

    async def test_alerts_require_auth(self, client: AsyncClient):
        response = await client.get("/v1/health/alerts")
        assert response.status_code == 401


class TestAnomalies:
    async def test_list_anomalies_empty(self, client: AsyncClient):
        headers, _ = await setup_asset(client)
        response = await client.get("/v1/health/anomalies", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 0

    async def test_list_anomalies_pagination(self, client: AsyncClient):
        headers, _ = await setup_asset(client)
        response = await client.get("/v1/health/anomalies?per_page=10", headers=headers)
        assert response.status_code == 200

    async def test_anomalies_require_auth(self, client: AsyncClient):
        response = await client.get("/v1/health/anomalies")
        assert response.status_code == 401


class TestWorkOrders:
    async def test_create_work_order(self, client: AsyncClient):
        headers, asset = await setup_asset(client)
        now = datetime.now(timezone.utc)
        response = await client.post("/v1/maintenance/work-orders", json={
            "asset_id": asset["id"],
            "title": "Replace Inverter",
            "description": "Inverter showing error codes",
            "priority": "high",
            "scheduled_start": now.isoformat(),
            "scheduled_end": (now + timedelta(days=1)).isoformat(),
            "estimated_cost": 1500.00,
        }, headers=headers)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Replace Inverter"
        assert data["priority"] == "high"
        assert data["status"] == "scheduled"
        assert data["asset_name"] == "Health Panel"

    async def test_create_work_order_nonexistent_asset(self, client: AsyncClient):
        headers, _ = await setup_asset(client)
        now = datetime.now(timezone.utc)
        response = await client.post("/v1/maintenance/work-orders", json={
            "asset_id": "00000000-0000-0000-0000-000000000000",
            "title": "Ghost",
            "scheduled_start": now.isoformat(),
            "scheduled_end": (now + timedelta(hours=1)).isoformat(),
        }, headers=headers)
        assert response.status_code == 404

    async def test_list_work_orders(self, client: AsyncClient):
        headers, asset = await setup_asset(client)
        now = datetime.now(timezone.utc)
        await client.post("/v1/maintenance/work-orders", json={
            "asset_id": asset["id"], "title": "WO-1",
            "scheduled_start": now.isoformat(),
            "scheduled_end": (now + timedelta(hours=1)).isoformat(),
        }, headers=headers)
        await client.post("/v1/maintenance/work-orders", json={
            "asset_id": asset["id"], "title": "WO-2",
            "scheduled_start": now.isoformat(),
            "scheduled_end": (now + timedelta(hours=2)).isoformat(),
        }, headers=headers)
        response = await client.get("/v1/maintenance/work-orders", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 2

    async def test_list_work_orders_pagination(self, client: AsyncClient):
        headers, _ = await setup_asset(client)
        response = await client.get("/v1/maintenance/work-orders?per_page=10", headers=headers)
        assert response.status_code == 200

    async def test_update_work_order(self, client: AsyncClient):
        headers, asset = await setup_asset(client)
        now = datetime.now(timezone.utc)
        create = await client.post("/v1/maintenance/work-orders", json={
            "asset_id": asset["id"], "title": "Update Me",
            "scheduled_start": now.isoformat(),
            "scheduled_end": (now + timedelta(hours=1)).isoformat(),
        }, headers=headers)
        wo_id = create.json()["id"]
        response = await client.put(f"/v1/maintenance/work-orders/{wo_id}", json={
            "status": "in_progress",
            "priority": "critical",
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["priority"] == "critical"

    async def test_update_nonexistent_work_order(self, client: AsyncClient):
        headers, _ = await setup_asset(client)
        response = await client.put(
            "/v1/maintenance/work-orders/00000000-0000-0000-0000-000000000000",
            json={"status": "completed"},
            headers=headers,
        )
        assert response.status_code == 404

    async def test_work_orders_require_auth(self, client: AsyncClient):
        response = await client.get("/v1/maintenance/work-orders")
        assert response.status_code == 401

    async def test_create_work_order_validation_error(self, client: AsyncClient):
        headers, _ = await setup_asset(client)
        response = await client.post("/v1/maintenance/work-orders", json={
            "title": "Incomplete",
        }, headers=headers)
        assert response.status_code == 422

    async def test_work_order_requires_admin(self, client: AsyncClient):
        reg = await client.post("/v1/auth/register", json={
            "organization_name": "ViewerOrg",
            "organization_slug": "viewer-org-hlth",
            "email": "viewer-hlth@test.com",
            "password": "StrongPass1!",
            "display_name": "Viewer",
        })
        headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}
        now = datetime.now(timezone.utc)
        response = await client.post("/v1/maintenance/work-orders", json={
            "asset_id": "00000000-0000-0000-0000-000000000000",
            "title": "No Perm",
            "scheduled_start": now.isoformat(),
            "scheduled_end": (now + timedelta(hours=1)).isoformat(),
        }, headers=headers)
        assert response.status_code == 403
