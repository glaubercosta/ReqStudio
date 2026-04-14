"""Artifact and ArtifactVersion models with TenantMixin for multi-tenant isolation (Story 6.1).

Artifacts are structured JSONB representations of requirements, derived from sessions.
Every confirmed update increments the version and creates a snapshot in ArtifactVersion.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantMixin

# Artifact Types
ARTIFACT_TYPE_PRD = "prd"
ARTIFACT_TYPE_USER_STORIES = "user_stories"
ARTIFACT_TYPE_TECHNICAL_SPEC = "technical_spec"
VALID_ARTIFACT_TYPES = {ARTIFACT_TYPE_PRD, ARTIFACT_TYPE_USER_STORIES, ARTIFACT_TYPE_TECHNICAL_SPEC}

# Artifact Status
ARTIFACT_STATUS_DRAFT = "draft"
ARTIFACT_STATUS_COMPLETE = "complete"


class Artifact(TenantMixin, Base):
    """Modelo principal de artefato estruturado.

    Isolamento garantido por TenantMixin.
    Referencia Session e Project para contexto.
    """

    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True, index=True
    )

    artifact_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    # Estado canônico do artefato (JSONB)
    artifact_state: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Dados de cobertura calculada (Story 6.3)
    coverage_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True, default=None)

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=ARTIFACT_STATUS_DRAFT)

    created_at: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.utcnow().replace(microsecond=0)
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.utcnow().replace(microsecond=0),
        onupdate=lambda: datetime.utcnow().replace(microsecond=0),
    )


class ArtifactVersion(TenantMixin, Base):
    """Snapshot histórico de um artefato.

    Criado automaticamente a cada incremento de versão do Artifact.
    """

    __tablename__ = "artifact_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    artifact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False, index=True
    )

    version: Mapped[int] = mapped_column(Integer, nullable=False)
    state_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    change_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by: Mapped[str | None] = mapped_column(
        String(36), nullable=True
    )  # User ID se implementado

    created_at: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.utcnow().replace(microsecond=0)
    )
