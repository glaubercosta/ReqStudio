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
from collections.abc import AsyncGenerator

from sqlalchemy import func, select

from app.core.config import settings
from app.core.exceptions import (
    not_found_error,
    session_already_started_error,
    session_not_paused_error,
)
from app.db.tenant import TenantScope
from app.integrations.llm_client import CompletionChunk, stream_completion
from app.modules.auth.models import User
from app.modules.engine.context_builder import build_context
from app.modules.projects.models import Project
from app.modules.sessions.models import (
    SESSION_STATUS_ACTIVE,
    SESSION_STATUS_COMPLETED,
    SESSION_STATUS_PAUSED,
    Message,
    Session,
)
from app.modules.workflows.models import Agent, WorkflowStep
from app.seeds.seed_workflows import (
    COMPLETION_TEMPLATE as _COMPLETION_TEMPLATE,
)
from app.seeds.seed_workflows import (
    KICKSTART_TEMPLATE as _KICKSTART_TEMPLATE,
)
from app.seeds.seed_workflows import (
    RETURN_GREETING_TEMPLATE as _RETURN_GREETING_TEMPLATE,
)
from app.seeds.seed_workflows import (
    RETURN_GREETING_TEMPLATE_NO_SUMMARIES as _RETURN_GREETING_TEMPLATE_NO_SUMMARIES,
)
from app.seeds.seed_workflows import (
    STEP_NAMES as _STEP_NAMES,
)
from app.seeds.seed_workflows import (
    TRANSITION_TEMPLATE as _TRANSITION_TEMPLATE,
)

logger = logging.getLogger(__name__)


