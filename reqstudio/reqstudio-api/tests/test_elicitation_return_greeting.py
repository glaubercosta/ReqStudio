"""Testes do return_greeting engine e endpoint SSE (Story 7.3).

Cobre:
  - return_greeting() em sessão pausada com step_summaries → persiste msg, status=active
  - return_greeting() em sessão pausada sem summaries → greeting simplificado
  - return_greeting() em sessão não pausada → GuidedRecoveryError 409 SESSION_NOT_PAUSED
  - return_greeting() em sessão inexistente → GuidedRecoveryError 404
  - Endpoint POST /return-greeting: SSE, auth, error SSE para sessão não pausada

LLM é mocked. DB é real (SQLite in-memory via conftest).
"""

from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.core.exceptions import GuidedRecoveryError
from app.integrations.llm_client import CompletionChunk, CompletionMetrics

_PATCH_STREAM = "app.modules.engine.elicitation.stream_completion"

# ── Helpers ───────────────────────────────────────────────────────────────────


def _auth(token: dict) -> dict:
    return {"Authorization": f"Bearer {token['access_token']}"}


async def _create_project(client: AsyncClient, token: dict) -> dict:
    res = await client.post(
        "/api/v1/projects",
        json={"name": "Projeto Return", "business_domain": "Saúde"},
        headers=_auth(token),
    )
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


async def _pause_session(client: AsyncClient, token: dict, session_id: str) -> None:
    res = await client.patch(
        f"/api/v1/sessions/{session_id}",
        json={"status": "paused"},
        headers=_auth(token),
    )
    assert res.status_code == 200, res.text


async def _mock_greeting_stream(*args, **kwargs):
    """Simula stream de greeting com conteúdo."""
    chunks = ["Bem-vindo de volta! ", "Continuamos pela etapa Contexto."]
    for text in chunks:
        yield CompletionChunk(content=text, done=False)
    yield CompletionChunk(
        content="",
        done=True,
        metrics=CompletionMetrics(
            model="mock", input_tokens=40, output_tokens=18,
            total_tokens=58, cost_usd=0.001, latency_ms=90, success=True,
        ),
    )


# ── Testes de return_greeting() engine ───────────────────────────────────────


@pytest.mark.asyncio
async def test_return_greeting_sessao_pausada_persiste_mensagem(
    client: AsyncClient, tenant_a_token, seed_workflows
):
    """return_greeting() em sessão pausada: persiste msg como assistant, status=active."""
    from app.db.session import get_db
    from app.db.tenant import TenantScope
    from app.main import app
    from app.modules.engine.elicitation import return_greeting

    project = await _create_project(client, tenant_a_token)
    session_data = await _create_session(client, tenant_a_token, project["id"])
    session_id = session_data["id"]
    await _pause_session(client, tenant_a_token, session_id)

    with patch(_PATCH_STREAM, side_effect=_mock_greeting_stream):
        async for db in app.dependency_overrides[get_db]():
            scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
            chunks = []
            async for chunk in return_greeting(scope, session_id):
                chunks.append(chunk)

    # Chunks recebidos
    content_chunks = [c for c in chunks if not c.done]
    done_chunks = [c for c in chunks if c.done]
    assert len(content_chunks) == 2
    assert len(done_chunks) == 1

    # Mensagem persistida
    res = await client.get(
        f"/api/v1/sessions/{session_id}/messages",
        headers=_auth(tenant_a_token),
    )
    messages = res.json()["data"]["items"]
    assert len(messages) == 1
    assert messages[0]["role"] == "assistant"
    assert "Bem-vindo" in messages[0]["content"] or "Continuamos" in messages[0]["content"]

    # Status = active
    res = await client.get(f"/api/v1/sessions/{session_id}", headers=_auth(tenant_a_token))
    assert res.json()["data"]["status"] == "active"


