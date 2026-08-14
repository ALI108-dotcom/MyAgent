"""Pytest fixtures for API testing."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an AsyncClient instance bound to the FastAPI application."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver"
    ) as client:
        yield client


@pytest.fixture
async def auth_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an AsyncClient authenticated as standard user."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver"
    ) as client:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "user", "password": "UserPass123!"},
        )
        token = resp.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"
        yield client


@pytest.fixture
async def admin_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an AsyncClient authenticated as admin user."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver"
    ) as client:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "AdminPass123!"},
        )
        token = resp.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"
        yield client