async def elicit(
    scope: TenantScope,
    session_id: str,
    user_message: str,
    user_name: str | None = None,
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

    # ── Step 3: Resolve display name (prefer explicit display name over email prefix) ──
    resolved_user_name = _resolve_user_display_name(user_name)
    if not resolved_user_name:
        # Fallback defensivo para fluxos antigos que não repassam user_name no endpoint
        user = await scope.db.scalar(select(User).where(User.tenant_id == scope.tenant_id))
        if user:
            raw_display_name = getattr(user, "display_name", None)
            resolved_user_name = _resolve_user_display_name(raw_display_name or user.email)

    # ── Step 4: Context Builder ──
    context = await build_context(
        scope,
        session_id,
        max_tokens=settings.LLM_MAX_CONTEXT_TOKENS,
        user_name=resolved_user_name,
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


async def kickstart(
    scope: TenantScope,
    session_id: str,
) -> AsyncGenerator[CompletionChunk, None]:
    """Gera a mensagem de abertura proativa da Mary (Story 7.1).

    Deve ser chamado apenas em sessões sem mensagens (primeiro acesso).
    NÃO avança workflow_position — kickstart não conta como par user+assistant.

    Yields:
        CompletionChunk com conteúdo parcial da IA.

    Raises:
        GuidedRecoveryError(404): sessão não encontrada / outro tenant
        GuidedRecoveryError(409): sessão já possui mensagens (SESSION_ALREADY_STARTED)
    """
    # ── Step 1: Validar sessão ──
    session = await scope.db.scalar(scope.where_id(Session, session_id))
    if not session:
        raise not_found_error("sessão")

    # ── Step 2: Idempotência — só executa se sessão está vazia ──
    next_idx = await _next_message_index(scope, session_id)
    if next_idx != 0:
        raise session_already_started_error()

    # ── Step 3: Carregar system_prompt do agente ──
    system_prompt = await _load_agent_system_prompt(scope.db, session.workflow_id)

    # ── Step 4: Montar messages para kickstart ──
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": _KICKSTART_TEMPLATE},
    ]

    # ── Step 5: Stream LLM + Step 6: Persistir resposta completa ──
    full_response = ""

    try:
        async for chunk in stream_completion(messages):
            full_response += chunk.content

            if chunk.done:
                metrics = chunk.metrics if chunk.metrics else None
                assistant_msg = Message(
                    session_id=session_id,
                    tenant_id=scope.tenant_id,
                    role="assistant",
                    content=full_response,
                    message_index=0,
                    input_tokens=metrics.input_tokens if metrics else None,
                    output_tokens=metrics.output_tokens if metrics else None,
                    cost_usd=metrics.cost_usd if metrics else None,
                    latency_ms=metrics.latency_ms if metrics else None,
                    model=metrics.model if metrics else None,
                )
                scope.db.add(assistant_msg)
                await scope.db.commit()

                logger.info(
                    "Kickstart message persisted",
                    extra={"session_id": session_id, "response_length": len(full_response)},
                )

            yield chunk
    except Exception:
        await scope.db.rollback()
        raise


async def return_greeting(
    scope: TenantScope,
    session_id: str,
) -> AsyncGenerator[CompletionChunk, None]:
    """Gera saudação de retorno ao projeto para sessão pausada (Story 7.3).

    Muda status para active, gera greeting via LLM com contexto das etapas
    já concluídas e persiste mensagem como role="assistant". Se o stream
    falhar, o status é revertido para paused para evitar estado inconsistente.

    Yields:
        CompletionChunk com conteúdo parcial da IA.

    Raises:
        GuidedRecoveryError(404): sessão não encontrada / outro tenant
        GuidedRecoveryError(409): sessão não está pausada (SESSION_NOT_PAUSED)
    """
    # ── Step 1: Validar sessão ──
    session = await scope.db.scalar(scope.where_id(Session, session_id))
    if not session:
        raise not_found_error("sessão")

    # ── Step 2: Verificar status == paused ──
    if session.status != SESSION_STATUS_PAUSED:
        raise session_not_paused_error()

    # ── Step 3: Mudar status para active imediatamente ──
    session.status = SESSION_STATUS_ACTIVE

    # ── Step 4: Montar prompt com contexto das etapas concluídas ──
    position = session.workflow_position or {}
    summaries = position.get("step_summaries") or {}
    current_step = position.get("current_step", 1)
    next_step_name = _STEP_NAMES.get(current_step, "próxima etapa")

    if summaries:
        summary_lines = []
        for k, v in sorted(summaries.items(), key=lambda x: _safe_int(x[0])):
            step_num = _safe_int(k)
            if step_num is not None and step_num in _STEP_NAMES:
                summary_lines.append(f"- {_STEP_NAMES[step_num]}: {v}")
        summaries_text = "\n".join(summary_lines)
        context_block = f"Etapas já concluídas:\n{summaries_text}\n\n"
        progress_instruction = (
            "liste brevemente as etapas concluídas usando os resumos acima"
        )
        prompt = _RETURN_GREETING_TEMPLATE.format(
            context_block=context_block,
            progress_instruction=progress_instruction,
            next_step_name=next_step_name,
        )
    else:
        prompt = _RETURN_GREETING_TEMPLATE_NO_SUMMARIES.format(
            next_step_name=next_step_name,
        )

    system_prompt = await _load_agent_system_prompt(scope.db, session.workflow_id)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    # ── Step 5: Stream LLM + Step 6: Persistir resposta completa ──
    full_response = ""

    try:
        async for chunk in stream_completion(messages):
            full_response += chunk.content

            if chunk.done:
                metrics = chunk.metrics if chunk.metrics else None
                assistant_msg = Message(
                    session_id=session_id,
                    tenant_id=scope.tenant_id,
                    role="assistant",
                    content=full_response,
                    message_index=await _next_message_index(scope, session_id),
                    input_tokens=metrics.input_tokens if metrics else None,
                    output_tokens=metrics.output_tokens if metrics else None,
                    cost_usd=metrics.cost_usd if metrics else None,
                    latency_ms=metrics.latency_ms if metrics else None,
                    model=metrics.model if metrics else None,
                )
                scope.db.add(assistant_msg)
                await scope.db.commit()

                logger.info(
                    "Return greeting persisted",
                    extra={"session_id": session_id, "response_length": len(full_response)},
                )

            yield chunk
    except Exception:
        # Reverter status para paused: estado consistente se stream falhou
        await scope.db.rollback()
        session_after_rollback = await scope.db.scalar(scope.where_id(Session, session_id))
        if session_after_rollback and session_after_rollback.status == SESSION_STATUS_ACTIVE:
            session_after_rollback.status = SESSION_STATUS_PAUSED
            await scope.db.commit()
        raise


# ── Helpers internos ──────────────────────────────────────────────────────────


async def _load_agent_system_prompt(db, workflow_id: str) -> str:
    """Carrega o system_prompt do agente associado ao primeiro step do workflow."""
    step = await db.scalar(
        select(WorkflowStep)
        .where(WorkflowStep.workflow_id == workflow_id)
        .order_by(WorkflowStep.position.asc())
    )
    if not step:
        return "Você é Mary, analista sênior de requisitos do ReqStudio."
    agent = await db.scalar(select(Agent).where(Agent.id == step.agent_id))
    _fallback = "Você é Mary, analista sênior de requisitos do ReqStudio."
    return agent.system_prompt if agent else _fallback


async def _next_message_index(scope: TenantScope, session_id: str) -> int:
    """Calcula o próximo message_index para a sessão."""
    count = (
        await scope.db.scalar(
            select(func.count()).select_from(Message).where(Message.session_id == session_id)
        )
        or 0
    )
    return count


async def _advance_workflow(scope: TenantScope, session: Session) -> None:
    """Avança a posição do workflow e gera mensagem de transição via LLM.

    Lógica MVP simplificada: cada par user+assistant = 1 step concluído.
    AC 4: o incremento de current_step é persistido ANTES da chamada LLM
    de transição (commit atômico). Se o LLM falhar, o avanço permanece e o
    erro propaga; o usuário pode reenviar para regenerar a mensagem.
    """
    position = dict(session.workflow_position or {"current_step": 1})
    current_step = position.get("current_step", 1)

    total_steps = (
        await scope.db.scalar(
            select(func.count())
            .select_from(WorkflowStep)
            .where(WorkflowStep.workflow_id == session.workflow_id)
        )
        or 0
    )

    system_prompt = await _load_agent_system_prompt(scope.db, session.workflow_id)

    if current_step < total_steps:
        new_step = current_step + 1
        new_position = dict(position)
        new_position["current_step"] = new_step
        session.workflow_position = new_position
        await scope.db.commit()  # AC 4: estado atômico antes do LLM

        transition_prompt = _TRANSITION_TEMPLATE.format(
            completed_step_num=current_step,
            completed_step_name=_STEP_NAMES.get(current_step, str(current_step)),
            next_step_num=new_step,
            next_step_name=_STEP_NAMES.get(new_step, str(new_step)),
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transition_prompt},
        ]
        full_transition = ""
        try:
            async for chunk in stream_completion(messages):
                full_transition += chunk.content
        except Exception:
            logger.exception(
                "Transition LLM failed after step advance",
                extra={"session_id": session.id, "new_step": new_step},
            )
            raise

        summary = _extract_summary(full_transition)
        summaries = dict(new_position.get("step_summaries") or {})
        summaries[str(current_step)] = summary
        updated_position = dict(new_position)
        updated_position["step_summaries"] = summaries
        session.workflow_position = updated_position

        msg_index = await _next_message_index(scope, session.id)
        transition_msg = Message(
            session_id=session.id,
            tenant_id=scope.tenant_id,
            role="assistant",
            content=_strip_summary_tag(full_transition),
            message_index=msg_index,
        )
        scope.db.add(transition_msg)

        logger.info(
            "Workflow advanced",
            extra={"session_id": session.id, "new_step": new_step, "total": total_steps},
        )

    elif current_step >= total_steps:
        new_position = dict(position)
        summaries = dict(new_position.get("step_summaries") or {})

        summary_lines = []
        for k, v in sorted(summaries.items(), key=lambda x: _safe_int(x[0]) or 0):
            step_num = _safe_int(k)
            label = _STEP_NAMES.get(step_num, k) if step_num is not None else k
            summary_lines.append(f"Etapa {k} — {label}: {v}")
        summaries_text = "\n".join(summary_lines)

        completion_prompt = _COMPLETION_TEMPLATE.format(summaries_text=summaries_text)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": completion_prompt},
        ]
        full_completion = ""
        try:
            async for chunk in stream_completion(messages):
                full_completion += chunk.content
        except Exception:
            logger.exception(
                "Completion LLM failed",
                extra={"session_id": session.id, "current_step": current_step},
            )
            raise

        summary = _extract_summary(full_completion)
        summaries[str(current_step)] = summary
        new_position["step_summaries"] = summaries
        new_position["current_step"] = total_steps
        new_position["completed"] = True

        msg_index = await _next_message_index(scope, session.id)
        completion_msg = Message(
            session_id=session.id,
            tenant_id=scope.tenant_id,
            role="assistant",
            content=_strip_summary_tag(full_completion),
            message_index=msg_index,
        )
        scope.db.add(completion_msg)

        session.workflow_position = new_position
        session.status = SESSION_STATUS_COMPLETED

        logger.info(
            "Workflow completed",
            extra={"session_id": session.id, "total_steps": total_steps},
        )


