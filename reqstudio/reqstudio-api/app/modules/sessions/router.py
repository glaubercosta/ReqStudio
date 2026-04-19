"""Sessions router — CRUD endpoints + SSE streaming (Stories 5.1, 5.5)."""

import json
import logging

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.core.dependencies import get_current_user
from app.core.exceptions import GuidedRecoveryError
from app.db.tenant import TenantScope, get_tenant_scope
from app.modules.auth.models import User
from app.modules.engine.elicitation import elicit, kickstart, return_greeting
from app.modules.sessions import service
from app.modules.sessions.schemas import (
    MessageCreate,
    MessageListResponse,
    MessageResponse,
    SessionCreateBody,
    SessionListResponse,
    SessionResponse,
    SessionUpdate,
)
from app.schemas.response import ApiResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["sessions"])


def _sse_error_payload(exc: Exception) -> str:
    """Serializa erro SSE preservando GuidedRecoveryError; sanitiza demais.

    GuidedRecoveryError já é estruturado e seguro para o usuário.
    Outras exceções são logadas como 500 e devolvidas com mensagem genérica
    para não vazar internals (stack traces, queries, paths) via SSE.
    """
    if isinstance(exc, GuidedRecoveryError):
        return json.dumps(
            {"code": str(exc.code), "message": exc.message},
            ensure_ascii=False,
        )
    logger.exception("Unhandled error in SSE stream")
    return json.dumps(
        {"code": "INTERNAL_ERROR", "message": "Erro interno. Tente novamente."},
        ensure_ascii=False,
    )


# ── Session Routes ────────────────────────────────────────────────────────────


@router.post(
    "/projects/{project_id}/sessions",
    response_model=ApiResponse[SessionResponse],
    status_code=201,
)
async def create_session(
    project_id: str,
    payload: SessionCreateBody | None = None,
    scope: TenantScope = Depends(get_tenant_scope),
) -> ApiResponse[SessionResponse]:
    """Cria uma sessão de elicitação no projeto."""
    workflow_id = payload.workflow_id if payload else None
    result = await service.create_session(scope, project_id, workflow_id)
    return ApiResponse(data=result)


@router.get(
    "/projects/{project_id}/sessions",
    response_model=ApiResponse[SessionListResponse],
)
async def list_sessions(
    project_id: str,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    status: list[str] | None = Query(
        default=None, description="Filtrar por status (ex: active,paused)"
    ),
    scope: TenantScope = Depends(get_tenant_scope),
) -> ApiResponse[SessionListResponse]:
    """Lista sessões de um projeto com paginação. Aceita filtro opcional de status."""
    result = await service.list_sessions(
        scope, project_id=project_id, page=page, size=size, status=status
    )
    return ApiResponse(data=result)


@router.get(
    "/sessions/{session_id}",
    response_model=ApiResponse[SessionResponse],
)
async def get_session(
    session_id: str,
    scope: TenantScope = Depends(get_tenant_scope),
) -> ApiResponse[SessionResponse]:
    """Retorna detalhes de uma sessão."""
    result = await service.get_session(scope, session_id)
    return ApiResponse(data=result)


@router.patch(
    "/sessions/{session_id}",
    response_model=ApiResponse[SessionResponse],
)
async def update_session(
    session_id: str,
    payload: SessionUpdate,
    scope: TenantScope = Depends(get_tenant_scope),
) -> ApiResponse[SessionResponse]:
    """Atualiza status da sessão (pause/resume/complete)."""
    result = await service.update_session(scope, session_id, payload)
    return ApiResponse(data=result)


# ── Message Routes ────────────────────────────────────────────────────────────


@router.post(
    "/sessions/{session_id}/messages",
    response_model=ApiResponse[MessageResponse],
    status_code=201,
)
async def add_message(
    session_id: str,
    payload: MessageCreate,
    scope: TenantScope = Depends(get_tenant_scope),
) -> ApiResponse[MessageResponse]:
    """Envia uma mensagem para uma sessão (sem streaming)."""
    result = await service.add_message(scope, session_id, payload)
    return ApiResponse(data=result)


@router.get(
    "/sessions/{session_id}/messages",
    response_model=ApiResponse[MessageListResponse],
)
async def list_messages(
    session_id: str,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    scope: TenantScope = Depends(get_tenant_scope),
) -> ApiResponse[MessageListResponse]:
    """Lista mensagens de uma sessão com paginação."""
    result = await service.list_messages(scope, session_id, page=page, size=size)
    return ApiResponse(data=result)


