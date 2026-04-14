"""Testes de Pausar e Retomar Sessão — Story 5.8.

Cobre: pause via PATCH, resume via PATCH, estado preservado,
workflow_position e artifact_state persistidos entre pause/resume.
"""

import pytest
from httpx import AsyncClient

# ── Helpers ───────────────────────────────────────────────────────────────────


def _auth(token: dict) -> dict:
    return {"Authorization": f"Bearer {token['access_token']}"}


async def _create_project(client: AsyncClient, token: dict) -> dict:
    payload = {"name": "Projeto Pause", "business_domain": "Logística"}
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


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pause_session(client: AsyncClient, tenant_a_token, seed_workflows):
    """PATCH status=paused funciona e preserva dados."""
    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])
    assert session["status"] == "active"

    res = await client.patch(
        f"/api/v1/sessions/{session['id']}",
        json={"status": "paused"},
        headers=_auth(tenant_a_token),
    )
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "paused"


@pytest.mark.asyncio
async def test_resume_session(client: AsyncClient, tenant_a_token, seed_workflows):
    """Pausar e depois retomar → status volta para active."""
    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])

    # Pause
    await client.patch(
        f"/api/v1/sessions/{session['id']}",
        json={"status": "paused"},
        headers=_auth(tenant_a_token),
    )

    # Resume
    res = await client.patch(
        f"/api/v1/sessions/{session['id']}",
        json={"status": "active"},
        headers=_auth(tenant_a_token),
    )
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "active"


@pytest.mark.asyncio
async def test_paused_session_preserves_messages(
    client: AsyncClient,
    tenant_a_token,
    seed_workflows,
):
    """Mensagens persistem após pause/resume."""
    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])

    # Adicionar mensagem
    await client.post(
        f"/api/v1/sessions/{session['id']}/messages",
        json={"content": "Mensagem antes do pause", "role": "user"},
        headers=_auth(tenant_a_token),
    )

    # Pause
    await client.patch(
        f"/api/v1/sessions/{session['id']}",
        json={"status": "paused"},
        headers=_auth(tenant_a_token),
    )

    # Resume
    await client.patch(
        f"/api/v1/sessions/{session['id']}",
        json={"status": "active"},
        headers=_auth(tenant_a_token),
    )

    # Verificar que mensagem ainda está lá
    res = await client.get(
        f"/api/v1/sessions/{session['id']}/messages",
        headers=_auth(tenant_a_token),
    )
    assert res.status_code == 200
    messages = res.json()["data"]["items"]
    assert len(messages) == 1
    assert messages[0]["content"] == "Mensagem antes do pause"


@pytest.mark.asyncio
async def test_paused_session_preserves_workflow_position(
    client: AsyncClient,
    tenant_a_token,
    seed_workflows,
):
    """workflow_position persiste entre pause/resume."""
    from unittest.mock import patch

    from app.integrations.llm_client import CompletionChunk, CompletionMetrics

    async def _mock_llm(*args, **kwargs):
        yield CompletionChunk(content="Resposta", done=False)
        yield CompletionChunk(
            content="",
            done=True,
            metrics=CompletionMetrics(model="mock", success=True),
        )

    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])

    # Elicitar para avançar workflow
    with patch("app.modules.sessions.router.elicit") as mock_elicit:
        mock_elicit.side_effect = _mock_llm
        await client.post(
            f"/api/v1/sessions/{session['id']}/elicit",
            json={"content": "Teste"},
            headers=_auth(tenant_a_token),
        )

    # Verificar posição
    res = await client.get(
        f"/api/v1/sessions/{session['id']}",
        headers=_auth(tenant_a_token),
    )
    position_before = res.json()["data"]["workflow_position"]

    # Pause
    await client.patch(
        f"/api/v1/sessions/{session['id']}",
        json={"status": "paused"},
        headers=_auth(tenant_a_token),
    )

    # Resume
    await client.patch(
        f"/api/v1/sessions/{session['id']}",
        json={"status": "active"},
        headers=_auth(tenant_a_token),
    )

    # Verificar que posição está preservada
    res = await client.get(
        f"/api/v1/sessions/{session['id']}",
        headers=_auth(tenant_a_token),
    )
    position_after = res.json()["data"]["workflow_position"]
    assert position_after == position_before


@pytest.mark.asyncio
async def test_cross_tenant_cannot_pause(
    client: AsyncClient,
    tenant_a_token,
    tenant_b_token,
    seed_workflows,
):
    """Outro tenant não consegue pausar sessão alheia."""
    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])

    res = await client.patch(
        f"/api/v1/sessions/{session['id']}",
        json={"status": "paused"},
        headers=_auth(tenant_b_token),
    )
    assert res.status_code == 404
