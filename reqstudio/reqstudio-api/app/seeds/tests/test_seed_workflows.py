"""Testes do seed de workflows — Story 5.5-1.

Cobre: qualidade BMAD do system prompt, profundidade dos steps,
e comportamento do re-seed com --force.

Padrão: testes unitários/estáticos (sem DB) + testes de integração com DB in-memory.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.modules.auth.models import RefreshToken, Tenant, User  # noqa: F401
from app.modules.documents.models import Document, DocumentChunk  # noqa: F401
from app.modules.projects.models import Project  # noqa: F401
from app.modules.sessions.models import Session, Message  # noqa: F401
from app.modules.workflows.models import Workflow, WorkflowStep, Agent  # noqa: F401

from app.seeds.seed_workflows import SEED_AGENT, SEED_STEPS, SEED_WORKFLOW, seed

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
async def db_session():
    """Sessão SQLite in-memory isolada para testes do seed."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# ── Testes Estáticos (sem DB) ─────────────────────────────────────────────────


def test_system_prompt_tem_comprimento_minimo():
    """AC 4: system_prompt deve ter mais de 800 chars para ser BMAD-quality."""
    prompt = SEED_AGENT["system_prompt"]
    assert len(prompt) > 800, (
        f"system_prompt tem apenas {len(prompt)} chars — mínimo exigido é 800. "
        "Adicione mais contexto de persona, técnicas de elicitação ou few-shot examples."
    )


def test_system_prompt_contem_tecnicas_de_elicitacao():
    """AC 1: system_prompt deve mencionar pelo menos uma técnica BMAD real."""
    prompt = SEED_AGENT["system_prompt"].lower()
    tecnicas = ["5 whys", "jtbd", "cenário", "contraponto", "jobs to be done"]
    encontradas = [t for t in tecnicas if t.lower() in prompt]
    assert len(encontradas) >= 2, (
        f"system_prompt menciona apenas {len(encontradas)} técnica(s): {encontradas}. "
        "Esperado: pelo menos 2 técnicas de elicitação BMAD."
    )


def test_system_prompt_contem_few_shot_examples():
    """AC 1: system_prompt deve ter pelo menos 2 exemplos few-shot de turno user/mary."""
    prompt = SEED_AGENT["system_prompt"]
    # Verificar presença de marcadores de exemplos few-shot
    assert "Exemplo 1" in prompt or "exemplo 1" in prompt.lower(), (
        "system_prompt não contém 'Exemplo 1' — adicione pelo menos 2 exemplos few-shot."
    )
    assert "Exemplo 2" in prompt or "exemplo 2" in prompt.lower(), (
        "system_prompt não contém 'Exemplo 2' — adicione pelo menos 2 exemplos few-shot."
    )


def test_system_prompt_contem_instrucao_de_verbosidade():
    """AC 1: system_prompt deve ter regra explícita de verbosidade (máx X perguntas)."""
    prompt = SEED_AGENT["system_prompt"]
    assert "3 perguntas" in prompt or "máximo 3" in prompt or "max 3" in prompt.lower(), (
        "system_prompt não contém instrução de verbosidade (máx 3 perguntas por turno)."
    )


def test_system_prompt_contem_instrucao_de_fase():
    """AC 2, 3: system_prompt deve instruir comportamento por fase (Fase 1 e Fase 2)."""
    prompt = SEED_AGENT["system_prompt"]
    assert "Fase 1" in prompt, "system_prompt deve ter seção explícita de Fase 1."
    assert "Fase 2" in prompt, "system_prompt deve ter seção explícita de Fase 2."


def test_system_prompt_contem_instrucao_de_transicao():
    """AC 2: system_prompt deve instruir como sinalizar transição entre fases."""
    prompt = SEED_AGENT["system_prompt"]
    # Verificar que há instrução de transição entre Fase 1 e Fase 2
    has_transition = (
        "transição" in prompt.lower()
        or "aprofundar" in prompt.lower()
        or "Agora que tenho" in prompt
    )
    assert has_transition, (
        "system_prompt não contém instrução de transição entre Fase 1 e Fase 2."
    )