@pytest.mark.asyncio
async def test_return_greeting_com_step_summaries(
    client: AsyncClient, tenant_a_token, seed_workflows
):
    """return_greeting() com step_summaries populado: greeting inclui contexto."""
    from sqlalchemy import select

    from app.db.session import get_db
    from app.db.tenant import TenantScope
    from app.main import app
    from app.modules.engine.elicitation import return_greeting
    from app.modules.sessions.models import Session

    project = await _create_project(client, tenant_a_token)
    session_data = await _create_session(client, tenant_a_token, project["id"])
    session_id = session_data["id"]

    # Injetar step_summaries no workflow_position
    async for db in app.dependency_overrides[get_db]():
        sess = await db.scalar(select(Session).where(Session.id == session_id))
        assert sess is not None
        sess.workflow_position = {
            "current_step": 2,
            "step_summaries": {"1": "Contexto do projeto mapeado com clareza"},
        }
        sess.status = "paused"
        await db.commit()

    captured_prompts = []

    async def _capture_stream(messages, *args, **kwargs):
        captured_prompts.append(messages)
        async for chunk in _mock_greeting_stream():
            yield chunk

    with patch(_PATCH_STREAM, side_effect=_capture_stream):
        async for db in app.dependency_overrides[get_db]():
            scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
            async for _ in return_greeting(scope, session_id):
                pass

    # Prompt enviado ao LLM deve conter o resumo da etapa 1
    assert len(captured_prompts) == 1
    user_prompt = captured_prompts[0][-1]["content"]
    assert "Contexto do projeto mapeado com clareza" in user_prompt


@pytest.mark.asyncio
async def test_return_greeting_sem_summaries_usa_template_simplificado(
    client: AsyncClient, tenant_a_token, seed_workflows
):
    """return_greeting() sem step_summaries usa RETURN_GREETING_TEMPLATE_NO_SUMMARIES."""
    from app.db.session import get_db
    from app.db.tenant import TenantScope
    from app.main import app
    from app.modules.engine.elicitation import return_greeting

    project = await _create_project(client, tenant_a_token)
    session_data = await _create_session(client, tenant_a_token, project["id"])
    session_id = session_data["id"]
    await _pause_session(client, tenant_a_token, session_id)

    captured_prompts = []

    async def _capture_stream(messages, *args, **kwargs):
        captured_prompts.append(messages)
        async for chunk in _mock_greeting_stream():
            yield chunk

    with patch(_PATCH_STREAM, side_effect=_capture_stream):
        async for db in app.dependency_overrides[get_db]():
            scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
            async for _ in return_greeting(scope, session_id):
                pass

    # Prompt simplificado: não deve ter "Etapas já concluídas:"
    assert len(captured_prompts) == 1
    user_prompt = captured_prompts[0][-1]["content"]
    assert "Etapas já concluídas" not in user_prompt
    assert "Contexto" in user_prompt  # próxima etapa referenciada


@pytest.mark.asyncio
async def test_return_greeting_sessao_nao_pausada_retorna_409(
    client: AsyncClient, tenant_a_token, seed_workflows
):
    """return_greeting() em sessão ativa → GuidedRecoveryError 409 SESSION_NOT_PAUSED."""
    from app.db.session import get_db
    from app.db.tenant import TenantScope
    from app.main import app
    from app.modules.engine.elicitation import return_greeting

    project = await _create_project(client, tenant_a_token)
    session_data = await _create_session(client, tenant_a_token, project["id"])
    session_id = session_data["id"]
    # Sessão criada com status=active — não pausada

    async for db in app.dependency_overrides[get_db]():
        scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
        with pytest.raises(GuidedRecoveryError) as exc_info:
            async for _ in return_greeting(scope, session_id):
                pass
        assert exc_info.value.status_code == 409
        assert exc_info.value.code == "SESSION_NOT_PAUSED"

    # Nenhuma mensagem criada
    res = await client.get(
        f"/api/v1/sessions/{session_id}/messages",
        headers=_auth(tenant_a_token),
    )
    assert len(res.json()["data"]["items"]) == 0