def _safe_int(value) -> int | None:
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _normalize_summary_line(raw_line: str) -> str:
    return raw_line.strip().strip("*").strip()


_SUMMARY_TAG = "[RESUMO]:"
_SUMMARY_MAX_CHARS = 200


def _extract_summary(response: str) -> str:
    """Extrai resumo de 1 linha da resposta do LLM (tag [RESUMO]:).

    Robustez:
    - Procura a tag em qualquer linha (não só a primeira)
    - Tolera markdown de ênfase (**, *) ao redor da tag
    - Limita o resumo a _SUMMARY_MAX_CHARS

    Fallback: primeiros _SUMMARY_MAX_CHARS chars se tag ausente.
    """
    if not response or not response.strip():
        return ""

    for raw_line in response.splitlines():
        normalized = _normalize_summary_line(raw_line)
        if normalized.startswith(_SUMMARY_TAG):
            return normalized[len(_SUMMARY_TAG):].strip()[:_SUMMARY_MAX_CHARS]

    return response.strip()[:_SUMMARY_MAX_CHARS]


def _strip_summary_tag(response: str) -> str:
    """Remove a linha contendo [RESUMO]: para não vazar metadado ao usuário."""
    if not response:
        return response
    kept = [
        line
        for line in response.splitlines()
        if not _normalize_summary_line(line).startswith(_SUMMARY_TAG)
    ]
    return "\n".join(kept).rstrip()


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
        "context": step >= 1,
        "stakeholders": step >= 2,
        "goals": step >= 3,
        "flows": step >= 4,
        "nfr": step >= 5,
        "review": False,  # Manual
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


def _resolve_user_display_name(raw_name: str | None) -> str | None:
    """Normaliza nome de exibição para uso no prompt.

    Regras:
    - Prioriza nome explícito quando enviado pelo endpoint (display name).
    - Se vier e-mail, remove domínio e tenta humanizar o prefixo.
    - Retorna None para entradas vazias.
    """
    if not raw_name:
        return None

    candidate = raw_name.strip()
    if not candidate:
        return None

    if "@" in candidate:
        candidate = candidate.split("@", 1)[0]

    candidate = candidate.replace(".", " ").replace("_", " ").replace("-", " ")
    normalized = " ".join(part for part in candidate.split() if part).strip()
    if not normalized:
        return None

    return normalized.title()