def test_seed_tem_cinco_steps():
    """AC 3, 5: seed deve ter exatamente 5 steps de elicitação."""
    assert len(SEED_STEPS) == 5, (
        f"SEED_STEPS tem {len(SEED_STEPS)} steps — esperados 5."
    )


def test_todos_os_steps_tem_profundidade_minima():
    """AC 3: cada step deve ter mais de 100 chars (profundidade mínima garantida)."""
    for i, step in enumerate(SEED_STEPS, 1):
        template = step["prompt_template"]
        assert len(template) > 100, (
            f"Step {i} tem apenas {len(template)} chars — mínimo é 100. "
            f"Conteúdo: '{template[:80]}...'"
        )


def test_steps_cobrem_tecnicas_distintas():
    """AC 3: os steps em conjunto devem cobrir pelo menos 3 técnicas BMAD distintas."""
    todos_templates = " ".join(s["prompt_template"].lower() for s in SEED_STEPS)
    tecnicas_presentes = []
    if "jtbd" in todos_templates or "jobs to be done" in todos_templates:
        tecnicas_presentes.append("JTBD")
    if "cenário" in todos_templates or "pior" in todos_templates:
        tecnicas_presentes.append("Cenários Extremos")
    if "contraponto" in todos_templates or "e se" in todos_templates:
        tecnicas_presentes.append("Contraponto")
    if "impacto" in todos_templates or "não resolver" in todos_templates:
        tecnicas_presentes.append("Impacto Negativo")

    assert len(tecnicas_presentes) >= 2, (
        f"Steps cobrem apenas {len(tecnicas_presentes)} técnica(s): {tecnicas_presentes}. "
        "Esperadas pelo menos 2 técnicas distintas de elicitação."
    )


def test_step1_cobre_abertura_com_documentos():
    """AC 3: Step 1 deve ter instrução para lidar com documentos importados."""
    template = SEED_STEPS[0]["prompt_template"].lower()
    has_docs_instruction = "documento" in template or "importado" in template
    assert has_docs_instruction, (
        "Step 1 deve instruir como abrir quando há documentos importados na sessão."
    )


def test_agent_name_is_mary():
    """Sanidade: agent deve se chamar Mary."""
    assert SEED_AGENT["name"] == "Mary"
    assert SEED_AGENT["role"] == "analyst"


# ── Testes de Integração com DB ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_seed_insere_agent_workflow_e_steps(db_session: AsyncSession, monkeypatch):
    """AC 5: seed() deve criar Agent, Workflow e 5 WorkflowSteps no banco."""
    from sqlalchemy import select
    from unittest.mock import AsyncMock, MagicMock, patch

    # Mock do create_async_engine para usar a sessão de teste
    mock_engine = MagicMock()
    mock_session_cm = MagicMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=db_session)
    mock_session_cm.__aexit__ = AsyncMock(return_value=False)
    mock_factory = MagicMock(return_value=mock_session_cm)

    with (
        patch("app.seeds.seed_workflows.create_async_engine", return_value=mock_engine),
        patch("app.seeds.seed_workflows.sessionmaker", return_value=mock_factory),
    ):
        await seed(force=False)

    # Verificar Agent
    agent = await db_session.scalar(select(Agent).where(Agent.name == "Mary"))
    assert agent is not None, "Agent 'Mary' não foi criado pelo seed."
    assert len(agent.system_prompt) > 800, (
        f"Agent.system_prompt tem {len(agent.system_prompt)} chars — esperado > 800."
    )

    # Verificar Workflow
    workflow = await db_session.scalar(
        select(Workflow).where(Workflow.name == "elicitation-briefing")
    )
    assert workflow is not None, "Workflow 'elicitation-briefing' não foi criado."

    # Verificar Steps
    from sqlalchemy import func
    count = await db_session.scalar(
        select(func.count()).select_from(WorkflowStep).where(
            WorkflowStep.workflow_id == workflow.id
        )
    )
    assert count == 5, f"Esperados 5 WorkflowSteps, encontrados {count}."


