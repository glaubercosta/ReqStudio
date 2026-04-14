"""Session and Message business logic with TenantScope enforcement (Story 5.1).

Every function receives TenantScope as first argument — never raw AsyncSession.
project_id ownership is validated on session creation to prevent cross-tenant binding.
"""

import math
from datetime import datetime

from sqlalchemy import func, select

from app.core.exceptions import not_found_error
from app.db.tenant import TenantScope
from app.modules.projects.models import Project
from app.modules.sessions.models import SESSION_STATUS_ACTIVE, Message, Session
from app.modules.sessions.schemas import (
    MessageCreate,
    MessageListResponse,
    MessageResponse,
    SessionListResponse,
    SessionResponse,
    SessionUpdate,
)
from app.modules.workflows.models import Workflow

# ── Default Workflow ──────────────────────────────────────────────────────────

DEFAULT_WORKFLOW_NAME = "elicitation-briefing"


async def _resolve_workflow_id(scope: TenantScope, workflow_id: str | None) -> str:
    """Resolve o workflow_id, usando o briefing como default."""
    if workflow_id:
        wf = await scope.db.scalar(select(Workflow).where(Workflow.id == workflow_id))
        if not wf:
            raise not_found_error("workflow")
        return wf.id

    wf = await scope.db.scalar(select(Workflow).where(Workflow.name == DEFAULT_WORKFLOW_NAME))
    if not wf:
        raise not_found_error("workflow")
    return wf.id


# ── Sessions ──────────────────────────────────────────────────────────────────


async def create_session(
    scope: TenantScope,
    project_id: str,
    workflow_id: str | None = None,
) -> SessionResponse:
    """Cria uma sessão vinculada a um projeto.

    Valida que o project_id pertence ao tenant antes de criar,
    prevenindo vinculação a projetos de outros tenants.
    """
    # Validar ownership do projeto
    project = await scope.db.scalar(scope.where_id(Project, project_id))
    if not project:
        raise not_found_error("projeto")

    resolved_workflow_id = await _resolve_workflow_id(scope, workflow_id)

    session = Session(
        project_id=project_id,
        workflow_id=resolved_workflow_id,
        tenant_id=scope.tenant_id,
        status=SESSION_STATUS_ACTIVE,
    )
    scope.db.add(session)
    await scope.db.commit()
    await scope.db.refresh(session)

    return SessionResponse(
        **{k: getattr(session, k) for k in SessionResponse.model_fields if k != "message_count"},
        message_count=0,
    )


async def list_sessions(
    scope: TenantScope,
    project_id: str,
    page: int = 1,
    size: int = 20,
    status: list[str] | None = None,
) -> SessionListResponse:
    """Lista sessões de um projeto do tenant com paginação.

    Args:
        status: Opcional. Filtra por lista de status (ex: ['active', 'paused']).
    """
    offset = (page - 1) * size

    base_where = (Session.tenant_id == scope.tenant_id, Session.project_id == project_id)

    count_stmt = select(func.count()).select_from(Session).where(*base_where)
    if status:
        count_stmt = count_stmt.where(Session.status.in_(status))
    total: int = await scope.db.scalar(count_stmt) or 0

    stmt = (
        scope.select(Session, Session.project_id == project_id)
        .order_by(Session.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    if status:
        stmt = stmt.where(Session.status.in_(status))
    rows = await scope.db.scalars(stmt)

    items = []
    for s in rows:
        msg_count = (
            await scope.db.scalar(
                select(func.count()).select_from(Message).where(Message.session_id == s.id)
            )
            or 0
        )
        items.append(
            SessionResponse(
                **{k: getattr(s, k) for k in SessionResponse.model_fields if k != "message_count"},
                message_count=msg_count,
            )
        )

    return SessionListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total > 0 else 0,
    )


async def get_session(scope: TenantScope, session_id: str) -> SessionResponse:
    """Busca sessão por ID. Retorna 404 para IDs de outros tenants."""
    session = await scope.db.scalar(scope.where_id(Session, session_id))
    if not session:
        raise not_found_error("sessão")

    msg_count = (
        await scope.db.scalar(
            select(func.count()).select_from(Message).where(Message.session_id == session.id)
        )
        or 0
    )

    return SessionResponse(
        **{k: getattr(session, k) for k in SessionResponse.model_fields if k != "message_count"},
        message_count=msg_count,
    )


async def update_session(
    scope: TenantScope,
    session_id: str,
    payload: SessionUpdate,
) -> SessionResponse:
    """Atualiza campos da sessão. Retorna 404 para IDs de outros tenants."""
    session = await scope.db.scalar(scope.where_id(Session, session_id))
    if not session:
        raise not_found_error("sessão")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(session, field, value)

    session.updated_at = datetime.utcnow().replace(microsecond=0)
    await scope.db.commit()
    await scope.db.refresh(session)

    msg_count = (
        await scope.db.scalar(
            select(func.count()).select_from(Message).where(Message.session_id == session.id)
        )
        or 0
    )

    return SessionResponse(
        **{k: getattr(session, k) for k in SessionResponse.model_fields if k != "message_count"},
        message_count=msg_count,
    )


# ── Messages ─────────────────────────────────────────────────────────────────


async def add_message(
    scope: TenantScope,
    session_id: str,
    payload: MessageCreate,
) -> MessageResponse:
    """Adiciona mensagem a uma sessão. Valida ownership da sessão.

    message_index é calculado automaticamente baseado na contagem atual.
    """
    session = await scope.db.scalar(scope.where_id(Session, session_id))
    if not session:
        raise not_found_error("sessão")

    # Calcular próximo message_index
    current_count = (
        await scope.db.scalar(
            select(func.count()).select_from(Message).where(Message.session_id == session_id)
        )
        or 0
    )

    message = Message(
        session_id=session_id,
        tenant_id=scope.tenant_id,
        role=payload.role,
        content=payload.content,
        message_index=current_count,
    )
    scope.db.add(message)
    await scope.db.commit()
    await scope.db.refresh(message)
    return MessageResponse.model_validate(message)


async def list_messages(
    scope: TenantScope,
    session_id: str,
    page: int = 1,
    size: int = 50,
) -> MessageListResponse:
    """Lista mensagens de uma sessão com paginação. Valida ownership."""
    # Validar que a sessão pertence ao tenant
    session = await scope.db.scalar(scope.where_id(Session, session_id))
    if not session:
        raise not_found_error("sessão")

    offset = (page - 1) * size

    count_stmt = (
        select(func.count())
        .select_from(Message)
        .where(Message.session_id == session_id)
        .where(Message.tenant_id == scope.tenant_id)
    )
    total: int = await scope.db.scalar(count_stmt) or 0

    stmt = (
        scope.select(Message, Message.session_id == session_id)
        .order_by(Message.message_index.asc())
        .offset(offset)
        .limit(size)
    )
    rows = await scope.db.scalars(stmt)
    items = [MessageResponse.model_validate(m) for m in rows]

    return MessageListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total > 0 else 0,
    )
