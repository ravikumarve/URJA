import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


REGISTER_PAYLOAD = {
    "organization_name": "Test Org",
    "organization_slug": "test-org",
    "email": "admin@test.com",
    "password": "StrongPass1!",
    "display_name": "Admin User",
    "timezone": "UTC",
    "currency": "USD",
}


async def register_user(client: AsyncClient, payload: dict | None = None) -> dict:
    if payload is None:
        payload = REGISTER_PAYLOAD
    response = await client.post("/v1/auth/register", json=payload)
    assert response.status_code == 201
    return response.json()


async def get_auth_headers(client: AsyncClient) -> dict:
    data = await register_user(client)
    return {"Authorization": f"Bearer {data['access_token']}"}


class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        data = await register_user(client)
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "admin@test.com"
        assert data["user"]["role"] == "admin"
        assert data["organization"]["slug"] == "test-org"

    async def test_register_duplicate_email(self, client: AsyncClient):
        await register_user(client)
        dup = {**REGISTER_PAYLOAD, "organization_slug": "other-org"}
        response = await client.post("/v1/auth/register", json=dup)
        assert response.status_code == 409
        assert "Email already registered" in response.json()["detail"]

    async def test_register_duplicate_slug(self, client: AsyncClient):
        await register_user(client)
        dup = {**REGISTER_PAYLOAD, "email": "other@test.com"}
        response = await client.post("/v1/auth/register", json=dup)
        assert response.status_code == 409
        assert "Organization slug already exists" in response.json()["detail"]

    async def test_register_missing_fields(self, client: AsyncClient):
        response = await client.post("/v1/auth/register", json={"email": "bad@test.com"})
        assert response.status_code == 422


