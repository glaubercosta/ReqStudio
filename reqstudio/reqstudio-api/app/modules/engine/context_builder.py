"""Context Builder — monta prompt com contexto priorizado e isolado (Story 5.2).

Prioridade de montagem (do mais importante ao menos):
  1. System prompt (do workflow step / agent)
  2. Documentos de referência (chunks do projeto)
  3. Artifact state (estado atual do artefato em construção)
  4. Mensagens recentes (últimas N)
  5. Mensagens antigas (truncadas primeiro se exceder limite)

Invariante de segurança:
  100% do conteúdo DEVE pertencer ao mesmo project_id.
  Violação → ContextIsolationError (severity: CRITICAL).
"""

import json
import logging
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import context_isolation_error, not_found_error
from app.db.tenant import TenantScope
from app.modules.documents.models import Document, DocumentChunk
from app.modules.engine.token_counter import estimate_tokens, estimate_messages_tokens
from app.modules.sessions.models import Message, Session
from app.modules.workflows.models import Agent, Workflow, WorkflowStep

logger = logging.getLogger(__name__)

# Limites configuráveis — podem migrar para settings no futuro
DEFAULT_MAX_CONTEXT_TOKENS = 8000
RECENT_MESSAGES_COUNT = 20


@dataclass
class ContextResult:
    """Resultado do Context Builder — pronto para envio ao LLM.

    Attributes:
        messages:       Lista de dicts no formato LLM [{"role": ..., "content": ...}]
        total_tokens:   Estimativa de tokens consumidos
        truncated:      True se mensagens antigas foram cortadas
        doc_count:      Quantidade de documentos incluídos
        project_id:     ID do projeto (para auditoria)
    """
    messages: list[dict[str, str]] = field(default_factory=list)
    total_tokens: int = 0
    truncated: bool = False
    doc_count: int = 0
    project_id: str = ""


async def build_context(
    scope: TenantScope,
    session_id: str,
    max_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS,
    user_name: str | None = None,
) -> ContextResult:
    """Monta o contexto completo para uma chamada ao LLM.

    Args:
        scope:       TenantScope com db e tenant_id
        session_id:  ID da sessão de elicitação
        max_tokens:  Limite máximo de tokens no contexto

    Returns:
        ContextResult com mensagens prontas para o LLM

    Raises:
        GuidedRecoveryError: se sessão não encontrada (404)
        GuidedRecoveryError: se dados de outro projeto detectados (500)
    """
    # 1. Carregar sessão com validação de tenant
    session = await scope.db.scalar(scope.where_id(Session, session_id))
    if not session:
        raise not_found_error("sessão")

    project_id = session.project_id

    # 2. Carregar workflow step e system prompt
    system_prompt = await _load_system_prompt(
        scope.db, session.workflow_id, session.workflow_position, user_name=user_name,
    )

    # 3. Carregar documentos de referência
    doc_chunks = await _load_document_chunks(scope, project_id)

    # 4. Carregar artifact_state
    artifact_state = session.artifact_state

    # 5. Carregar mensagens (todas, ordenadas)
    messages = await _load_messages(scope, session_id)

    # 6. Validar isolamento: tudo pertence ao mesmo project_id
    _validate_isolation(scope.tenant_id, project_id, doc_chunks, messages)

    # 7. Montar contexto com priorização e truncamento
    return _assemble_context(
        system_prompt=system_prompt,
        doc_chunks=doc_chunks,
        artifact_state=artifact_state,
        messages=messages,
        project_id=project_id,
        max_tokens=max_tokens,
    )


# ── Loaders internos ─────────────────────────────────────────────────────────


async def _load_system_prompt(
    db: AsyncSession,
    workflow_id: str,
    workflow_position: dict | None,
    user_name: str | None = None,
) -> str:
    """Carrega o system prompt do workflow step atual."""
    # Determinar posição atual (default: step 1)
    current_position = 1
    if workflow_position and "current_step" in workflow_position:
        current_position = workflow_position["current_step"]

    step = await db.scalar(
        select(WorkflowStep)
        .where(WorkflowStep.workflow_id == workflow_id)
        .where(WorkflowStep.position == current_position)
    )

    if not step:
        # Fallback: primeiro step
        step = await db.scalar(
            select(WorkflowStep)
            .where(WorkflowStep.workflow_id == workflow_id)
            .order_by(WorkflowStep.position.asc())
        )

    if not step:
        return "Você é um assistente de elicitação de requisitos."

    # Carregar agent prompt
    agent = await db.scalar(select(Agent).where(Agent.id == step.agent_id))
    agent_prompt = agent.system_prompt if agent else ""

    # Compor: agent prompt + step template
    parts = []
    if agent_prompt:
        parts.append(agent_prompt)
    if step.prompt_template:
        parts.append(step.prompt_template)

    combined = "\n\n".join(parts) if parts else "Você é um assistente de elicitação de requisitos."

    # Inject user name if available
    if user_name:
        combined += f"\n\nO usuário com quem você está conversando se chama {user_name}. Trate-o pelo nome."

    return combined


async def _load_document_chunks(
    scope: TenantScope,
    project_id: str,
) -> list[dict[str, str]]:
    """Carrega chunks dos documentos do projeto, filtrados por tenant."""
    stmt = (
        scope.select(DocumentChunk, DocumentChunk.project_id == project_id)
        .order_by(DocumentChunk.document_id, DocumentChunk.chunk_index)
    )
    rows = await scope.db.scalars(stmt)
    return [
        {"document_id": c.document_id, "project_id": c.project_id,
         "tenant_id": c.tenant_id, "content": c.content}
        for c in rows
    ]


