"""Project model with TenantMixin for multi-tenant data isolation (Story 3.1)."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantMixin

PROJECT_STATUS_ACTIVE = "active"
PROJECT_STATUS_ARCHIVED = "archived"
VALID_STATUSES = {PROJECT_STATUS_ACTIVE, PROJECT_STATUS_ARCHIVED}


class Project(TenantMixin, Base):
    """Espaço de trabalho de requisitos pertencente a um tenant.

    Isolation invariant: toda query DEVE usar TenantScope.select(Project).
    Cross-tenant access retorna 404 implícito (via where_id → None).
    """

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_domain: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=PROJECT_STATUS_ACTIVE,
    )
    # JSONB em PostgreSQL, JSON em SQLite — armazena progresso e metadados da sessão
    progress_summary: Mapped[dict[str, Any] | None] = mapped_column(
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
