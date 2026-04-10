"""Document service — async, TenantScope (Stories 4.1 + 4.2).

Invariants (Lição 9 do projeto):
  - TenantScope.select(Document) em TODA query — nunca select raw.
  - project_id validado antes de qualquer operação.
  - Chunks deletados em cascata via SQLAlchemy relationship.
"""

from __future__ import annotations

import magic  # type: ignore[import-not-found]
from sqlalchemy import func, select

from app.core.exceptions import ErrorCode, GuidedRecoveryError, Severity, not_found_error
from app.db.tenant import TenantScope
from app.modules.documents.models import (
    ALLOWED_MIME_TYPES,
    DOCUMENT_STATUS_ERROR,
    DOCUMENT_STATUS_READY,
    MAX_UPLOAD_BYTES,
    Document,
    DocumentChunk,
)
from app.modules.documents.parsers import parse_markdown, parse_pdf
from app.modules.documents.schemas import DocumentListResponse, DocumentResponse
from app.modules.projects.models import Project

# ── Custom Errors ─────────────────────────────────────────────────────────────

def _upload_too_large_error(size_mb: int) -> GuidedRecoveryError:
    return GuidedRecoveryError(
        code=ErrorCode.VALIDATION_ERROR,
        message=f"Arquivo excede o limite de 20 MB ({size_mb} MB enviados).",
        help="Reduza o tamanho do arquivo e tente novamente.",
        actions=[],
        severity=Severity.WARNING,
        status_code=413,
    )


def _unsupported_mime_error(mime: str) -> GuidedRecoveryError:
    return GuidedRecoveryError(
        code=ErrorCode.VALIDATION_ERROR,
        message=f"Tipo de arquivo não suportado: {mime}.",
        help="Envie apenas arquivos PDF ou Markdown (.md, .markdown).",
        actions=[],
        severity=Severity.WARNING,
        status_code=415,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _detect_mime(content: bytes, filename: str) -> str:
    """Detecta MIME real do conteúdo (não pela extensão)."""
    detected = magic.from_buffer(content[:2048], mime=True)
    if detected == "text/plain" and filename.lower().endswith((".md", ".markdown")):
        return "text/markdown"
    return detected


def _parse(content: bytes, mime_type: str) -> list[str]:
    if mime_type == "application/pdf":
        return parse_pdf(content)
    return parse_markdown(content)


def _to_response(doc: Document, chunk_count: int) -> DocumentResponse:
    return DocumentResponse(
        id=doc.id,
        project_id=doc.project_id,
        filename=doc.filename,
        mime_type=doc.mime_type,
        size_bytes=doc.size_bytes,
        status=doc.status,
        chunk_count=chunk_count,
        tenant_id=doc.tenant_id,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


# ── Service ───────────────────────────────────────────────────────────────────

async def upload_document(
    scope: TenantScope,
    project_id: str,
    filename: str,
    content: bytes,
) -> DocumentResponse:
    """Valida, persiste e parseia um documento de referência."""

    # 1. Projeto existe e pertence ao tenant
    await scope.get_or_404(Project, project_id, "projeto")

    # 2. Tamanho
    if len(content) > MAX_UPLOAD_BYTES:
        raise _upload_too_large_error(len(content) // (1024 * 1024))

    # 3. MIME real (não extensão)
    mime_type = _detect_mime(content, filename)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise _unsupported_mime_error(mime_type)

    # 4. Persiste o documento (status: processing)
    doc = Document(
        project_id=project_id,
        tenant_id=scope.tenant_id,
        filename=filename,
        mime_type=mime_type,
        size_bytes=len(content),
    )
    scope.db.add(doc)
    await scope.db.flush()  # gera doc.id sem commit

    # 5. Parse e chunks
    chunk_count = 0
    try:
        raw_chunks = _parse(content, mime_type)
        for idx, chunk_text in enumerate(raw_chunks):
            scope.db.add(DocumentChunk(
                document_id=doc.id,
                project_id=project_id,
                tenant_id=scope.tenant_id,
                chunk_index=idx,
                content=chunk_text,
                chunk_metadata={"source": filename, "chunk_index": idx},
            ))
        doc.status = DOCUMENT_STATUS_READY
        chunk_count = len(raw_chunks)
    except Exception:
        doc.status = DOCUMENT_STATUS_ERROR

    await scope.db.commit()
    await scope.db.refresh(doc)
    return _to_response(doc, chunk_count)


async def list_documents(
    scope: TenantScope,
    project_id: str,
) -> DocumentListResponse:
    # Valida projeto
    await scope.get_or_404(Project, project_id, "projeto")

    # Busca documentos com contagem de chunks via subquery
    stmt = scope.select(Document, Document.project_id == project_id)
    docs = list(await scope.db.scalars(stmt))

    # Conta chunks por documento em uma query
    if docs:
        doc_ids = [d.id for d in docs]
        count_stmt = (
            select(DocumentChunk.document_id, func.count().label("cnt"))
            .where(DocumentChunk.document_id.in_(doc_ids))
            .group_by(DocumentChunk.document_id)
        )
        chunk_counts: dict[str, int] = {
            row.document_id: row.cnt
            for row in await scope.db.execute(count_stmt)
        }
    else:
        chunk_counts = {}

    items = [_to_response(d, chunk_counts.get(d.id, 0)) for d in docs]
    return DocumentListResponse(items=items, total=len(items))


async def delete_document(
    scope: TenantScope,
    project_id: str,
    document_id: str,
) -> None:
    # Valida projeto
    await scope.get_or_404(Project, project_id, "projeto")

    doc = await scope.db.scalar(
        scope.select(Document, Document.id == document_id, Document.project_id == project_id)
    )
    if not doc:
        raise not_found_error("documento")

    await scope.db.delete(doc)
    await scope.db.commit()
