"""Testes de CRUD de Sessões e Mensagens — Story 5.1.

Cobre: criação, listagem paginada, get por ID, atualização,
mensagens com message_index, isolamento cross-tenant, seed data e 404.

Padrão: client compartilhado, auth via headers=_auth(token).
Referência: test_projects.py (Read-Before-Write, Lição 11).
"""

import pytest
from httpx import AsyncClient

# ── Helpers ───────────────────────────────────────────────────────────────────


def _auth(token: dict) -> dict:
    return {"Authorization": f"Bearer {token['access_token']}"}


async def _create_project(client: AsyncClient, token: dict, **overrides) -> dict:
    payload = {"name": "Projeto Sessão", "business_domain": "Educação", **overrides}
    res = await client.post("/api/v1/projects", json=payload, headers=_auth(token))
    assert res.status_code == 201, res.text
    return res.json()["data"]


async def _create_session(client: AsyncClient, token: dict, project_id: str) -> dict:
    res = await client.post(
        f"/api/v1/projects/{project_id}/sessions",
        json={},
        headers=_auth(token),
    )
    assert res.status_code == 201, res.text
    return res.json()["data"]


async def _send_message(client: AsyncClient, token: dict, session_id: str, content: str) -> dict:
    res = await client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"content": content},
        headers=_auth(token),
    )
    assert res.status_code == 201, res.text
    return res.json()["data"]


# ── Criação de Sessão ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_session_returns_201(client: AsyncClient, tenant_a_token, seed_workflows):
    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])
    assert session["project_id"] == project["id"]
    assert session["status"] == "active"
    assert session["tenant_id"] == tenant_a_token["tenant_id"]
    assert session["workflow_id"] == seed_workflows  # default briefing


@pytest.mark.asyncio
async def test_create_session_with_project_of_another_tenant_returns_404(
    client: AsyncClient,
    tenant_a_token,
    tenant_b_token,
    seed_workflows,
):
    project_a = await _create_project(client, tenant_a_token)
    res = await client.post(
        f"/api/v1/projects/{project_a['id']}/sessions",
        json={},
        headers=_auth(tenant_b_token),
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_create_session_with_nonexistent_project_returns_404(
    client: AsyncClient,
    tenant_a_token,
    seed_workflows,
):
    res = await client.post(
        "/api/v1/projects/inexistente-id/sessions",
        json={},
        headers=_auth(tenant_a_token),
    )
    assert res.status_code == 404


# ── Listagem de Sessões ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_sessions_returns_only_tenant_sessions(
    client: AsyncClient,
    tenant_a_token,
    tenant_b_token,
    seed_workflows,
):
    project_a = await _create_project(client, tenant_a_token)
    await _create_session(client, tenant_a_token, project_a["id"])
    await _create_session(client, tenant_a_token, project_a["id"])

    # Tenant A vê 2
    res_a = await client.get(
        f"/api/v1/projects/{project_a['id']}/sessions",
        headers=_auth(tenant_a_token),
    )
    assert res_a.status_code == 200
    data_a = res_a.json()["data"]
    assert data_a["total"] == 2
    assert len(data_a["items"]) == 2

    # Tenant B vê 0 (projeto de A)
    res_b = await client.get(
        f"/api/v1/projects/{project_a['id']}/sessions",
        headers=_auth(tenant_b_token),
    )
    assert res_b.status_code == 200
    assert res_b.json()["data"]["total"] == 0


# ── Detalhe da Sessão ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_session_returns_200(client: AsyncClient, tenant_a_token, seed_workflows):
    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])

    res = await client.get(
        f"/api/v1/sessions/{session['id']}",
        headers=_auth(tenant_a_token),
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["id"] == session["id"]
    assert data["message_count"] == 0


@pytest.mark.asyncio
async def test_get_session_of_another_tenant_returns_404(
    client: AsyncClient,
    tenant_a_token,
    tenant_b_token,
    seed_workflows,
):
    project_a = await _create_project(client, tenant_a_token)
    session_a = await _create_session(client, tenant_a_token, project_a["id"])

    res = await client.get(
        f"/api/v1/sessions/{session_a['id']}",
        headers=_auth(tenant_b_token),
    )
    assert res.status_code == 404


# ── Atualização de Sessão ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_session_status_to_paused(client: AsyncClient, tenant_a_token, seed_workflows):
    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])

    res = await client.patch(
        f"/api/v1/sessions/{session['id']}",
        json={"status": "paused"},
        headers=_auth(tenant_a_token),
    )
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "paused"


# ── Mensagens ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_message_returns_201(client: AsyncClient, tenant_a_token, seed_workflows):
    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])
    msg = await _send_message(client, tenant_a_token, session["id"], "Olá IA!")

    assert msg["role"] == "user"
    assert msg["content"] == "Olá IA!"
    assert msg["message_index"] == 0
    assert msg["tenant_id"] == tenant_a_token["tenant_id"]


@pytest.mark.asyncio
async def test_add_message_to_session_of_another_tenant_returns_404(
    client: AsyncClient,
    tenant_a_token,
    tenant_b_token,
    seed_workflows,
):
    project_a = await _create_project(client, tenant_a_token)
    session_a = await _create_session(client, tenant_a_token, project_a["id"])

    res = await client.post(
        f"/api/v1/sessions/{session_a['id']}/messages",
        json={"content": "Intruso!"},
        headers=_auth(tenant_b_token),
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_message_index_increments(client: AsyncClient, tenant_a_token, seed_workflows):
    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])

    msg0 = await _send_message(client, tenant_a_token, session["id"], "Primeira")
    msg1 = await _send_message(client, tenant_a_token, session["id"], "Segunda")
    msg2 = await _send_message(client, tenant_a_token, session["id"], "Terceira")

    assert msg0["message_index"] == 0
    assert msg1["message_index"] == 1
    assert msg2["message_index"] == 2


@pytest.mark.asyncio
async def test_list_messages_paginated(client: AsyncClient, tenant_a_token, seed_workflows):
    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])

    for i in range(5):
        await _send_message(client, tenant_a_token, session["id"], f"Msg {i}")

    res = await client.get(
        f"/api/v1/sessions/{session['id']}/messages?page=1&size=2",
        headers=_auth(tenant_a_token),
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["pages"] == 3


@pytest.mark.asyncio
async def test_list_messages_of_session_from_another_tenant_returns_404(
    client: AsyncClient,
    tenant_a_token,
    tenant_b_token,
    seed_workflows,
):
    project_a = await _create_project(client, tenant_a_token)
    session_a = await _create_session(client, tenant_a_token, project_a["id"])

    res = await client.get(
        f"/api/v1/sessions/{session_a['id']}/messages",
        headers=_auth(tenant_b_token),
    )
    assert res.status_code == 404


# ── Seed Data ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_session_created_with_default_workflow(
    client: AsyncClient, tenant_a_token, seed_workflows
):
    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])
    assert session["workflow_id"] == seed_workflows


@pytest.mark.asyncio
async def test_session_get_includes_message_count(
    client: AsyncClient, tenant_a_token, seed_workflows
):
    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])
    await _send_message(client, tenant_a_token, session["id"], "Msg 1")
    await _send_message(client, tenant_a_token, session["id"], "Msg 2")

    res = await client.get(
        f"/api/v1/sessions/{session['id']}",
        headers=_auth(tenant_a_token),
    )
    assert res.json()["data"]["message_count"] == 2
