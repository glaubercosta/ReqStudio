"""Tests for health endpoint — Story 1.1 AC#1."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_ok(client: AsyncClient):
    """GET /health returns 200 with status ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_response_structure(client: AsyncClient):
    """GET /health response has exactly the expected shape."""
    response = await client.get("/health")
    data = response.json()
    assert "status" in data
    assert len(data) == 1
    assert data["status"] == "ok"
