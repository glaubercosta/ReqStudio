"""Testes de registro de usuário — Story 2.1."""

import pytest
from httpx import AsyncClient


REGISTER_URL = "/api/v1/auth/register"


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """AC#1 + AC#2: registro retorna 201 com user e tenant_id."""
    response = await client.post(
        REGISTER_URL,
        json={"email": "ana@example.com", "password": "senha1234"},
    )
    assert response.status_code == 201
    body = response.json()
    assert "data" in body
    assert body["data"]["email"] == "ana@example.com"
    assert "id" in body["data"]
    assert "tenant_id" in body["data"]
    assert body["data"]["tenant_id"]  # não vazio — tenant criado


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """AC#3: e-mail duplicado retorna Guided Recovery EMAIL_ALREADY_EXISTS."""
    payload = {"email": "dup@example.com", "password": "senha1234"}
    await client.post(REGISTER_URL, json=payload)  # primeiro registro

    response = await client.post(REGISTER_URL, json=payload)  # duplicado
    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "EMAIL_ALREADY_EXISTS"
    assert "help" in body["error"]
    assert "actions" in body["error"]


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    """AC#4: senha <8 chars retorna Guided Recovery WEAK_PASSWORD."""
    response = await client.post(
        REGISTER_URL,
        json={"email": "fraco@example.com", "password": "1234"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "WEAK_PASSWORD"


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    """Validação Pydantic: email inválido retorna erro estruturado."""
    response = await client.post(
        REGISTER_URL,
        json={"email": "nao-eh-email", "password": "senha1234"},
    )
    assert response.status_code == 422
    body = response.json()
    assert "error" in body


@pytest.mark.asyncio
async def test_register_tenant_isolation(client: AsyncClient):
    """AC#5: dois usuários diferentes recebem tenant_ids distintos."""
    r1 = await client.post(
        REGISTER_URL,
        json={"email": "user1@example.com", "password": "senha1234"},
    )
    r2 = await client.post(
        REGISTER_URL,
        json={"email": "user2@example.com", "password": "senha1234"},
    )
    assert r1.status_code == 201
    assert r2.status_code == 201
    tenant1 = r1.json()["data"]["tenant_id"]
    tenant2 = r2.json()["data"]["tenant_id"]
    assert tenant1 != tenant2  # isolamento garantido
