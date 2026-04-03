"""Elicitation Engine — orquestra sessão de elicitação com workflow (Story 5.4).

Pipeline por mensagem do usuário:
  1. Write-ahead save: persiste mensagem ANTES de chamar o LLM
  2. Load workflow position
  3. Context Builder: monta prompt com priorização e isolamento
  4. LLM stream: gera resposta via LiteLLM
  5. Save response: persiste resposta completa ao final do stream
  6. Update session: workflow_position + artifact_state

Invariante de resiliência (architecture.md §486-489):
  Mensagem do user salva ANTES do LLM. Se crash, user re-envia.
  Resposta salva COMPLETA ao final, independente do client estar conectado.
"""

import logging
from typing import AsyncGenerator

from sqlalchemy import func, select

from app.core.config import settings
from app.core.exceptions import not_found_error
from app.db.tenant import TenantScope
from app.integrations.llm_client import CompletionChunk, stream_completion
from app.modules.engine.context_builder import build_context
from app.modules.sessions.models import Message, Session, SESSION_STATUS_COMPLETED
from app.modules.auth.models import User
from app.modules.workflows.models import WorkflowStep
from app.modules.projects.models import Project

logger = logging.getLogger(__name__)


async def elicit(
    scope: TenantScope,
    session_id: str,
    user_message: str,
) -> AsyncGenerator[CompletionChunk, None]:
    """Executa um ciclo de elicitação: recebe input do user, retorna stream da IA.

    Args:
        scope:          TenantScope com db e tenant_id
        session_id:     ID da sessão ativa
        user_message:   Texto enviado pelo usuário

    Yields:
        CompletionChunk com conteúdo parcial da IA.
        Último chunk: done=True com métricas.

    Raises:
        GuidedRecoveryError(404): sessão não encontrada / outro tenant
        GuidedRecoveryError(500): violação de isolamento no contexto
        GuidedRecoveryError(503/504): LLM indisponível/timeout
    """
    # ── Step 1: Validar sessão ──
    session = await scope.db.scalar(scope.where_id(Session, session_id))
    if not session:
        raise not_found_error("sessão")

    # ── Step 2: Write-ahead save (mensagem do user ANTES do LLM) ──
    user_msg_index = await _next_message_index(scope, session_id)
    user_msg = Message(
        session_id=session_id,
        tenant_id=scope.tenant_id,
        role="user",
        content=user_message,
        message_index=user_msg_index,
    )
    scope.db.add(user_msg)
    await scope.db.commit()
    await scope.db.refresh(user_msg)

    logger.info(
        "Write-ahead save: user message persisted",
        extra={"session_id": session_id, "message_index": user_msg_index},
    )

    # ── Step 3: Load user name ──
    user = await scope.db.scalar(
        select(User).where(User.tenant_id == scope.tenant_id)
    )
    user_name = user.email.split('@')[0].replace('.', ' ').title() if user else None

    # ── Step 4: Context Builder ──
    context = await build_context(
        scope,
        session_id,
        max_tokens=settings.LLM_MAX_CONTEXT_TOKENS,
        user_name=user_name,
    )

    logger.info(
        "Context built",
        extra={
            "session_id": session_id,
            "total_tokens": context.total_tokens,
            "truncated": context.truncated,
            "doc_count": context.doc_count,
        },
    )

    # ── Step 4: LLM stream + Step 5: Collect full response ──
    full_response = ""

    async for chunk in stream_completion(context.messages):
        full_response += chunk.content

        if chunk.done:
            # ── Step 5: Save response (mensagem completa da IA) ──
            assistant_msg_index = await _next_message_index(scope, session_id)
            metrics = chunk.metrics if chunk.metrics else None
            assistant_msg = Message(
                session_id=session_id,
                tenant_id=scope.tenant_id,
                role="assistant",
                content=full_response,
                message_index=assistant_msg_index,
                input_tokens=metrics.input_tokens if metrics else None,
                output_tokens=metrics.output_tokens if metrics else None,
                cost_usd=metrics.cost_usd if metrics else None,
                latency_ms=metrics.latency_ms if metrics else None,
                model=metrics.model if metrics else None,
            )
            scope.db.add(assistant_msg)

            # ── Step 6: Update workflow position e progress_summary ──
            await _advance_workflow(scope, session)
            await _update_progress_summary(scope, session)
            await scope.db.commit()

            logger.info(
                "Elicitation cycle complete",
                extra={
                    "session_id": session_id,
                    "response_length": len(full_response),
                    "metrics": {
                        "input_tokens": chunk.metrics.input_tokens if chunk.metrics else 0,
                        "output_tokens": chunk.metrics.output_tokens if chunk.metrics else 0,
                        "cost_usd": chunk.metrics.cost_usd if chunk.metrics else 0,
                    },
                },
            )

        yield chunk


# ── Helpers internos ──────────────────────────────────────────────────────────


async def _next_message_index(scope: TenantScope, session_id: str) -> int:
    """Calcula o próximo message_index para a sessão."""
    count = await scope.db.scalar(
        select(func.count())
        .select_from(Message)
        .where(Message.session_id == session_id)
    ) or 0
    return count


async def _advance_workflow(scope: TenantScope, session: Session) -> None:
    """Avança a posição do workflow se o step atual foi concluído.

    Lógica MVP simplificada: cada par user+assistant = 1 step concluído.
    V2: lógica condicional baseada na resposta da IA (ex: "coverage completa").
    """
    position = session.workflow_position or {"current_step": 1}
    current_step = position.get("current_step", 1)

    # Verificar se existe próximo step
    total_steps = await scope.db.scalar(
        select(func.count())
        .select_from(WorkflowStep)
        .where(WorkflowStep.workflow_id == session.workflow_id)
    ) or 0

    if current_step < total_steps:
        position["current_step"] = current_step + 1
        session.workflow_position = position
        logger.info(
            "Workflow advanced",
            extra={"session_id": session.id, "new_step": current_step + 1, "total": total_steps},
        )
    elif current_step >= total_steps:
        # Último step — marcar sessão como completed
        position["current_step"] = total_steps
        position["completed"] = True
        session.workflow_position = position
        session.status = SESSION_STATUS_COMPLETED
        logger.info(
            "Workflow completed",
            extra={"session_id": session.id, "total_steps": total_steps},
        )


def _compute_progress_summary(workflow_position: dict | None) -> dict:
    """Deriva progress_summary a partir da posição atual no workflow.

    Mapeamento simples step → checklist (refinado no Epic 6).
    Invariante: garante que 'step' seja um inteiro válido.
    """
    raw_step = (workflow_position or {}).get("current_step", 0)
    try:
        step = int(raw_step)
    except (ValueError, TypeError):
        step = 0

    return {
        "context":      step >= 1,
        "stakeholders": step >= 2,
        "goals":        step >= 3,
        "flows":        step >= 4,
        "nfr":          step >= 5,
        "review":       False,  # Manual
    }


async def _update_progress_summary(scope: TenantScope, session: Session) -> None:
    """Atualiza progress_summary do projeto baseado na posição do workflow.

    Isolamento garantido: filtra por scope.tenant_id via scope.where_id.
    """
    project = await scope.db.scalar(scope.where_id(Project, session.project_id))
    if not project:
        logger.warning(
            "Cannot update progress_summary: project not found",
            extra={"session_id": session.id, "project_id": session.project_id},
        )
        return

    project.progress_summary = _compute_progress_summary(session.workflow_position)
    logger.info(
        "progress_summary updated",
        extra={
            "project_id": project.id,
            "progress": project.progress_summary,
        },
    )
