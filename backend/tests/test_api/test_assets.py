import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


REGISTER_PAYLOAD = {
    "organization_name": "Asset Test Corp",
    "organization_slug": "asset-test-corp",
    "email": "assets@test.com",
    "password": "StrongPass1!",
    "display_name": "Asset Manager",
}


async def register_org(client: AsyncClient, slug: str = "asset-test-corp") -> dict:
    payload = {**REGISTER_PAYLOAD, "organization_slug": slug, "email": f"{slug}@test.com"}
    response = await client.post("/v1/auth/register", json=payload)
    assert response.status_code == 201
    return response.json()


async def get_headers(client: AsyncClient, slug: str = "asset-test-corp") -> dict:
    data = await register_org(client, slug)
    return {"Authorization": f"Bearer {data['access_token']}"}


async def create_site(client: AsyncClient, headers: dict, code: str = "site-001") -> dict:
    response = await client.post("/v1/sites", json={
        "name": "Test Solar Farm",
        "code": code,
        "description": "A test site",
        "capacity_mw": 10.0,
        "timezone": "UTC",
    }, headers=headers)
    assert response.status_code == 201
    return response.json()


class TestSites:
    async def test_create_site(self, client: AsyncClient):
        headers = await get_headers(client)
        site = await create_site(client, headers)
        assert site["name"] == "Test Solar Farm"
        assert site["code"] == "site-001"
        assert site["capacity_mw"] == 10.0
        assert site["asset_count"] == 0

    async def test_create_site_duplicate_code(self, client: AsyncClient):
        headers = await get_headers(client)
        await create_site(client, headers, "dup-site")
        response = await client.post("/v1/sites", json={
            "name": "Duplicate",
            "code": "dup-site",
            "capacity_mw": 5.0,
        }, headers=headers)
        assert response.status_code == 409

    async def test_list_sites(self, client: AsyncClient):
        headers = await get_headers(client)
        await create_site(client, headers, "list-site-1")
        await create_site(client, headers, "list-site-2")
        response = await client.get("/v1/sites", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        assert len(data["items"]) >= 2

    async def test_list_sites_pagination(self, client: AsyncClient):
        headers = await get_headers(client)
        await create_site(client, headers, "pag-site")
        response = await client.get("/v1/sites?page=1&page_size=5", headers=headers)
        assert response.status_code == 200

    async def test_get_site(self, client: AsyncClient):
        headers = await get_headers(client)
        site = await create_site(client, headers, "get-site")
        response = await client.get(f"/v1/sites/{site['id']}", headers=headers)
        assert response.status_code == 200
        assert response.json()["id"] == site["id"]

    async def test_get_site_not_found(self, client: AsyncClient):
        headers = await get_headers(client)
        response = await client.get("/v1/sites/00000000-0000-0000-0000-000000000000", headers=headers)
        assert response.status_code == 404

    async def test_sites_require_auth(self, client: AsyncClient):
        response = await client.get("/v1/sites")
        assert response.status_code == 401

    async def test_create_site_validation_error(self, client: AsyncClient):
        headers = await get_headers(client)
        response = await client.post("/v1/sites", json={"name": "Bad"}, headers=headers)
        assert response.status_code == 422


class TestAssets:
    async def test_create_asset(self, client: AsyncClient):
        headers = await get_headers(client)
        site = await create_site(client, headers, "asset-site-1")
        response = await client.post("/v1/assets", json={
            "site_id": site["id"],
            "asset_type": "solar_panel",
            "name": "Panel-001",
            "code": "PNL-001",
            "capacity_kw": 500.0,
            "manufacturer": "TestCorp",
        }, headers=headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Panel-001"
        assert data["code"] == "PNL-001"
        assert data["asset_type"] == "solar_panel"

    async def test_create_asset_nonexistent_site(self, client: AsyncClient):
        headers = await get_headers(client)
        response = await client.post("/v1/assets", json={
            "site_id": "00000000-0000-0000-0000-000000000000",
            "asset_type": "solar_panel",
            "name": "Ghost",
            "code": "GHOST-001",
        }, headers=headers)
        assert response.status_code == 404

    async def test_create_asset_duplicate_code(self, client: AsyncClient):
        headers = await get_headers(client)
        site = await create_site(client, headers, "dup-asset-site")
        await client.post("/v1/assets", json={
            "site_id": site["id"], "asset_type": "solar_panel",
            "name": "Original", "code": "DUP-CODE",
        }, headers=headers)
        response = await client.post("/v1/assets", json={
            "site_id": site["id"], "asset_type": "inverter",
            "name": "Duplicate", "code": "DUP-CODE",
        }, headers=headers)
        assert response.status_code == 409

    async def test_list_assets(self, client: AsyncClient):
        headers = await get_headers(client)
        site = await create_site(client, headers, "list-asset-site")
        await client.post("/v1/assets", json={
            "site_id": site["id"], "asset_type": "solar_panel",
            "name": "A1", "code": "LA-001",
        }, headers=headers)
        await client.post("/v1/assets", json={
            "site_id": site["id"], "asset_type": "inverter",
            "name": "A2", "code": "LA-002",
        }, headers=headers)
        response = await client.get("/v1/assets", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2

    async def test_list_assets_filter_by_type(self, client: AsyncClient):
        headers = await get_headers(client)
        site = await create_site(client, headers, "filter-asset-site")
        await client.post("/v1/assets", json={
            "site_id": site["id"], "asset_type": "solar_panel",
            "name": "SP", "code": "FLT-SP",
        }, headers=headers)
        await client.post("/v1/assets", json={
            "site_id": site["id"], "asset_type": "battery_storage",
            "name": "BT", "code": "FLT-BT",
        }, headers=headers)
        response = await client.get("/v1/assets?asset_type=solar_panel", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert all(a["asset_type"] == "solar_panel" for a in data["items"])

    async def test_get_asset_detail(self, client: AsyncClient):
        headers = await get_headers(client)
        site = await create_site(client, headers, "detail-asset-site")
        create_resp = await client.post("/v1/assets", json={
            "site_id": site["id"], "asset_type": "solar_panel",
            "name": "Detail-Panel", "code": "DTL-001",
        }, headers=headers)
        asset_id = create_resp.json()["id"]
        response = await client.get(f"/v1/assets/{asset_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == asset_id
        assert data["site"]["name"] == "Test Solar Farm"

    async def test_get_asset_not_found(self, client: AsyncClient):
        headers = await get_headers(client)
        response = await client.get("/v1/assets/00000000-0000-0000-0000-000000000000", headers=headers)
        assert response.status_code == 404

    async def test_update_asset(self, client: AsyncClient):
        headers = await get_headers(client)
        site = await create_site(client, headers, "update-asset-site")
        create_resp = await client.post("/v1/assets", json={
            "site_id": site["id"], "asset_type": "solar_panel",
            "name": "Old Name", "code": "UPD-001",
        }, headers=headers)
        asset_id = create_resp.json()["id"]
        response = await client.put(f"/v1/assets/{asset_id}", json={
            "name": "New Name",
            "capacity_kw": 600.0,
        }, headers=headers)
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    async def test_update_asset_not_found(self, client: AsyncClient):
        headers = await get_headers(client)
        response = await client.put("/v1/assets/00000000-0000-0000-0000-000000000000", json={
            "name": "Ghost",
        }, headers=headers)
        assert response.status_code == 404

    async def test_update_asset_duplicate_code(self, client: AsyncClient):
        headers = await get_headers(client)
        site = await create_site(client, headers, "dup-code-site")
        await client.post("/v1/assets", json={
            "site_id": site["id"], "asset_type": "solar_panel",
            "name": "Existing", "code": "EXIST",
        }, headers=headers)
        create2 = await client.post("/v1/assets", json={
            "site_id": site["id"], "asset_type": "inverter",
            "name": "Target", "code": "TARGET",
        }, headers=headers)
        asset2_id = create2.json()["id"]
        response = await client.put(f"/v1/assets/{asset2_id}", json={
            "code": "EXIST",
        }, headers=headers)
        assert response.status_code == 409

    async def test_decommission_asset(self, client: AsyncClient):
        headers = await get_headers(client)
        site = await create_site(client, headers, "decom-site")
        create_resp = await client.post("/v1/assets", json={
            "site_id": site["id"], "asset_type": "solar_panel",
            "name": "Retire Me", "code": "RET-001",
        }, headers=headers)
        asset_id = create_resp.json()["id"]
        response = await client.delete(f"/v1/assets/{asset_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "retired"
        assert data["asset_id"] == asset_id

    async def test_decommission_asset_not_found(self, client: AsyncClient):
        headers = await get_headers(client)
        response = await client.delete("/v1/assets/00000000-0000-0000-0000-000000000000", headers=headers)
        assert response.status_code == 404

    async def test_assets_require_auth(self, client: AsyncClient):
        response = await client.get("/v1/assets")
        assert response.status_code == 401

    async def test_create_asset_validation_error(self, client: AsyncClient):
        headers = await get_headers(client)
        response = await client.post("/v1/assets", json={"name": "Incomplete"}, headers=headers)
        assert response.status_code == 422

    async def test_create_asset_with_parent(self, client: AsyncClient):
        headers = await get_headers(client)
        site = await create_site(client, headers, "parent-site")
        parent = await client.post("/v1/assets", json={
            "site_id": site["id"], "asset_type": "inverter",
            "name": "Parent Inv", "code": "PARENT-INV",
        }, headers=headers)
        parent_id = parent.json()["id"]
        child = await client.post("/v1/assets", json={
            "site_id": site["id"], "asset_type": "solar_panel",
            "name": "Child Panel", "code": "CHILD-PNL",
            "parent_asset_id": parent_id,
        }, headers=headers)
        assert child.status_code == 201
        detail = await client.get(f"/v1/assets/{child.json()['id']}", headers=headers)
        assert detail.json()["parent_asset"]["id"] == parent_id