async def _load_messages(
    scope: TenantScope,
    session_id: str,
) -> list[dict]:
    """Carrega todas as mensagens da sessão ordenadas por index."""
    stmt = (
        scope.select(Message, Message.session_id == session_id)
        .order_by(Message.message_index.asc())
    )
    rows = await scope.db.scalars(stmt)
    return [
        {"role": m.role, "content": m.content, "tenant_id": m.tenant_id,
         "session_id": m.session_id}
        for m in rows
    ]


# ── Validação de Isolamento ──────────────────────────────────────────────────


def _validate_isolation(
    tenant_id: str,
    project_id: str,
    doc_chunks: list[dict],
    messages: list[dict],
) -> None:
    """Valida que 100% dos dados pertencem ao tenant e projeto corretos.

    Esta é a última barreira antes de enviar dados ao LLM.
    Um vazamento aqui significaria expor dados de outro tenant à IA.
    """
    for chunk in doc_chunks:
        if chunk.get("tenant_id") != tenant_id:
            logger.critical(
                "ISOLATION VIOLATION: document chunk pertence a outro tenant",
                extra={"expected_tenant": tenant_id, "chunk_tenant": chunk.get("tenant_id")},
            )
            raise context_isolation_error("document chunk cross-tenant detectado")
        if chunk.get("project_id") != project_id:
            logger.critical(
                "ISOLATION VIOLATION: document chunk pertence a outro projeto",
                extra={"expected_project": project_id, "chunk_project": chunk.get("project_id")},
            )
            raise context_isolation_error("document chunk cross-project detectado")

    for msg in messages:
        if msg.get("tenant_id") != tenant_id:
            logger.critical(
                "ISOLATION VIOLATION: message pertence a outro tenant",
                extra={"expected_tenant": tenant_id, "msg_tenant": msg.get("tenant_id")},
            )
            raise context_isolation_error("message cross-tenant detectada")


# ── Montagem com Priorização e Truncamento ───────────────────────────────────


def _assemble_context(
    system_prompt: str,
    doc_chunks: list[dict[str, str]],
    artifact_state: dict | None,
    messages: list[dict],
    project_id: str,
    max_tokens: int,
) -> ContextResult:
    """Monta as mensagens para o LLM respeitando o limite de tokens.

    Prioridade (nunca truncada → truncada primeiro):
      1. System prompt          — NUNCA truncado
      2. Docs de referência     — NUNCA truncado (assumindo que cabem)
      3. Artifact state         — NUNCA truncado
      4. Mensagens recentes     — últimas N, preservadas
      5. Mensagens antigas      — TRUNCADAS PRIMEIRO se exceder limite
    """
    result_messages: list[dict[str, str]] = []
    truncated = False

    # ── Layer 1: System prompt (obrigatório) ──
    result_messages.append({"role": "system", "content": system_prompt})

    # ── Layer 2: Documentos de referência ──
    if doc_chunks:
        doc_text_parts = []
        for chunk in doc_chunks:
            doc_text_parts.append(chunk["content"])
        doc_context = (
            "=== DOCUMENTOS DE REFERÊNCIA DO PROJETO ===\n\n"
            + "\n\n---\n\n".join(doc_text_parts)
        )
        result_messages.append({"role": "system", "content": doc_context})

    # ── Layer 3: Artifact state ──
    if artifact_state:
        artifact_text = (
            "=== ESTADO ATUAL DO ARTEFATO ===\n\n"
            + json.dumps(artifact_state, ensure_ascii=False, indent=2)
        )
        result_messages.append({"role": "system", "content": artifact_text})

    # Calcular tokens fixos (layers 1-3)
    fixed_tokens = estimate_messages_tokens(result_messages)

    # ── Layers 4-5: Mensagens (com truncamento) ──
    remaining_tokens = max_tokens - fixed_tokens
    conversation_messages = [{"role": m["role"], "content": m["content"]} for m in messages]

    if remaining_tokens <= 0:
        # Sem espaço — só as layers fixas
        truncated = len(conversation_messages) > 0
    else:
        total_msg_tokens = estimate_messages_tokens(conversation_messages)

        if total_msg_tokens <= remaining_tokens:
            # Tudo cabe
            result_messages.extend(conversation_messages)
        else:
            # Truncar mensagens antigas (manter as recentes)
            truncated = True
            kept_messages = _truncate_old_messages(conversation_messages, remaining_tokens)
            result_messages.extend(kept_messages)

    return ContextResult(
        messages=result_messages,
        total_tokens=estimate_messages_tokens(result_messages),
        truncated=truncated,
        doc_count=len(doc_chunks),
        project_id=project_id,
    )


def _truncate_old_messages(
    messages: list[dict[str, str]],
    max_tokens: int,
) -> list[dict[str, str]]:
    """Remove mensagens do INÍCIO (mais antigas) até caber no limite.

    Preserva as mensagens mais recentes que cabem no budget.
    """
    # Tentar de trás para frente: incluir as mais recentes primeiro
    kept: list[dict[str, str]] = []
    used_tokens = 2  # overhead de conversa

    for msg in reversed(messages):
        msg_tokens = estimate_tokens(msg["content"]) + 4  # overhead por msg
        if used_tokens + msg_tokens <= max_tokens:
            kept.insert(0, msg)
            used_tokens += msg_tokens
        else:
            break  # não cabe mais nenhuma mensagem antiga

    return kept