class TestLogin:
    async def test_login_success(self, client: AsyncClient):
        await register_user(client)
        response = await client.post("/v1/auth/login", json={
            "email": "admin@test.com",
            "password": "StrongPass1!",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "admin@test.com"

    async def test_login_wrong_password(self, client: AsyncClient):
        await register_user(client)
        response = await client.post("/v1/auth/login", json={
            "email": "admin@test.com",
            "password": "wrongpass",
        })
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        response = await client.post("/v1/auth/login", json={
            "email": "ghost@test.com",
            "password": "anything",
        })
        assert response.status_code == 401

    async def test_login_missing_fields(self, client: AsyncClient):
        response = await client.post("/v1/auth/login", json={})
        assert response.status_code == 422


class TestRefresh:
    async def test_refresh_success(self, client: AsyncClient):
        reg = await register_user(client)
        response = await client.post("/v1/auth/refresh", json={
            "refresh_token": reg["refresh_token"],
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_invalid_token(self, client: AsyncClient):
        response = await client.post("/v1/auth/refresh", json={
            "refresh_token": "not-a-real-token",
        })
        assert response.status_code == 401

    async def test_refresh_empty_token(self, client: AsyncClient):
        response = await client.post("/v1/auth/refresh", json={"refresh_token": ""})
        assert response.status_code == 401


class TestLogout:
    async def test_logout_success(self, client: AsyncClient):
        reg = await register_user(client)
        response = await client.post("/v1/auth/logout", json={
            "refresh_token": reg["refresh_token"],
        })
        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully"

    async def test_logout_twice(self, client: AsyncClient):
        reg = await register_user(client)
        await client.post("/v1/auth/logout", json={"refresh_token": reg["refresh_token"]})
        response = await client.post("/v1/auth/logout", json={
            "refresh_token": reg["refresh_token"],
        })
        assert response.status_code == 200

    async def test_logout_missing_body(self, client: AsyncClient):
        response = await client.post("/v1/auth/logout", json={})
        assert response.status_code == 422


class TestMe:
    async def test_get_me_authenticated(self, client: AsyncClient):
        headers = await get_auth_headers(client)
        response = await client.get("/v1/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@test.com"
        assert data["display_name"] == "Admin User"
        assert data["role"] == "admin"
        assert data["is_active"] is True

    async def test_get_me_no_token(self, client: AsyncClient):
        response = await client.get("/v1/auth/me")
        assert response.status_code == 401

    async def test_get_me_bad_token(self, client: AsyncClient):
        response = await client.get("/v1/auth/me", headers={"Authorization": "Bearer badtoken"})
        assert response.status_code == 401


class TestApiKeys:
    async def test_create_api_key(self, client: AsyncClient):
        headers = await get_auth_headers(client)
        response = await client.post("/v1/auth/api-keys", json={
            "name": "test-key",
            "scope": "read",
        }, headers=headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test-key"
        assert data["key_prefix"] == data["full_key"][:12]
        assert data["is_active"] is True

    async def test_create_api_key_duplicate_name(self, client: AsyncClient):
        headers = await get_auth_headers(client)
        await client.post("/v1/auth/api-keys", json={"name": "dup-key", "scope": "read"}, headers=headers)
        response = await client.post("/v1/auth/api-keys", json={"name": "dup-key", "scope": "write"}, headers=headers)
        assert response.status_code == 409

    async def test_list_api_keys(self, client: AsyncClient):
        headers = await get_auth_headers(client)
        await client.post("/v1/auth/api-keys", json={"name": "key1", "scope": "read"}, headers=headers)
        await client.post("/v1/auth/api-keys", json={"name": "key2", "scope": "write"}, headers=headers)
        response = await client.get("/v1/auth/api-keys", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    async def test_revoke_api_key(self, client: AsyncClient):
        headers = await get_auth_headers(client)
        create_resp = await client.post("/v1/auth/api-keys", json={"name": "revoke-me", "scope": "read"}, headers=headers)
        key_id = create_resp.json()["id"]
        response = await client.delete(f"/v1/auth/api-keys/{key_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["message"] == "API key revoked successfully"

    async def test_revoke_nonexistent_key(self, client: AsyncClient):
        headers = await get_auth_headers(client)
        response = await client.delete("/v1/auth/api-keys/00000000-0000-0000-0000-000000000000", headers=headers)
        assert response.status_code == 404

    async def test_api_keys_require_auth(self, client: AsyncClient):
        response = await client.get("/v1/auth/api-keys")
        assert response.status_code == 401


class TestUsers:
    async def test_list_users(self, client: AsyncClient):
        headers = await get_auth_headers(client)
        response = await client.get("/v1/auth/users", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    async def test_list_users_pagination(self, client: AsyncClient):
        headers = await get_auth_headers(client)
        response = await client.get("/v1/auth/users?page=1&page_size=5", headers=headers)
        assert response.status_code == 200

    async def test_invite_user(self, client: AsyncClient):
        headers = await get_auth_headers(client)
        response = await client.post("/v1/auth/users/invite", json={
            "email": "invited@test.com",
            "display_name": "Invited User",
            "role": "viewer",
        }, headers=headers)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "invited@test.com"
        assert data["role"] == "viewer"

    async def test_invite_duplicate_email(self, client: AsyncClient):
        headers = await get_auth_headers(client)
        await client.post("/v1/auth/users/invite", json={
            "email": "dup@test.com", "display_name": "Dup", "role": "viewer",
        }, headers=headers)
        response = await client.post("/v1/auth/users/invite", json={
            "email": "dup@test.com", "display_name": "Dup Again", "role": "operator",
        }, headers=headers)
        assert response.status_code == 409

    async def test_change_user_role(self, client: AsyncClient):
        headers = await get_auth_headers(client)
        invite_resp = await client.post("/v1/auth/users/invite", json={
            "email": "change-role@test.com", "display_name": "Role Change", "role": "viewer",
        }, headers=headers)
        user_id = invite_resp.json()["id"]
        response = await client.put(f"/v1/auth/users/{user_id}/role", json={
            "role": "operator",
        }, headers=headers)
        assert response.status_code == 200
        assert response.json()["role"] == "operator"

    async def test_change_own_role_forbidden(self, client: AsyncClient):
        headers = await get_auth_headers(client)
        me = await client.get("/v1/auth/me", headers=headers)
        my_id = me.json()["id"]
        response = await client.put(f"/v1/auth/users/{my_id}/role", json={
            "role": "viewer",
        }, headers=headers)
        assert response.status_code == 403

    async def test_change_nonexistent_user_role(self, client: AsyncClient):
        headers = await get_auth_headers(client)
        response = await client.put("/v1/auth/users/00000000-0000-0000-0000-000000000000/role", json={
            "role": "viewer",
        }, headers=headers)
        assert response.status_code == 404

    async def test_list_users_filter_by_role(self, client: AsyncClient):
        headers = await get_auth_headers(client)
        response = await client.get("/v1/auth/users?role=admin", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert all(u["role"] == "admin" for u in data["items"])
