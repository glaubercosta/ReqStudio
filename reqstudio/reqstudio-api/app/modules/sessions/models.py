"""Session and Message models with TenantMixin for multi-tenant isolation (Story 5.1).

Session pertence a um Project e segue um Workflow.
Message pertence a uma Session.

Invariante de isolamento: toda query DEVE usar TenantScope.select().
Redundância intencional: Message tem tenant_id próprio para defesa em profundidade
(queries de mensagem não precisam de JOIN com session para filtrar por tenant).
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantMixin

SESSION_STATUS_ACTIVE = "active"
SESSION_STATUS_PAUSED = "paused"
SESSION_STATUS_COMPLETED = "completed"
VALID_SESSION_STATUSES = {SESSION_STATUS_ACTIVE, SESSION_STATUS_PAUSED, SESSION_STATUS_COMPLETED}

MESSAGE_ROLE_USER = "user"
MESSAGE_ROLE_ASSISTANT = "assistant"
MESSAGE_ROLE_SYSTEM = "system"
VALID_MESSAGE_ROLES = {MESSAGE_ROLE_USER, MESSAGE_ROLE_ASSISTANT, MESSAGE_ROLE_SYSTEM}


class Session(TenantMixin, Base):
    """Sessão de elicitação vinculada a um projeto e workflow.

    Isolation invariant: toda query DEVE usar TenantScope.select(Session).
    Cross-tenant access retorna 404 implícito (via where_id → None).
    """

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workflow_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workflows.id"),
        nullable=False,
    )
    workflow_position: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SESSION_STATUS_ACTIVE,
    )
    artifact_state: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.utcnow().replace(microsecond=0),
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.utcnow().replace(microsecond=0),
        onupdate=lambda: datetime.utcnow().replace(microsecond=0),
    )


class Message(TenantMixin, Base):
    """Mensagem individual dentro de uma sessão de elicitação.

    tenant_id é redundante com Session.tenant_id por design —
    defesa em profundidade para queries diretas de mensagens.
    """

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=MESSAGE_ROLE_USER,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    cost_usd: Mapped[float | None] = mapped_column(nullable=True, default=None)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
        default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.utcnow().replace(microsecond=0),
    )
