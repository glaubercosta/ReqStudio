"""Testes de CRUD de Projetos — Story 3.1.

Cobre: criação, listagem paginada, get por ID, atualização,
arquivamento, isolamento cross-tenant e status 404.
"""

import pytest
from httpx import AsyncClient


# ── Helpers ───────────────────────────────────────────────────────────────────

def _auth(token: dict) -> dict:
    return {"Authorization": f"Bearer {token['access_token']}"}


async def _create(client: AsyncClient, token: dict, **overrides) -> dict:
    payload = {"name": "Projeto Teste", "business_domain": "Saúde", **overrides}
    res = await client.post("/api/v1/projects", json=payload, headers=_auth(token))
    assert res.status_code == 201, res.text
    return res.json()["data"]


# ── Criação ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_project_returns_201(client: AsyncClient, tenant_a_token):
    project = await _create(client, tenant_a_token, name="Projeto Alpha")
    assert project["name"] == "Projeto Alpha"
    assert project["status"] == "active"
    assert project["tenant_id"] == tenant_a_token["tenant_id"]


@pytest.mark.asyncio
async def test_create_project_without_optional_fields(client: AsyncClient, tenant_a_token):
    project = await _create(client, tenant_a_token, name="Mínimo")
    assert project["description"] is None
    assert project["business_domain"] == "Saúde"


@pytest.mark.asyncio
async def test_create_project_requires_name(client: AsyncClient, tenant_a_token):
    res = await client.post(
        "/api/v1/projects",
        json={"description": "sem nome"},
        headers=_auth(tenant_a_token),
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_create_project_requires_auth(client: AsyncClient):
    res = await client.post("/api/v1/projects", json={"name": "Sem Auth"})
    assert res.status_code == 401


# ── Listagem e Paginação ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_projects_returns_active_by_default(client: AsyncClient, tenant_a_token):
    await _create(client, tenant_a_token, name="P1")
    await _create(client, tenant_a_token, name="P2")
    res = await client.get("/api/v1/projects", headers=_auth(tenant_a_token))
    assert res.status_code == 200
    body = res.json()["data"]
    assert body["total"] >= 2
    assert all(p["status"] == "active" for p in body["items"])


@pytest.mark.asyncio
async def test_list_projects_pagination(client: AsyncClient, tenant_a_token):
    for i in range(5):
        await _create(client, tenant_a_token, name=f"Projeto {i}")
    res = await client.get(
        "/api/v1/projects?page=1&size=3",
        headers=_auth(tenant_a_token),
    )
    assert res.status_code == 200
    body = res.json()["data"]
    assert len(body["items"]) <= 3
    assert body["pages"] >= 1


# ── Get por ID ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_project_by_id(client: AsyncClient, tenant_a_token):
    created = await _create(client, tenant_a_token, name="Get Teste")
    res = await client.get(
        f"/api/v1/projects/{created['id']}",
        headers=_auth(tenant_a_token),
    )
    assert res.status_code == 200
    assert res.json()["data"]["id"] == created["id"]


@pytest.mark.asyncio
async def test_get_nonexistent_project_returns_404(client: AsyncClient, tenant_a_token):
    res = await client.get(
        "/api/v1/projects/00000000-0000-0000-0000-000000000000",
        headers=_auth(tenant_a_token),
    )
    assert res.status_code == 404


# ── Atualização ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_project_name(client: AsyncClient, tenant_a_token):
    created = await _create(client, tenant_a_token, name="Antes")
    res = await client.patch(
        f"/api/v1/projects/{created['id']}",
        json={"name": "Depois"},
        headers=_auth(tenant_a_token),
    )
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "Depois"


@pytest.mark.asyncio
async def test_archive_project(client: AsyncClient, tenant_a_token):
    created = await _create(client, tenant_a_token, name="Para Arquivar")
    res = await client.patch(
        f"/api/v1/projects/{created['id']}",
        json={"status": "archived"},
        headers=_auth(tenant_a_token),
    )
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "archived"


@pytest.mark.asyncio
async def test_archived_project_not_in_active_list(client: AsyncClient, tenant_a_token):
    created = await _create(client, tenant_a_token, name="Vai Arquivar")
    await client.patch(
        f"/api/v1/projects/{created['id']}",
        json={"status": "archived"},
        headers=_auth(tenant_a_token),
    )
    res = await client.get("/api/v1/projects", headers=_auth(tenant_a_token))
    ids = [p["id"] for p in res.json()["data"]["items"]]
    assert created["id"] not in ids


@pytest.mark.asyncio
async def test_archived_project_in_archived_list(client: AsyncClient, tenant_a_token):
    created = await _create(client, tenant_a_token, name="Arquivado")
    await client.patch(
        f"/api/v1/projects/{created['id']}",
        json={"status": "archived"},
        headers=_auth(tenant_a_token),
    )
    res = await client.get(
        "/api/v1/projects?status=archived",
        headers=_auth(tenant_a_token),
    )
    ids = [p["id"] for p in res.json()["data"]["items"]]
    assert created["id"] in ids


@pytest.mark.asyncio
async def test_invalid_status_returns_422(client: AsyncClient, tenant_a_token):
    created = await _create(client, tenant_a_token, name="Status Inválido")
    res = await client.patch(
        f"/api/v1/projects/{created['id']}",
        json={"status": "deleted"},
        headers=_auth(tenant_a_token),
    )
    assert res.status_code == 422


# ── Isolamento Multi-Tenant (AC #5) ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_tenant_a_cannot_access_tenant_b_project(
    client: AsyncClient,
    tenant_a_token,
    tenant_b_token,
):
    """Projeto de tenant_b retorna 404 para tenant_a — nunca 403."""
    project_b = await _create(client, tenant_b_token, name="Projeto B")
    res = await client.get(
        f"/api/v1/projects/{project_b['id']}",
        headers=_auth(tenant_a_token),
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_tenant_a_cannot_update_tenant_b_project(
    client: AsyncClient,
    tenant_a_token,
    tenant_b_token,
):
    project_b = await _create(client, tenant_b_token, name="Projeto B Update")
    res = await client.patch(
        f"/api/v1/projects/{project_b['id']}",
        json={"name": "Tentativa de Invasão"},
        headers=_auth(tenant_a_token),
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_list_only_returns_own_tenant_projects(
    client: AsyncClient,
    tenant_a_token,
    tenant_b_token,
):
    await _create(client, tenant_a_token, name="Projeto A")
    await _create(client, tenant_b_token, name="Projeto B")

    res_a = await client.get("/api/v1/projects", headers=_auth(tenant_a_token))
    tid_a = tenant_a_token["tenant_id"]
    assert all(p["tenant_id"] == tid_a for p in res_a.json()["data"]["items"])

    res_b = await client.get("/api/v1/projects", headers=_auth(tenant_b_token))
    tid_b = tenant_b_token["tenant_id"]
    assert all(p["tenant_id"] == tid_b for p in res_b.json()["data"]["items"])