# ── SSE Streaming (Story 5.5) ────────────────────────────────────────────────


@router.post("/sessions/{session_id}/kickstart")
async def kickstart_stream(
    session_id: str,
    scope: TenantScope = Depends(get_tenant_scope),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Endpoint SSE: gera mensagem proativa de abertura da Mary (Story 7.1).

    Retorna `text/event-stream` com events:
      - `event: message` — chunk parcial da IA
      - `event: done` — conclusão com métricas
      - `event: error` — erro (sessão já iniciada, LLM unavailable, etc.)
    """

    async def _sse_generator():
        try:
            async for chunk in kickstart(scope, session_id):
                if chunk.done:
                    m = chunk.metrics
                    data = json.dumps(
                        {
                            "content": "",
                            "done": True,
                            "metrics": {
                                "input_tokens": m.input_tokens if m else 0,
                                "output_tokens": m.output_tokens if m else 0,
                                "cost_usd": m.cost_usd if m else 0,
                                "latency_ms": round(m.latency_ms, 2) if m else 0,
                            }
                            if m
                            else None,
                        },
                        ensure_ascii=False,
                    )
                    yield f"event: done\ndata: {data}\n\n"
                else:
                    data = json.dumps(
                        {"content": chunk.content, "done": False},
                        ensure_ascii=False,
                    )
                    yield f"event: message\ndata: {data}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {_sse_error_payload(e)}\n\n"

    return StreamingResponse(
        _sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/sessions/{session_id}/return-greeting")
async def return_greeting_stream(
    session_id: str,
    scope: TenantScope = Depends(get_tenant_scope),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Endpoint SSE: gera saudação de retorno para sessão pausada (Story 7.3).

    Retorna `text/event-stream` com events:
      - `event: message` — chunk parcial da IA
      - `event: done` — conclusão com métricas
      - `event: error` — erro (sessão não pausada, LLM unavailable, etc.)
    """

    async def _sse_generator():
        try:
            async for chunk in return_greeting(scope, session_id):
                if chunk.done:
                    m = chunk.metrics
                    data = json.dumps(
                        {
                            "content": "",
                            "done": True,
                            "metrics": {
                                "input_tokens": m.input_tokens if m else 0,
                                "output_tokens": m.output_tokens if m else 0,
                                "cost_usd": m.cost_usd if m else 0,
                                "latency_ms": round(m.latency_ms, 2) if m else 0,
                            }
                            if m
                            else None,
                        },
                        ensure_ascii=False,
                    )
                    yield f"event: done\ndata: {data}\n\n"
                else:
                    data = json.dumps(
                        {"content": chunk.content, "done": False},
                        ensure_ascii=False,
                    )
                    yield f"event: message\ndata: {data}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {_sse_error_payload(e)}\n\n"

    return StreamingResponse(
        _sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/sessions/{session_id}/elicit")
async def elicit_stream(
    session_id: str,
    payload: MessageCreate,
    scope: TenantScope = Depends(get_tenant_scope),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Endpoint SSE: envia mensagem e recebe resposta da IA em streaming.

    Retorna `text/event-stream` com events:
      - `event: message` — chunk parcial da IA
      - `event: done` — conclusão com métricas
      - `event: error` — erro (LLM unavailable, timeout, etc.)
    """

    async def _sse_generator():
        try:
            async for chunk in elicit(
                scope,
                session_id,
                payload.content,
                user_name=getattr(current_user, "display_name", None) or current_user.email,
            ):
                if chunk.done:
                    data = json.dumps(
                        {
                            "content": "",
                            "done": True,
                            "metrics": {
                                "input_tokens": chunk.metrics.input_tokens if chunk.metrics else 0,
                                "output_tokens": chunk.metrics.output_tokens
                                if chunk.metrics
                                else 0,
                                "cost_usd": chunk.metrics.cost_usd if chunk.metrics else 0,
                                "latency_ms": round(chunk.metrics.latency_ms, 2)
                                if chunk.metrics
                                else 0,
                            }
                            if chunk.metrics
                            else None,
                        },
                        ensure_ascii=False,
                    )
                    yield f"event: done\ndata: {data}\n\n"
                else:
                    data = json.dumps(
                        {
                            "content": chunk.content,
                            "done": False,
                        },
                        ensure_ascii=False,
                    )
                    yield f"event: message\ndata: {data}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {_sse_error_payload(e)}\n\n"

    return StreamingResponse(
        _sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
