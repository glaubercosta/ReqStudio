"""Testes de _advance_workflow com geração de mensagens de transição (Story 7.2).

Cobre:
  - Mensagem de transição persistida ao avançar step N → N+1
  - step_summaries[str(N)] armazenado após advance
  - Mensagem de conclusão e status=completed ao avançar último step
  - Helper _extract_summary: tag [RESUMO]: e fallback
  - Invariante: kickstart NÃO chama _advance_workflow (step_summaries ausente)

LLM é mocked. DB é real (SQLite in-memory via conftest).
"""

from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tenant import TenantScope
from app.integrations.llm_client import CompletionChunk, CompletionMetrics
from app.modules.engine.elicitation import _extract_summary
from app.modules.workflows.models import Agent, Workflow, WorkflowStep

_PATCH_STREAM = "app.modules.engine.elicitation.stream_completion"

# ── Helpers ───────────────────────────────────────────────────────────────────


def _auth(token: dict) -> dict:
    return {"Authorization": f"Bearer {token['access_token']}"}


async def _create_project(client: AsyncClient, token: dict) -> dict:
    res = await client.post(
        "/api/v1/projects",
        json={"name": "Projeto Transição", "business_domain": "Tecnologia"},
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


async def _seed_multi_step_workflow(
    db: AsyncSession, tenant_id: str, num_steps: int = 5
) -> tuple[str, str]:
    """Cria workflow com num_steps steps e retorna (workflow_id, agent_id)."""
    agent = Agent(
        name=f"Mary-{num_steps}steps",
        role="analyst",
        system_prompt="Você é Mary.",
    )
    db.add(agent)
    await db.flush()

    workflow = Workflow(
        name=f"test-workflow-{num_steps}",
        description="Workflow de teste",
    )
    db.add(workflow)
    await db.flush()

    for pos in range(1, num_steps + 1):
        step = WorkflowStep(
            workflow_id=workflow.id,
            agent_id=agent.id,
            position=pos,
            prompt_template=f"Prompt da etapa {pos}",
            step_type="elicitation",
        )
        db.add(step)

    await db.commit()
    return workflow.id, agent.id


async def _mock_transition_stream(*args, **kwargs):
    """Simula stream de transição com tag [RESUMO]: em linha própria."""
    chunks = [
        "[RESUMO]: Contexto do projeto capturado com clareza\n\n",
        "Excelente progresso! ",
        "Vamos para a próxima etapa.",
    ]
    for piece in chunks:
        yield CompletionChunk(content=piece, done=False)
    yield CompletionChunk(
        content="",
        done=True,
        metrics=CompletionMetrics(
            model="mock", input_tokens=30, output_tokens=15,
            total_tokens=45, cost_usd=0.001, latency_ms=100, success=True,
        ),
    )


async def _mock_completion_stream(*args, **kwargs):
    """Simula stream de conclusão com tag [RESUMO]: em linha própria."""
    chunks = [
        "[RESUMO]: Restrições inegociáveis mapeadas\n\n",
        "Elicitação concluída com sucesso! ",
        "Obrigada pela colaboração.",
    ]
    for piece in chunks:
        yield CompletionChunk(content=piece, done=False)
    yield CompletionChunk(
        content="",
        done=True,
        metrics=CompletionMetrics(
            model="mock", input_tokens=40, output_tokens=20,
            total_tokens=60, cost_usd=0.002, latency_ms=120, success=True,
        ),
    )


async def _mock_elicit_stream(*args, **kwargs):
    """Simula stream de elicitação principal."""
    yield CompletionChunk(content="Resposta da Mary.", done=False)
    yield CompletionChunk(
        content="",
        done=True,
        metrics=CompletionMetrics(
            model="mock", input_tokens=50, output_tokens=10,
            total_tokens=60, cost_usd=0.001, latency_ms=80, success=True,
        ),
    )


# ── Testes unitários de _extract_summary ─────────────────────────────────────


def test_extract_summary_with_tag():
    """_extract_summary extrai texto após [RESUMO]: da primeira linha."""
    response = "[RESUMO]: Sistema de gestão de estoque captado\nRestante do texto aqui."
    result = _extract_summary(response)
    assert result == "Sistema de gestão de estoque captado"


def test_extract_summary_fallback():
    """_extract_summary retorna primeiros 120 chars quando tag ausente."""
    response = "Excelente progresso! Avançamos muito nesta etapa de contexto."
    result = _extract_summary(response)
    assert result == response[:120]
    assert "[RESUMO]" not in result


def test_extract_summary_empty():
    """_extract_summary retorna string vazia para input vazio."""
    assert _extract_summary("") == ""
    assert _extract_summary("   ") == ""


# ── Testes de integração de _advance_workflow ─────────────────────────────────


@pytest.mark.asyncio
async def test_advance_workflow_persists_transition_message(
    client: AsyncClient, tenant_a_token, seed_workflows
):
    """_advance_workflow persiste mensagem de transição ao avançar step 1 → 2."""
    from app.db.session import get_db
    from app.main import app
    from app.modules.engine.elicitation import elicit

    # Criar sessão
    project = await _create_project(client, tenant_a_token)
    session_data = await _create_session(client, tenant_a_token, project["id"])
    session_id = session_data["id"]

    # Seed extra step no workflow para ter 2 steps totais
    async for db in app.dependency_overrides[get_db]():
        from conftest import SEED_WORKFLOW_ID

        step2 = WorkflowStep(
            workflow_id=SEED_WORKFLOW_ID,
            agent_id="agent-analyst-001",
            position=2,
            prompt_template="Etapa 2",
            step_type="elicitation",
        )
        db.add(step2)
        await db.commit()

    call_count = 0

    async def _mock_stream_switcher(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # Primeira chamada: elicit principal
            async for chunk in _mock_elicit_stream():
                yield chunk
        else:
            # Segunda chamada: transição
            async for chunk in _mock_transition_stream():
                yield chunk

    with patch(_PATCH_STREAM, side_effect=_mock_stream_switcher):
        async for db in app.dependency_overrides[get_db]():
            scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
            async for _ in elicit(scope, session_id, "Primeira mensagem"):
                pass

    # Verificar mensagens: user + assistant (elicit) + assistant (transição)
    res = await client.get(
        f"/api/v1/sessions/{session_id}/messages",
        headers=_auth(tenant_a_token),
    )
    messages = res.json()["data"]["items"]
    assert len(messages) == 3

    roles = [m["role"] for m in messages]
    assert roles == ["user", "assistant", "assistant"]

    # Última mensagem é a transição. Por contrato, a tag [RESUMO]: é metadado
    # interno e NÃO deve vazar no conteúdo persistido para o usuário.
    transition_msg = messages[2]
    assert transition_msg["role"] == "assistant"
    assert "[RESUMO]:" not in transition_msg["content"]
    assert "Excelente progresso" in transition_msg["content"]


@pytest.mark.asyncio
async def test_advance_workflow_stores_step_summary(
    client: AsyncClient, tenant_a_token, seed_workflows
):
    """_advance_workflow armazena step_summaries[str(N)] após advance step 1 → 2."""
    from app.db.session import get_db
    from app.main import app
    from app.modules.engine.elicitation import elicit

    project = await _create_project(client, tenant_a_token)
    session_data = await _create_session(client, tenant_a_token, project["id"])
    session_id = session_data["id"]

    async for db in app.dependency_overrides[get_db]():
        from conftest import SEED_WORKFLOW_ID

        step2 = WorkflowStep(
            workflow_id=SEED_WORKFLOW_ID,
            agent_id="agent-analyst-001",
            position=2,
            prompt_template="Etapa 2",
            step_type="elicitation",
        )
        db.add(step2)
        await db.commit()

    call_count = 0

    async def _mock_stream_switcher(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            async for chunk in _mock_elicit_stream():
                yield chunk
        else:
            async for chunk in _mock_transition_stream():
                yield chunk

    with patch(_PATCH_STREAM, side_effect=_mock_stream_switcher):
        async for db in app.dependency_overrides[get_db]():
            scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
            async for _ in elicit(scope, session_id, "Primeira mensagem"):
                pass

    # Verificar workflow_position.step_summaries["1"]
    res = await client.get(f"/api/v1/sessions/{session_id}", headers=_auth(tenant_a_token))
    data = res.json()["data"]
    wp = data["workflow_position"]
    assert wp is not None
    assert wp["current_step"] == 2
    assert "step_summaries" in wp
    assert "1" in wp["step_summaries"]
    assert len(wp["step_summaries"]["1"]) > 0


@pytest.mark.asyncio
async def test_advance_workflow_step_counter_increments_before_llm(
    client: AsyncClient, tenant_a_token, seed_workflows
):
    """AC 4: current_step já é N+1 no momento da chamada LLM de transição."""
    from app.db.session import get_db
    from app.main import app
    from app.modules.engine.elicitation import elicit

    project = await _create_project(client, tenant_a_token)
    session_data = await _create_session(client, tenant_a_token, project["id"])
    session_id = session_data["id"]

    async for db in app.dependency_overrides[get_db]():
        from conftest import SEED_WORKFLOW_ID

        step2 = WorkflowStep(
            workflow_id=SEED_WORKFLOW_ID,
            agent_id="agent-analyst-001",
            position=2,
            prompt_template="Etapa 2",
            step_type="elicitation",
        )
        db.add(step2)
        await db.commit()

    captured_prompts = []

    async def _capture_prompt(messages, *args, **kwargs):
        captured_prompts.append(messages)
        # Primeiro call: elicit principal
        if len(captured_prompts) == 1:
            async for chunk in _mock_elicit_stream():
                yield chunk
        else:
            async for chunk in _mock_transition_stream():
                yield chunk

    with patch(_PATCH_STREAM, side_effect=_capture_prompt):
        async for db in app.dependency_overrides[get_db]():
            scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
            async for _ in elicit(scope, session_id, "Mensagem"):
                pass

    # Segunda chamada LLM é a de transição: deve mencionar a próxima etapa por nome
    # (apenas "2" seria trivialmente true via "step 2"/"etapa 2" — exigimos o nome).
    assert len(captured_prompts) >= 2
    transition_prompt = captured_prompts[1][-1]["content"]  # último role=user
    assert "Usuários e stakeholders" in transition_prompt


@pytest.mark.asyncio
async def test_advance_workflow_completion_step5(
    client: AsyncClient, tenant_a_token, seed_workflows
):
    """Ao concluir o último step: status=completed, mensagem de conclusão, step_summaries."""
    from app.db.session import get_db
    from app.main import app
    from app.modules.engine.elicitation import elicit

    # seed_workflows tem apenas 1 step → current_step=1 == total_steps=1 → completion
    project = await _create_project(client, tenant_a_token)
    session_resp = await _create_session(client, tenant_a_token, project["id"])
    session_id = session_resp["id"]

    call_count = 0

    async def _mock_stream_switcher(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            async for chunk in _mock_elicit_stream():
                yield chunk
        else:
            async for chunk in _mock_completion_stream():
                yield chunk

    with patch(_PATCH_STREAM, side_effect=_mock_stream_switcher):
        async for db in app.dependency_overrides[get_db]():
            scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
            async for _ in elicit(scope, session_id, "Mensagem final"):
                pass

    # Verificar status = completed
    res = await client.get(f"/api/v1/sessions/{session_id}", headers=_auth(tenant_a_token))
    data = res.json()["data"]
    assert data["status"] == "completed"

    wp = data["workflow_position"]
    assert wp["completed"] is True
    assert "step_summaries" in wp
    assert "1" in wp["step_summaries"]

    # Verificar mensagem de conclusão persistida
    msgs_res = await client.get(
        f"/api/v1/sessions/{session_id}/messages",
        headers=_auth(tenant_a_token),
    )
    messages = msgs_res.json()["data"]["items"]
    # user + assistant (elicit) + assistant (conclusão)
    assert len(messages) == 3
    # Tag [RESUMO]: é metadado interno e deve ser strippada do conteúdo persistido.
    assert "[RESUMO]:" not in messages[2]["content"]
    assert "Elicitação concluída" in messages[2]["content"]


@pytest.mark.asyncio
async def test_kickstart_nao_popula_step_summaries(
    client: AsyncClient, tenant_a_token, seed_workflows
):
    """AC 5: kickstart NÃO chama _advance_workflow; step_summaries permanece ausente."""
    from app.db.session import get_db
    from app.main import app
    from app.modules.engine.elicitation import kickstart

    async def _mock_kickstart_stream(*args, **kwargs):
        yield CompletionChunk(content="Olá! Sou Mary.", done=False)
        yield CompletionChunk(
            content="",
            done=True,
            metrics=CompletionMetrics(
                model="mock", input_tokens=20, output_tokens=5,
                total_tokens=25, cost_usd=0.001, latency_ms=50, success=True,
            ),
        )

    project = await _create_project(client, tenant_a_token)
    session_data = await _create_session(client, tenant_a_token, project["id"])
    session_id = session_data["id"]

    with patch(_PATCH_STREAM, side_effect=_mock_kickstart_stream):
        async for db in app.dependency_overrides[get_db]():
            scope = TenantScope(db=db, tenant_id=tenant_a_token["tenant_id"])
            async for _ in kickstart(scope, session_id):
                pass

    res = await client.get(f"/api/v1/sessions/{session_id}", headers=_auth(tenant_a_token))
    data = res.json()["data"]
    wp = data.get("workflow_position") or {}
    # step_summaries ausente ou vazio — kickstart não gera transição
    assert not wp.get("step_summaries")
    # current_step não avançou além do padrão
    assert wp.get("current_step", 1) == 1
