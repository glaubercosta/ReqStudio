"""Testes de refresh token — Story 2.3."""

import pytest
from httpx import AsyncClient

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"

VALID_USER = {"email": "refresh@example.com", "password": "senha1234"}


@pytest.fixture(autouse=True)
async def registered_user(client: AsyncClient):
    """Cria e faz login do usuário antes de cada teste."""
    await client.post(REGISTER_URL, json=VALID_USER)


async def _login(client: AsyncClient) -> tuple[str, str]:
    """Helper: faz login e retorna (access_token, refresh_token)."""
    resp = await client.post(LOGIN_URL, json=VALID_USER)
    assert resp.status_code == 200
    access_token = resp.json()["data"]["access_token"]
    refresh_token = resp.cookies.get("refresh_token")
    assert refresh_token, "Cookie refresh_token não encontrado"
    return access_token, refresh_token


@pytest.mark.asyncio
async def test_refresh_success(client: AsyncClient):
    """AC#1+2: refresh retorna 200 com novo access_token."""
    _, refresh_token = await _login(client)

    client.cookies.set("refresh_token", refresh_token)
    response = await client.post(REFRESH_URL)

    assert response.status_code == 200
    body = response.json()
    assert "data" in body
    assert "access_token" in body["data"]


@pytest.mark.asyncio
async def test_refresh_rotation(client: AsyncClient):
    """AC#2: rotation — novo refresh_token é diferente do anterior."""
    _, old_refresh = await _login(client)

    client.cookies.set("refresh_token", old_refresh)
    resp = await client.post(REFRESH_URL)
    assert resp.status_code == 200

    new_refresh = resp.cookies.get("refresh_token")
    assert new_refresh is not None
    assert new_refresh != old_refresh  # token rotacionado


@pytest.mark.asyncio
async def test_refresh_reuse_detection(client: AsyncClient):
    """AC#3: usar token já usado → TOKEN_REUSE_DETECTED e revogação em cascata."""
    _, old_refresh = await _login(client)

    # Primeiro uso — legítimo
    client.cookies.set("refresh_token", old_refresh)
    resp1 = await client.post(REFRESH_URL)
    assert resp1.status_code == 200

    # Segundo uso do mesmo token — reuse attack!
    client.cookies.set("refresh_token", old_refresh)
    resp2 = await client.post(REFRESH_URL)
    assert resp2.status_code == 401
    assert resp2.json()["error"]["code"] == "TOKEN_REUSE_DETECTED"


@pytest.mark.asyncio
async def test_refresh_revoked_after_reuse(client: AsyncClient):
    """AC#3: após reuse detection, novo token também é inválido (revogação em cascata)."""
    _, old_refresh = await _login(client)

    # Primeiro uso legítimo → gera novo_refresh
    client.cookies.set("refresh_token", old_refresh)
    resp1 = await client.post(REFRESH_URL)
    new_refresh = resp1.cookies.get("refresh_token")

    # Reuse attack com token antigo → revoga todos
    client.cookies.set("refresh_token", old_refresh)
    await client.post(REFRESH_URL)

    # Tentar usar o novo token (que foi revogado em cascata)
    client.cookies.set("refresh_token", new_refresh)
    resp3 = await client.post(REFRESH_URL)
    assert resp3.status_code == 401  # revogado


@pytest.mark.asyncio
async def test_refresh_without_cookie(client: AsyncClient):
    """AC#4: sem cookie → SESSION_EXPIRED."""
    response = await client.post(REFRESH_URL)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "SESSION_EXPIRED"


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient):
    """AC#4: token inválido/adulterado → SESSION_EXPIRED."""
    client.cookies.set("refresh_token", "token.adulterado.invalido")
    response = await client.post(REFRESH_URL)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "SESSION_EXPIRED"
