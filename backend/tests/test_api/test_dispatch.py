from datetime import datetime, timezone, timedelta

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

REGISTER_PAYLOAD = {
    "organization_name": "Dispatch Corp",
    "organization_slug": "dispatch-corp",
    "email": "dispatch@test.com",
    "password": "StrongPass1!",
    "display_name": "Dispatch Admin",
}


async def setup_org(client: AsyncClient, slug: str = "dispatch-corp") -> dict:
    payload = {**REGISTER_PAYLOAD, "organization_slug": slug, "email": f"{slug}@test.com"}
    reg = await client.post("/v1/auth/register", json=payload)
    assert reg.status_code == 201
    return {"Authorization": f"Bearer {reg.json()['access_token']}"}


class TestDispatchRules:
    async def test_create_rule(self, client: AsyncClient):
        headers = await setup_org(client)
        response = await client.post("/v1/dispatch/rules", json={
            "name": "Price Spike Rule",
            "description": "Respond to price spikes",
            "priority": 100,
            "condition_type": "price_above",
            "condition_config": {"threshold": 200.0},
            "action": "charge_battery",
            "action_config": {"rate": 0.5},
            "target_asset_type": "battery_storage",
            "cooldown_minutes": 15,
        }, headers=headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Price Spike Rule"
        assert data["condition_type"] == "price_above"
        assert data["is_active"] is True

    async def test_create_rule_duplicate_name(self, client: AsyncClient):
        headers = await setup_org(client, "dup-rule")
        await client.post("/v1/dispatch/rules", json={
            "name": "Dup Rule", "condition_type": "price_above", "action": "notify_operator",
        }, headers=headers)
        response = await client.post("/v1/dispatch/rules", json={
            "name": "Dup Rule", "condition_type": "price_below", "action": "no_action",
        }, headers=headers)
        assert response.status_code == 409

    async def test_list_rules(self, client: AsyncClient):
        headers = await setup_org(client, "list-rules")
        await client.post("/v1/dispatch/rules", json={
            "name": "Rule 1", "condition_type": "price_above", "action": "notify_operator",
        }, headers=headers)
        await client.post("/v1/dispatch/rules", json={
            "name": "Rule 2", "condition_type": "curtailment_detected", "action": "curtail_generation",
        }, headers=headers)
        response = await client.get("/v1/dispatch/rules", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 2

    async def test_update_rule(self, client: AsyncClient):
        headers = await setup_org(client, "update-rule")
        create = await client.post("/v1/dispatch/rules", json={
            "name": "Update Me", "condition_type": "price_above", "action": "notify_operator",
        }, headers=headers)
        rule_id = create.json()["id"]
        response = await client.put(f"/v1/dispatch/rules/{rule_id}", json={
            "name": "Updated Rule",
            "priority": 50,
            "is_active": False,
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Rule"
        assert data["priority"] == 50
        assert data["is_active"] is False

    async def test_update_nonexistent_rule(self, client: AsyncClient):
        headers = await setup_org(client, "nonex-rule")
        response = await client.put(
            "/v1/dispatch/rules/00000000-0000-0000-0000-000000000000",
            json={"name": "Ghost"},
            headers=headers,
        )
        assert response.status_code == 404

    async def test_delete_rule(self, client: AsyncClient):
        headers = await setup_org(client, "delete-rule")
        create = await client.post("/v1/dispatch/rules", json={
            "name": "Delete Me", "condition_type": "price_above", "action": "notify_operator",
        }, headers=headers)
        rule_id = create.json()["id"]
        response = await client.delete(f"/v1/dispatch/rules/{rule_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["data"]["message"] == "Rule deleted successfully"

    async def test_delete_nonexistent_rule(self, client: AsyncClient):
        headers = await setup_org(client, "delete-nonex")
        response = await client.delete(
            "/v1/dispatch/rules/00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        assert response.status_code == 404

    async def test_rules_require_auth(self, client: AsyncClient):
        response = await client.get("/v1/dispatch/rules")
        assert response.status_code == 401

    async def test_validation_error(self, client: AsyncClient):
        headers = await setup_org(client, "validate-rule")
        response = await client.post("/v1/dispatch/rules", json={
            "name": "Bad", "condition_type": "price_above",
        }, headers=headers)
        assert response.status_code == 422


class TestDispatchDecisions:
    async def test_list_decisions_empty(self, client: AsyncClient):
        headers = await setup_org(client, "decisions-empty")
        response = await client.get("/v1/dispatch/decisions", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 0

    async def test_list_decisions_pagination(self, client: AsyncClient):
        headers = await setup_org(client, "decisions-pag")
        response = await client.get("/v1/dispatch/decisions?per_page=10", headers=headers)
        assert response.status_code == 200


class TestCurtailment:
    async def test_list_events_empty(self, client: AsyncClient):
        headers = await setup_org(client, "curtail-empty")
        response = await client.get("/v1/curtailment/events", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 0

    async def test_list_events_pagination(self, client: AsyncClient):
        headers = await setup_org(client, "curtail-pag")
        response = await client.get("/v1/curtailment/events?per_page=10", headers=headers)
        assert response.status_code == 200

    async def test_revenue_lost(self, client: AsyncClient):
        headers = await setup_org(client, "rev-lost")
        now = datetime.now(timezone.utc)
        response = await client.get(
            f"/v1/curtailment/revenue-lost?start_date={(now - timedelta(days=30)).isoformat()}",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_curtailed_kwh" in data
        assert "total_revenue_lost" in data
        assert "event_count" in data

    async def test_revenue_lost_daily_granularity(self, client: AsyncClient):
        headers = await setup_org(client, "rev-daily")
        now = datetime.now(timezone.utc)
        response = await client.get(
            f"/v1/curtailment/revenue-lost?start_date={(now - timedelta(days=30)).isoformat()}&granularity=daily",
            headers=headers,
        )
        assert response.status_code == 200

    async def test_revenue_lost_by_asset(self, client: AsyncClient):
        headers = await setup_org(client, "rev-asset")
        now = datetime.now(timezone.utc)
        response = await client.get(
            f"/v1/curtailment/revenue-lost?start_date={(now - timedelta(days=30)).isoformat()}"
            f"&asset_id=00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        assert response.status_code == 200

    async def test_curtailment_requires_auth(self, client: AsyncClient):
        response = await client.get("/v1/curtailment/events")
        assert response.status_code == 401