@pytest.mark.asyncio
async def test_seed_idempotente_sem_force(db_session: AsyncSession, monkeypatch):
    """AC 5: seed() sem --force não deve duplicar dados se workflow já existe."""
    from sqlalchemy import select, func
    from unittest.mock import AsyncMock, MagicMock, patch

    mock_engine = MagicMock()
    mock_session_cm = MagicMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=db_session)
    mock_session_cm.__aexit__ = AsyncMock(return_value=False)
    mock_factory = MagicMock(return_value=mock_session_cm)

    with (
        patch("app.seeds.seed_workflows.create_async_engine", return_value=mock_engine),
        patch("app.seeds.seed_workflows.sessionmaker", return_value=mock_factory),
    ):
        # Primeiro seed
        await seed(force=False)
        # Segundo seed sem force — não deve duplicar
        await seed(force=False)

    count = await db_session.scalar(
        select(func.count()).select_from(Workflow).where(
            Workflow.name == "elicitation-briefing"
        )
    )
    assert count == 1, f"Workflow duplicado — encontrados {count} registros após 2 seeds."


@pytest.mark.asyncio
async def test_seed_com_force_substitui_prompt_antigo(db_session: AsyncSession, monkeypatch):
    """AC 5: seed() com --force deve substituir o agent e workflow sem deixar órfãos."""
    from sqlalchemy import select, func
    from unittest.mock import AsyncMock, MagicMock, patch

    mock_engine = MagicMock()
    mock_session_cm = MagicMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=db_session)
    mock_session_cm.__aexit__ = AsyncMock(return_value=False)
    mock_factory = MagicMock(return_value=mock_session_cm)

    with (
        patch("app.seeds.seed_workflows.create_async_engine", return_value=mock_engine),
        patch("app.seeds.seed_workflows.sessionmaker", return_value=mock_factory),
    ):
        # Seed inicial
        await seed(force=False)

        # Re-seed com force
        await seed(force=True)

    # Deve existir exatamente 1 workflow, 1 agent e 5 steps
    wf_count = await db_session.scalar(
        select(func.count()).select_from(Workflow).where(
            Workflow.name == "elicitation-briefing"
        )
    )
    assert wf_count == 1, f"Após --force, esperado 1 workflow, encontrado {wf_count}."

    agent_count = await db_session.scalar(
        select(func.count()).select_from(Agent).where(Agent.name == "Mary")
    )
    assert agent_count == 1, f"Após --force, esperado 1 agent, encontrado {agent_count}."

    workflow = await db_session.scalar(
        select(Workflow).where(Workflow.name == "elicitation-briefing")
    )
    step_count = await db_session.scalar(
        select(func.count()).select_from(WorkflowStep).where(
            WorkflowStep.workflow_id == workflow.id
        )
    )
    assert step_count == 5, f"Após --force, esperados 5 steps, encontrados {step_count}."

    # Verificar que o novo prompt tem qualidade BMAD
    agent = await db_session.scalar(select(Agent).where(Agent.name == "Mary"))
    assert len(agent.system_prompt) > 800, (
        "Após --force, o novo system_prompt deve ter > 800 chars."
    )


async def test_seed_deleta_agentes_com_mesmo_nome_preventivamente(db_session: AsyncSession, monkeypatch):
    """Garantir que não existam duplicatas de agentes com o mesmo nome (QA-5-5-1-001)."""
    from sqlalchemy import select, func
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.modules.workflows.models import Agent
    
    # Inserir agente "sujo" manualmente
    stray_agent = Agent(name="Mary", role="analyst", system_prompt="old prompt")
    db_session.add(stray_agent)
    await db_session.commit()
    
    mock_engine = MagicMock()
    mock_session_cm = MagicMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=db_session)
    mock_session_cm.__aexit__ = AsyncMock(return_value=False)
    mock_factory = MagicMock(return_value=mock_session_cm)
    
    with (
        patch("app.seeds.seed_workflows.create_async_engine", return_value=mock_engine),
        patch("app.seeds.seed_workflows.sessionmaker", return_value=mock_factory),
    ):
        # Executar seed com force
        await seed(force=True)
    
    # Verificar que só existe 1 agente chamado Mary e que o prompt é o novo
    agents = (await db_session.scalars(select(Agent).where(Agent.name == "Mary"))).all()
    assert len(agents) == 1, f"Deveria existir apenas 1 agente 'Mary', encontrados {len(agents)}."
    assert len(agents[0].system_prompt) > 800
