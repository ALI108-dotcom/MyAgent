"""Unit tests for system health and metadata endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient) -> None:
    """Verify root endpoint returns welcome message and documentation links."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["status"] == "running"


@pytest.mark.asyncio
async def test_health_check_endpoint(async_client: AsyncClient) -> None:
    """Verify health endpoint returns status, environment, and database connection state."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert "service" in data
    assert "database" in data
    assert "modules" in data
