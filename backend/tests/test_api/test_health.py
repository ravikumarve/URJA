import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "URJA"


@pytest.mark.asyncio
async def test_v1_prefix_exists(client: AsyncClient):
    response = await client.get("/v1/health/scores")
    assert response.status_code in (200, 401, 422)


@pytest.mark.asyncio
async def test_openapi_schema(client: AsyncClient):
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "URJA"