@pytest.mark.asyncio
async def test_return_greeting_llm_failure_reverts_status_to_paused(
    client: AsyncClient, tenant_a_token, seed_workflows
):
    """Se o stream LLM falhar mid-flight, status é revertido para 'paused' e nenhuma msg persiste.

    Cobre o rollback path em elicitation.return_greeting:341-348 que existe para
    evitar deixar a sessão presa em 'active' sem a mensagem de greeting persistida.
    """
    from sqlalchemy import select

    from app.db.session import get_db
    from app.db.tenant import TenantScope
    from app.main import app
    from app.modules.engine.elicitation import return_greeting
    from app.modules.sessions.models import Session

    project = await _create_project(client, tenant_a_token)
    session_data = await _create_session(client, tenant_a_token, project["id"])
    session_id = session_data["id"]
    await _pause_session(client, tenant_a_token, session_id)

    async def _failing_stream(*args, **kwargs):
        # Yield one chunk so the engine has progressed past the status flip,
        # then raise to simulate a mid-stream LLM failure.
        yield CompletionChunk(content="Bem-vindo ", done=False)
        raise RuntimeError("simulated LLM provider outage")

    with patch(_PATCH_STREAM, side_effect=_failing_stream):
        async for db in app.dependency_overrides[get_db]():
            scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
            with pytest.raises(RuntimeError, match="simulated LLM provider outage"):
                async for _ in return_greeting(scope, session_id):
                    pass

    # Status revertido para 'paused' (não ficou 'active' sem mensagem)
    async for db in app.dependency_overrides[get_db]():
        sess = await db.scalar(select(Session).where(Session.id == session_id))
        assert sess is not None
        assert sess.status == "paused"

    # Nenhuma mensagem assistant persistida
    res = await client.get(
        f"/api/v1/sessions/{session_id}/messages",
        headers=_auth(tenant_a_token),
    )
    assert len(res.json()["data"]["items"]) == 0


@pytest.mark.asyncio
async def test_return_greeting_sessao_nao_encontrada(
    client: AsyncClient, tenant_a_token, seed_workflows
):
    """return_greeting() em sessão inexistente → GuidedRecoveryError 404."""
    from app.db.session import get_db
    from app.db.tenant import TenantScope
    from app.main import app
    from app.modules.engine.elicitation import return_greeting

    async for db in app.dependency_overrides[get_db]():
        scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
        with pytest.raises(GuidedRecoveryError) as exc_info:
            async for _ in return_greeting(scope, "sessao-404"):
                pass
        assert exc_info.value.status_code == 404


# ── Testes do endpoint SSE /return-greeting ───────────────────────────────────


@pytest.mark.asyncio
async def test_return_greeting_endpoint_sessao_pausada(
    client: AsyncClient, tenant_a_token, seed_workflows
):
    """POST /sessions/{id}/return-greeting em sessão pausada → stream SSE bem-sucedido."""
    project = await _create_project(client, tenant_a_token)
    session_data = await _create_session(client, tenant_a_token, project["id"])
    session_id = session_data["id"]
    await _pause_session(client, tenant_a_token, session_id)

    with patch(_PATCH_STREAM, side_effect=_mock_greeting_stream):
        res = await client.post(
            f"/api/v1/sessions/{session_id}/return-greeting",
            headers=_auth(tenant_a_token),
        )

    assert res.status_code == 200
    assert "text/event-stream" in res.headers.get("content-type", "")
    body = res.text
    assert "event: message" in body or "event: done" in body


@pytest.mark.asyncio
async def test_return_greeting_endpoint_sessao_ativa_retorna_erro_sse(
    client: AsyncClient, tenant_a_token, seed_workflows
):
    """POST /return-greeting em sessão ativa → evento SSE de erro SESSION_NOT_PAUSED."""
    project = await _create_project(client, tenant_a_token)
    session_data = await _create_session(client, tenant_a_token, project["id"])
    session_id = session_data["id"]
    # Sessão ativa — não pausar

    res = await client.post(
        f"/api/v1/sessions/{session_id}/return-greeting",
        headers=_auth(tenant_a_token),
    )

    assert res.status_code == 200  # SSE: sempre 200, erros no stream
    assert "SESSION_NOT_PAUSED" in res.text


@pytest.mark.asyncio
async def test_return_greeting_endpoint_sem_auth_retorna_401(
    client: AsyncClient, seed_workflows
):
    """POST /return-greeting sem Authorization header → 401."""
    res = await client.post("/api/v1/sessions/qualquer-id/return-greeting")
    assert res.status_code == 401
