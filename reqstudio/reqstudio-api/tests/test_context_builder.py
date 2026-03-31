"""Testes do Context Builder — Story 5.2.

Cobre: montagem, priorização, truncamento, isolamento, contagem de tokens.

Padrão: client compartilhado, auth via headers=_auth(token).
Read-Before-Write: test_sessions.py (Lição 11).
"""

import pytest
from httpx import AsyncClient

from app.modules.engine.token_counter import estimate_tokens, estimate_messages_tokens


# ── Helpers ───────────────────────────────────────────────────────────────────

def _auth(token: dict) -> dict:
    return {"Authorization": f"Bearer {token['access_token']}"}


async def _create_project(client: AsyncClient, token: dict, **overrides) -> dict:
    payload = {"name": "Projeto Context", "business_domain": "Saúde", **overrides}
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


# ── Token Counter Tests ──────────────────────────────────────────────────────


def test_estimate_tokens_empty():
    assert estimate_tokens("") == 0


def test_estimate_tokens_basic():
    # 20 chars → ~5 tokens
    assert estimate_tokens("a" * 20) == 5


def test_estimate_tokens_minimum_is_one():
    assert estimate_tokens("hi") == 1


def test_estimate_messages_tokens():
    messages = [
        {"role": "system", "content": "a" * 100},
        {"role": "user", "content": "b" * 40},
    ]
    total = estimate_messages_tokens(messages)
    # 2 msgs * 4 overhead + 25 (100/4) + 10 (40/4) + 2 (conversa) = 45
    assert total == 45


# ── Context Builder Integration Tests ────────────────────────────────────────


@pytest.mark.asyncio
async def test_build_context_basic(client: AsyncClient, tenant_a_token, seed_workflows):
    """Monta contexto com system prompt e 1 mensagem."""
    from app.db.tenant import TenantScope
    from app.modules.engine.context_builder import build_context

    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])
    await _send_message(client, tenant_a_token, session["id"], "Quero criar um app de saúde")

    # Precisamos de um TenantScope real para o context_builder
    from tests.conftest import SEED_WORKFLOW_ID
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.db.session import get_db
    from app.main import app

    # Reusa a sessão de DB do client fixture
    async for db in app.dependency_overrides[get_db]():
        scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
        result = await build_context(scope, session["id"])

        assert result.project_id == project["id"]
        assert result.total_tokens > 0
        assert len(result.messages) >= 2  # system prompt + user message
        assert result.messages[0]["role"] == "system"
        # Última mensagem deve ser a do user
        user_msgs = [m for m in result.messages if m["role"] == "user"]
        assert len(user_msgs) == 1
        assert "saúde" in user_msgs[0]["content"]


@pytest.mark.asyncio
async def test_build_context_priority_order(client: AsyncClient, tenant_a_token, seed_workflows):
    """Verifica que system prompt vem antes das mensagens."""
    from app.db.tenant import TenantScope
    from app.modules.engine.context_builder import build_context
    from app.db.session import get_db
    from app.main import app

    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])
    await _send_message(client, tenant_a_token, session["id"], "Msg 1")
    await _send_message(client, tenant_a_token, session["id"], "Msg 2")

    async for db in app.dependency_overrides[get_db]():
        scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
        result = await build_context(scope, session["id"])

        # System prompt SEMPRE primeiro
        assert result.messages[0]["role"] == "system"
        # Mensagens de user vêm depois
        roles = [m["role"] for m in result.messages]
        system_idx = [i for i, r in enumerate(roles) if r == "system"]
        user_idx = [i for i, r in enumerate(roles) if r == "user"]
        assert all(s < u for s in system_idx for u in user_idx)


@pytest.mark.asyncio
async def test_build_context_truncation(client: AsyncClient, tenant_a_token, seed_workflows):
    """Com limite baixo de tokens, mensagens antigas são truncadas primeiro."""
    from app.db.tenant import TenantScope
    from app.modules.engine.context_builder import build_context
    from app.db.session import get_db
    from app.main import app

    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])

    # Criar 10 mensagens com conteúdo longo
    for i in range(10):
        await _send_message(client, tenant_a_token, session["id"], f"Mensagem número {i} " * 50)

    async for db in app.dependency_overrides[get_db]():
        scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
        # Limite baixo: forçar truncamento
        result = await build_context(scope, session["id"], max_tokens=500)

        assert result.truncated is True
        # Deve ter menos que 10 mensagens de user
        user_msgs = [m for m in result.messages if m["role"] == "user"]
        assert len(user_msgs) < 10
        # Mas deve ter pelo menos 1 mensagem recente
        assert len(user_msgs) >= 1
        # A última mensagem deve ser a mais recente (Mensagem número 9)
        assert "9" in user_msgs[-1]["content"]


