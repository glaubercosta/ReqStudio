"""Testes de login e JWT — Story 2.2."""

import pytest
from httpx import AsyncClient
from jose import jwt

from app.core.config import settings

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"

VALID_USER = {"email": "login@example.com", "password": "senha1234"}


@pytest.fixture(autouse=True)
async def registered_user(client: AsyncClient):
    """Cria o usuário antes de cada teste de login."""
    await client.post(REGISTER_URL, json=VALID_USER)


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """AC#1: login retorna 200 com access_token no corpo."""
    response = await client.post(LOGIN_URL, json=VALID_USER)
    assert response.status_code == 200
    body = response.json()
    assert "data" in body
    assert "access_token" in body["data"]
    assert body["data"]["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_sets_refresh_cookie(client: AsyncClient):
    """AC#2: login define refresh_token como cookie httpOnly."""
    response = await client.post(LOGIN_URL, json=VALID_USER)
    assert response.status_code == 200
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_access_token_claims(client: AsyncClient):
    """AC#3: access_token tem claims user_id, tenant_id, exp, iat."""
    response = await client.post(LOGIN_URL, json=VALID_USER)
    token = response.json()["data"]["access_token"]

    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    assert "sub" in payload       # user_id
    assert "tenant_id" in payload
    assert "exp" in payload
    assert "iat" in payload
    assert payload["type"] == "access"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """AC#4: senha errada → Guided Recovery INVALID_CREDENTIALS."""
    response = await client.post(
        LOGIN_URL,
        json={"email": VALID_USER["email"], "password": "senhaerrada"},
    )
    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "INVALID_CREDENTIALS"
    assert "help" in body["error"]
    assert "actions" in body["error"]


@pytest.mark.asyncio
async def test_login_unknown_email(client: AsyncClient):
    """AC#4: email inexistente → Guided Recovery INVALID_CREDENTIALS (sem revelar se existe)."""
    response = await client.post(
        LOGIN_URL,
        json={"email": "naoexiste@example.com", "password": "senha1234"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_get_tenant_id_dependency(client: AsyncClient):
    """AC#5: endpoint protegido retorna 401 sem token."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_authenticated_endpoint(client: AsyncClient):
    """AC#5: get_current_user dependency funciona com token válido."""
    login_resp = await client.post(LOGIN_URL, json=VALID_USER)
    token = login_resp.json()["data"]["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["email"] == VALID_USER["email"]
