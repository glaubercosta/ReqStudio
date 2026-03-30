"""Testes dos middlewares — Story 1.4 AC#1 e AC#2."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_request_id_added_to_response(client: AsyncClient):
    """AC#1: RequestIdMiddleware adiciona X-Request-ID na response."""
    response = await client.get("/health")
    assert "x-request-id" in response.headers
    request_id = response.headers["x-request-id"]
    assert len(request_id) == 36  # UUID4 format


@pytest.mark.asyncio
async def test_request_id_preserved_if_sent(client: AsyncClient):
    """AC#1: Se cliente enviar X-Request-ID, o mesmo valor é ecoado."""
    custom_id = "my-custom-trace-id-123"
    response = await client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.headers["x-request-id"] == custom_id


@pytest.mark.asyncio
async def test_each_request_gets_unique_id(client: AsyncClient):
    """AC#1: Requests diferentes recebem IDs diferentes."""
    r1 = await client.get("/health")
    r2 = await client.get("/health")
    assert r1.headers["x-request-id"] != r2.headers["x-request-id"]


@pytest.mark.asyncio
async def test_health_skips_tenant_middleware(client: AsyncClient):
    """AC#2: Rota /health não requer tenant_id (está em SKIP_PATHS)."""
    response = await client.get("/health")
    assert response.status_code == 200
