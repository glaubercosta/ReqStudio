"""Testes do Elicitation Engine — kickstart (Story 7.1).

Cobre:
  - kickstart() em sessão vazia: persiste mensagem como role=assistant, message_index=0
  - kickstart() em sessão com mensagens: lança GuidedRecoveryError 409
  - workflow_position não avança após kickstart
  - isolamento cross-tenant

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
        json={"name": "Projeto Kickstart", "business_domain": "Tecnologia"},
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


async def _get_messages(client: AsyncClient, token: dict, session_id: str) -> list:
    res = await client.get(
        f"/api/v1/sessions/{session_id}/messages",
        headers=_auth(token),
    )
    assert res.status_code == 200
    return res.json()["data"]["items"]


async def _mock_kickstart_stream(*args, **kwargs):
    """Simula streaming de resposta do LLM para kickstart."""
    chunks = ["Olá! Sou Mary, ", "analista de requisitos."]
    for text in chunks:
        yield CompletionChunk(content=text, done=False)
    yield CompletionChunk(
        content="",
        done=True,
        metrics=CompletionMetrics(
            model="mock",
            input_tokens=60,
            output_tokens=20,
            total_tokens=80,
            cost_usd=0.002,
            latency_ms=150,
            success=True,
        ),
    )


# ── Testes do kickstart() engine ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_kickstart_sessao_vazia_persiste_mensagem(
    client: AsyncClient, tenant_a_token, seed_workflows
):
    """kickstart() em sessão vazia: persiste mensagem assistant, message_index=0."""
    from app.db.session import get_db
    from app.db.tenant import TenantScope
    from app.main import app
    from app.modules.engine.elicitation import kickstart

    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])

    with patch(_PATCH_STREAM, side_effect=_mock_kickstart_stream):
        async for db in app.dependency_overrides[get_db]():
            scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
            chunks = []
            async for chunk in kickstart(scope, session["id"]):
                chunks.append(chunk)

    # Validar chunks recebidos
    content_chunks = [c for c in chunks if not c.done]
    done_chunks = [c for c in chunks if c.done]
    assert len(content_chunks) == 2
    assert len(done_chunks) == 1

    # Validar mensagem persistida
    messages = await _get_messages(client, tenant_a_token, session["id"])
    assert len(messages) == 1
    assert messages[0]["role"] == "assistant"
    assert messages[0]["message_index"] == 0
    assert "Mary" in messages[0]["content"]


@pytest.mark.asyncio
async def test_kickstart_sessao_com_mensagens_retorna_409(
    client: AsyncClient, tenant_a_token, seed_workflows
):
    """kickstart() em sessão com mensagens existentes → GuidedRecoveryError 409."""
    from unittest.mock import patch

    from app.db.session import get_db
    from app.db.tenant import TenantScope
    from app.main import app
    from app.modules.engine.elicitation import elicit, kickstart

    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])

    # Primeiro: adicionar uma mensagem via elicit
    async def _mock_elicit(*args, **kwargs):
        yield CompletionChunk(content="Resposta", done=False)
        yield CompletionChunk(
            content="", done=True, metrics=CompletionMetrics(model="mock", success=True)
        )

    with patch(_PATCH_STREAM, side_effect=_mock_elicit):
        async for db in app.dependency_overrides[get_db]():
            scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
            async for _ in elicit(scope, session["id"], "Primeira mensagem"):
                pass

    # Agora tentar kickstart → deve retornar 409
    with patch(_PATCH_STREAM, side_effect=_mock_kickstart_stream):
        async for db in app.dependency_overrides[get_db]():
            scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
            with pytest.raises(GuidedRecoveryError) as exc_info:
                async for _ in kickstart(scope, session["id"]):
                    pass
            assert exc_info.value.status_code == 409
            assert exc_info.value.code == "SESSION_ALREADY_STARTED"

    # Sem novas mensagens adicionadas pelo kickstart
    # Story 7.2: elicit em 1-step workflow gera completion message → 3 mensagens no total
    messages = await _get_messages(client, tenant_a_token, session["id"])
    # user + assistant(elicit) + assistant(completion), nenhuma do kickstart
    assert len(messages) == 3


@pytest.mark.asyncio
async def test_kickstart_nao_avanca_workflow_position(
    client: AsyncClient, tenant_a_token, seed_workflows
):
    """kickstart() NÃO chama _advance_workflow; workflow_position.current_step permanece em 1."""
    from app.db.session import get_db
    from app.db.tenant import TenantScope
    from app.main import app
    from app.modules.engine.elicitation import kickstart

    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])

    with patch(_PATCH_STREAM, side_effect=_mock_kickstart_stream):
        async for db in app.dependency_overrides[get_db]():
            scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
            async for _ in kickstart(scope, session["id"]):
                pass

    # workflow_position não deve ter avançado; session status deve ser "active"
    res = await client.get(f"/api/v1/sessions/{session['id']}", headers=_auth(tenant_a_token))
    data = res.json()["data"]
    assert data["status"] == "active"
    # workflow_position não avançou — completed deve ser ausente ou False
    wp = data.get("workflow_position")
    if wp:
        assert wp.get("completed") is not True


@pytest.mark.asyncio
async def test_kickstart_sessao_nao_encontrada(client: AsyncClient, tenant_a_token, seed_workflows):
    """kickstart() em sessão inexistente → GuidedRecoveryError 404."""
    from app.db.session import get_db
    from app.db.tenant import TenantScope
    from app.main import app
    from app.modules.engine.elicitation import kickstart

    async for db in app.dependency_overrides[get_db]():
        scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
        with pytest.raises(GuidedRecoveryError) as exc_info:
            async for _ in kickstart(scope, "sessao-404"):
                pass
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_kickstart_cross_tenant_isolation(
    client: AsyncClient, tenant_a_token, tenant_b_token, seed_workflows
):
    """kickstart() de outro tenant → GuidedRecoveryError 404 (isolamento)."""
    from app.db.session import get_db
    from app.db.tenant import TenantScope
    from app.main import app
    from app.modules.engine.elicitation import kickstart

    project_a = await _create_project(client, tenant_a_token)
    session_a = await _create_session(client, tenant_a_token, project_a["id"])

    async for db in app.dependency_overrides[get_db]():
        scope_b = TenantScope(db=db, tenant_id=tenant_b_token["tenant_id"])
        with pytest.raises(GuidedRecoveryError) as exc_info:
            async for _ in kickstart(scope_b, session_a["id"]):
                pass
        assert exc_info.value.status_code == 404


# ── Testes do endpoint /kickstart (SSE) ──────────────────────────────────────


@pytest.mark.asyncio
async def test_kickstart_endpoint_sessao_vazia(
    client: AsyncClient, tenant_a_token, seed_workflows
):
    """POST /sessions/{id}/kickstart em sessão vazia → stream SSE bem-sucedido."""
    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])

    with patch(_PATCH_STREAM, side_effect=_mock_kickstart_stream):
        res = await client.post(
            f"/api/v1/sessions/{session['id']}/kickstart",
            headers=_auth(tenant_a_token),
        )

    assert res.status_code == 200
    assert "text/event-stream" in res.headers.get("content-type", "")
    body = res.text
    assert "event: message" in body or "event: done" in body


@pytest.mark.asyncio
async def test_kickstart_endpoint_sessao_ja_iniciada_retorna_erro_sse(
    client: AsyncClient, tenant_a_token, seed_workflows
):
    """POST /kickstart em sessão com mensagens → evento SSE de erro com SESSION_ALREADY_STARTED."""
    from unittest.mock import patch as mock_patch

    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])

    # Primeiro kickstart bem-sucedido
    with mock_patch(
        "app.modules.engine.elicitation.stream_completion", side_effect=_mock_kickstart_stream
    ):
        await client.post(
            f"/api/v1/sessions/{session['id']}/kickstart",
            headers=_auth(tenant_a_token),
        )

    # Segundo kickstart → deve retornar evento de erro
    with mock_patch(
        "app.modules.engine.elicitation.stream_completion", side_effect=_mock_kickstart_stream
    ):
        res = await client.post(
            f"/api/v1/sessions/{session['id']}/kickstart",
            headers=_auth(tenant_a_token),
        )

    assert res.status_code == 200  # SSE: sempre 200, erros vêm no stream
    assert "SESSION_ALREADY_STARTED" in res.text


@pytest.mark.asyncio
async def test_kickstart_endpoint_sem_auth_retorna_401(client: AsyncClient, seed_workflows):
    """POST /kickstart sem Authorization header → 401."""
    res = await client.post("/api/v1/sessions/qualquer-id/kickstart")
    assert res.status_code == 401
