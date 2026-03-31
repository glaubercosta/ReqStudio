"""Document and DocumentChunk models with TenantMixin (Story 4.1)."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantMixin

DOCUMENT_STATUS_PROCESSING = "processing"
DOCUMENT_STATUS_READY = "ready"
DOCUMENT_STATUS_ERROR = "error"

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/markdown",
    "text/x-markdown",
    "text/plain",        # .md sem MIME explícito
}

MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB


class Document(TenantMixin, Base):
    """Documento de referência importado para um projeto.

    Isolation invariant: project_id + tenant_id garantem isolamento duplo.
    Toda query DEVE usar TenantScope.select(Document).
    """

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=DOCUMENT_STATUS_PROCESSING
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.utcnow().replace(microsecond=0)
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.utcnow().replace(microsecond=0),
        onupdate=lambda: datetime.utcnow().replace(microsecond=0),
    )

    # Relacionamento com chunks (eager-loadable)
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(TenantMixin, Base):
    """Fragmento de texto extraído de um Document para consumo pelo LLM (Story 4.1).

    O chunk_index garante ordem de leitura preservada no contexto.
    """

    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(String(36), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.utcnow().replace(microsecond=0)
    )

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
