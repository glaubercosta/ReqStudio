"""Testes do Elicitation Engine — Story 5.4.

Cobre: pipeline completo, write-ahead save, workflow progression,
crash recovery (mensagem salva antes do LLM), e isolamento cross-tenant.

LLM é mocked. DB é real (SQLite in-memory via conftest).
"""

from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.core.exceptions import GuidedRecoveryError
from app.integrations.llm_client import CompletionChunk, CompletionMetrics

# ── Helpers ───────────────────────────────────────────────────────────────────


def _auth(token: dict) -> dict:
    return {"Authorization": f"Bearer {token['access_token']}"}


async def _create_project(client: AsyncClient, token: dict) -> dict:
    payload = {"name": "Projeto Engine", "business_domain": "Finanças"}
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


async def _get_messages(client: AsyncClient, token: dict, session_id: str) -> list:
    res = await client.get(
        f"/api/v1/sessions/{session_id}/messages",
        headers=_auth(token),
    )
    assert res.status_code == 200
    return res.json()["data"]["items"]


async def _mock_llm_stream(*args, **kwargs):
    """Simula streaming de resposta do LLM."""
    chunks = ["Olá! ", "Vamos ", "começar."]
    for text in chunks:
        yield CompletionChunk(content=text, done=False)
    yield CompletionChunk(
        content="",
        done=True,
        metrics=CompletionMetrics(
            model="mock",
            input_tokens=50,
            output_tokens=15,
            total_tokens=65,
            cost_usd=0.001,
            latency_ms=200,
            success=True,
        ),
    )


# ── Pipeline Tests ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_elicit_full_pipeline(client: AsyncClient, tenant_a_token, seed_workflows):
    """Pipeline completo: user msg → context → LLM → assistant msg."""
    from app.db.session import get_db
    from app.db.tenant import TenantScope
    from app.main import app
    from app.modules.engine.elicitation import elicit

    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])

    with patch("app.modules.engine.elicitation.stream_completion", side_effect=_mock_llm_stream):
        async for db in app.dependency_overrides[get_db]():
            scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
            chunks = []
            async for chunk in elicit(scope, session["id"], "Quero criar um app de finanças"):
                chunks.append(chunk)

    # Validar chunks
    content_chunks = [c for c in chunks if not c.done]
    done_chunks = [c for c in chunks if c.done]
    assert len(content_chunks) == 3
    assert len(done_chunks) == 1
    assert done_chunks[0].metrics.cost_usd == 0.001

    # Validar mensagens salvas
    messages = await _get_messages(client, tenant_a_token, session["id"])
    assert len(messages) == 2  # user + assistant
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Quero criar um app de finanças"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Olá! Vamos começar."
    assert messages[1]["input_tokens"] == 50
    assert messages[1]["output_tokens"] == 15
    assert messages[1]["cost_usd"] == 0.001
    assert messages[1]["latency_ms"] is not None
    assert messages[1]["model"] == "mock"


@pytest.mark.asyncio
async def test_elicit_write_ahead_save(client: AsyncClient, tenant_a_token, seed_workflows):
    """Mensagem do user é salva ANTES de chamar o LLM (write-ahead)."""
    from app.db.session import get_db
    from app.db.tenant import TenantScope
    from app.main import app
    from app.modules.engine.elicitation import elicit

    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])

    saved_before_llm = False

    async def _llm_that_checks_db(*args, **kwargs):
        """Mock que verifica se a mensagem do user já foi salva."""
        nonlocal saved_before_llm
        msgs = await _get_messages(client, tenant_a_token, session["id"])
        user_msgs = [m for m in msgs if m["role"] == "user"]
        saved_before_llm = len(user_msgs) > 0

        yield CompletionChunk(content="Resposta", done=False)
        yield CompletionChunk(
            content="",
            done=True,
            metrics=CompletionMetrics(model="mock", success=True),
        )

    with patch("app.modules.engine.elicitation.stream_completion", side_effect=_llm_that_checks_db):
        async for db in app.dependency_overrides[get_db]():
            scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
            async for _ in elicit(scope, session["id"], "Teste write-ahead"):
                pass

    assert saved_before_llm is True


@pytest.mark.asyncio
async def test_elicit_session_not_found(client: AsyncClient, tenant_a_token, seed_workflows):
    """Sessão inexistente → 404."""
    from app.db.session import get_db
    from app.db.tenant import TenantScope
    from app.main import app
    from app.modules.engine.elicitation import elicit

    async for db in app.dependency_overrides[get_db]():
        scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
        with pytest.raises(GuidedRecoveryError) as exc_info:
            async for _ in elicit(scope, "sessao-404", "msg"):
                pass
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_elicit_cross_tenant_isolation(
    client: AsyncClient,
    tenant_a_token,
    tenant_b_token,
    seed_workflows,
):
    """Sessão de outro tenant → 404."""
    from app.db.session import get_db
    from app.db.tenant import TenantScope
    from app.main import app
    from app.modules.engine.elicitation import elicit

    project_a = await _create_project(client, tenant_a_token)
    session_a = await _create_session(client, tenant_a_token, project_a["id"])

    async for db in app.dependency_overrides[get_db]():
        scope_b = TenantScope(db=db, tenant_id=tenant_b_token["tenant_id"])
        with pytest.raises(GuidedRecoveryError) as exc_info:
            async for _ in elicit(scope_b, session_a["id"], "Intruso!"):
                pass
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_elicit_workflow_progression(client: AsyncClient, tenant_a_token, seed_workflows):
    """Cada ciclo de elicitação avança o workflow_position."""
    from app.db.session import get_db
    from app.db.tenant import TenantScope
    from app.main import app
    from app.modules.engine.elicitation import elicit

    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])

    with patch("app.modules.engine.elicitation.stream_completion", side_effect=_mock_llm_stream):
        async for db in app.dependency_overrides[get_db]():
            scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
            # Primeiro ciclo
            async for _ in elicit(scope, session["id"], "Ciclo 1"):
                pass

    # Verificar que o workflow avançou
    res = await client.get(
        f"/api/v1/sessions/{session['id']}",
        headers=_auth(tenant_a_token),
    )
    data = res.json()["data"]
    # Com 1 step no seed, após 1 ciclo deve ter completed
    assert data["workflow_position"] is not None
    assert data["workflow_position"].get("completed") is True
    assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_elicit_message_index_sequence(client: AsyncClient, tenant_a_token, seed_workflows):
    """Múltiplos ciclos mantêm message_index correto."""
    from app.db.session import get_db
    from app.db.tenant import TenantScope
    from app.main import app
    from app.modules.engine.elicitation import elicit

    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])

    with patch("app.modules.engine.elicitation.stream_completion", side_effect=_mock_llm_stream):
        async for db in app.dependency_overrides[get_db]():
            scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
            async for _ in elicit(scope, session["id"], "Msg 1"):
                pass

    messages = await _get_messages(client, tenant_a_token, session["id"])
    assert messages[0]["message_index"] == 0  # user
    assert messages[1]["message_index"] == 1  # assistant