@pytest.mark.asyncio
async def test_build_context_no_truncation_when_fits(client: AsyncClient, tenant_a_token, seed_workflows):
    """Com limite alto, nenhuma mensagem é truncada."""
    from app.db.tenant import TenantScope
    from app.modules.engine.context_builder import build_context
    from app.db.session import get_db
    from app.main import app

    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])
    await _send_message(client, tenant_a_token, session["id"], "Mensagem curta")

    async for db in app.dependency_overrides[get_db]():
        scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
        result = await build_context(scope, session["id"], max_tokens=50000)

        assert result.truncated is False


@pytest.mark.asyncio
async def test_build_context_session_not_found(client: AsyncClient, tenant_a_token, seed_workflows):
    """Sessão inexistente retorna 404."""
    from app.db.tenant import TenantScope
    from app.modules.engine.context_builder import build_context
    from app.core.exceptions import GuidedRecoveryError
    from app.db.session import get_db
    from app.main import app

    async for db in app.dependency_overrides[get_db]():
        scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
        with pytest.raises(GuidedRecoveryError) as exc_info:
            await build_context(scope, "sessao-inexistente")
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_build_context_cross_tenant_isolation(
    client: AsyncClient, tenant_a_token, tenant_b_token, seed_workflows,
):
    """Sessão de outro tenant não é acessível."""
    from app.db.tenant import TenantScope
    from app.modules.engine.context_builder import build_context
    from app.core.exceptions import GuidedRecoveryError
    from app.db.session import get_db
    from app.main import app

    project_a = await _create_project(client, tenant_a_token)
    session_a = await _create_session(client, tenant_a_token, project_a["id"])

    async for db in app.dependency_overrides[get_db]():
        scope_b = TenantScope(db=db, tenant_id=tenant_b_token["tenant_id"])
        with pytest.raises(GuidedRecoveryError) as exc_info:
            await build_context(scope_b, session_a["id"])
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_build_context_isolation_validation():
    """Validação direta: chunks de outro tenant disparam erro CRITICAL."""
    from app.modules.engine.context_builder import _validate_isolation
    from app.core.exceptions import GuidedRecoveryError

    chunks_ok = [{"tenant_id": "t1", "project_id": "p1", "content": "ok"}]
    _validate_isolation("t1", "p1", chunks_ok, [])  # Não deve lançar

    # Chunk de outro tenant
    chunks_bad_tenant = [{"tenant_id": "t2", "project_id": "p1", "content": "leak"}]
    with pytest.raises(GuidedRecoveryError) as exc_info:
        _validate_isolation("t1", "p1", chunks_bad_tenant, [])
    assert exc_info.value.status_code == 500
    assert "CONTEXT_ISOLATION_VIOLATION" in str(exc_info.value.code)

    # Chunk de outro projeto
    chunks_bad_project = [{"tenant_id": "t1", "project_id": "p2", "content": "leak"}]
    with pytest.raises(GuidedRecoveryError) as exc_info:
        _validate_isolation("t1", "p1", chunks_bad_project, [])
    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_build_context_message_isolation_validation():
    """Mensagem de outro tenant dispara erro CRITICAL."""
    from app.modules.engine.context_builder import _validate_isolation
    from app.core.exceptions import GuidedRecoveryError

    msgs_bad = [{"role": "user", "content": "msg", "tenant_id": "t2", "session_id": "s1"}]
    with pytest.raises(GuidedRecoveryError):
        _validate_isolation("t1", "p1", [], msgs_bad)


@pytest.mark.asyncio
async def test_build_context_empty_session(client: AsyncClient, tenant_a_token, seed_workflows):
    """Sessão sem mensagens retorna apenas system prompt."""
    from app.db.tenant import TenantScope
    from app.modules.engine.context_builder import build_context
    from app.db.session import get_db
    from app.main import app

    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])

    async for db in app.dependency_overrides[get_db]():
        scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
        result = await build_context(scope, session["id"])

        assert len(result.messages) >= 1  # pelo menos system prompt
        assert result.messages[0]["role"] == "system"
        assert result.truncated is False
        assert result.doc_count == 0
