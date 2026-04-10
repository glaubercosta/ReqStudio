"""Unit tests for documents/service.py — targeting uncovered service functions.

Covers: upload_document, list_documents, delete_document,
helper functions (_detect_mime, _parse, _to_response, error factories).
"""

from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import GuidedRecoveryError
from app.db.tenant import TenantScope
from app.modules.documents.models import (
    DOCUMENT_STATUS_ERROR,
    DOCUMENT_STATUS_READY,
    MAX_UPLOAD_BYTES,
    Document,
    DocumentChunk,
)
from app.modules.documents.service import (
    _detect_mime,
    _parse,
    _to_response,
    _unsupported_mime_error,
    _upload_too_large_error,
    delete_document,
    list_documents,
    upload_document,
)
from app.modules.projects.models import PROJECT_STATUS_ACTIVE, Project

TENANT_ID = "t-doc-svc-001"


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _seed_project(db: AsyncSession, tenant_id: str = TENANT_ID) -> Project:
    project = Project(
        name="Doc Project",
        business_domain="Saúde",
        tenant_id=tenant_id,
        status=PROJECT_STATUS_ACTIVE,
    )
    db.add(project)
    await db.flush()
    return project


# ── Error factories ──────────────────────────────────────────────────────────


def test_upload_too_large_error():
    err = _upload_too_large_error(25)
    assert err.status_code == 413
    assert "25 MB" in err.message


def test_unsupported_mime_error():
    err = _unsupported_mime_error("image/png")
    assert err.status_code == 415
    assert "image/png" in err.message


# ── _detect_mime ─────────────────────────────────────────────────────────────


def test_detect_mime_markdown_extension():
    """text/plain with .md extension should be detected as text/markdown."""
    with patch("app.modules.documents.service.magic") as mock_magic:
        mock_magic.from_buffer.return_value = "text/plain"
        result = _detect_mime(b"# Hello", "readme.md")
        assert result == "text/markdown"


def test_detect_mime_markdown_extension_uppercase():
    with patch("app.modules.documents.service.magic") as mock_magic:
        mock_magic.from_buffer.return_value = "text/plain"
        result = _detect_mime(b"# Hello", "README.MARKDOWN")
        assert result == "text/markdown"


def test_detect_mime_pdf():
    with patch("app.modules.documents.service.magic") as mock_magic:
        mock_magic.from_buffer.return_value = "application/pdf"
        result = _detect_mime(b"%PDF-1.4", "doc.pdf")
        assert result == "application/pdf"


def test_detect_mime_plain_text_not_md():
    with patch("app.modules.documents.service.magic") as mock_magic:
        mock_magic.from_buffer.return_value = "text/plain"
        result = _detect_mime(b"plain content", "notes.txt")
        assert result == "text/plain"


# ── _parse ───────────────────────────────────────────────────────────────────


def test_parse_markdown():
    content = (b"# Title\n\nSome content that is long enough"
               b" to be a valid chunk for testing purposes.")
    result = _parse(content, "text/markdown")
    assert isinstance(result, list)


def test_parse_pdf():
    """parse_pdf delegates to fitz; mock at import level in parsers module."""
    import importlib
    import sys
    import types

    # Create a fake fitz module
    fake_fitz = types.ModuleType("fitz")
    mock_doc_ctx = type("Doc", (), {
        "__enter__": lambda self: self,
        "__exit__": lambda self, *a: None,
        "__iter__": lambda self: iter([type("Page", (), {
            "get_text": lambda self, _: "Page 1 content that is long enough",
        })()]),
    })()
    fake_fitz.open = lambda **kwargs: mock_doc_ctx  # type: ignore[attr-defined]
    sys.modules["fitz"] = fake_fitz
    try:
        # Reload parsers so it picks up our fake fitz
        import app.modules.documents.parsers as parsers_mod
        importlib.reload(parsers_mod)
        result = parsers_mod.parse_pdf(b"fake-pdf-bytes")
        assert isinstance(result, list)
    finally:
        del sys.modules["fitz"]
        importlib.reload(parsers_mod)


# ── _to_response ─────────────────────────────────────────────────────────────


def test_to_response():
    from datetime import datetime

    now = datetime.utcnow().replace(microsecond=0)
    doc = Document(
        id="doc-1",
        project_id="proj-1",
        filename="test.md",
        mime_type="text/markdown",
        size_bytes=100,
        status=DOCUMENT_STATUS_READY,
        tenant_id=TENANT_ID,
    )
    # Manually set timestamps since defaults only trigger on DB flush
    doc.created_at = now
    doc.updated_at = now
    resp = _to_response(doc, chunk_count=3)
    assert resp.id == "doc-1"
    assert resp.chunk_count == 3
    assert resp.filename == "test.md"


# ── upload_document ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upload_document_success(db_session: AsyncSession):
    project = await _seed_project(db_session)
    await db_session.commit()

    md_content = (
        b"# Test\n\nThis is a test document with enough"
        b" content to create a chunk for testing."
    )

    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    with patch("app.modules.documents.service.magic") as mock_magic:
        mock_magic.from_buffer.return_value = "text/plain"
        result = await upload_document(scope, project.id, "test.md", md_content)

    assert result.filename == "test.md"
    assert result.mime_type == "text/markdown"
    assert result.status == DOCUMENT_STATUS_READY
    assert result.project_id == project.id


@pytest.mark.asyncio
async def test_upload_document_project_not_found(db_session: AsyncSession):
    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    with pytest.raises(GuidedRecoveryError):
        await upload_document(scope, "nonexistent-project", "test.md", b"content")


@pytest.mark.asyncio
async def test_upload_document_too_large(db_session: AsyncSession):
    project = await _seed_project(db_session)
    await db_session.commit()

    large_content = b"x" * (MAX_UPLOAD_BYTES + 1)
    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    with pytest.raises(GuidedRecoveryError) as exc_info:
        await upload_document(scope, project.id, "large.md", large_content)
    assert exc_info.value.status_code == 413


@pytest.mark.asyncio
async def test_upload_document_unsupported_mime(db_session: AsyncSession):
    project = await _seed_project(db_session)
    await db_session.commit()

    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    with patch("app.modules.documents.service.magic") as mock_magic:
        mock_magic.from_buffer.return_value = "image/png"
        with pytest.raises(GuidedRecoveryError) as exc_info:
            await upload_document(scope, project.id, "image.png", b"fake-png-data")
        assert exc_info.value.status_code == 415


@pytest.mark.asyncio
async def test_upload_document_parse_error_sets_error_status(db_session: AsyncSession):
    project = await _seed_project(db_session)
    await db_session.commit()

    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    with (
        patch("app.modules.documents.service.magic") as mock_magic,
        patch("app.modules.documents.service._parse", side_effect=Exception("parse fail")),
    ):
        mock_magic.from_buffer.return_value = "text/plain"
        result = await upload_document(scope, project.id, "bad.md", b"content")

    assert result.status == DOCUMENT_STATUS_ERROR


# ── list_documents ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_documents_empty(db_session: AsyncSession):
    project = await _seed_project(db_session)
    await db_session.commit()

    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    result = await list_documents(scope, project.id)
    assert result.total == 0
    assert result.items == []


@pytest.mark.asyncio
async def test_list_documents_with_items(db_session: AsyncSession):
    project = await _seed_project(db_session)
    doc = Document(
        project_id=project.id,
        tenant_id=TENANT_ID,
        filename="test.md",
        mime_type="text/markdown",
        size_bytes=100,
        status=DOCUMENT_STATUS_READY,
    )
    db_session.add(doc)
    await db_session.flush()
    chunk = DocumentChunk(
        document_id=doc.id,
        project_id=project.id,
        tenant_id=TENANT_ID,
        chunk_index=0,
        content="Test chunk content",
    )
    db_session.add(chunk)
    await db_session.commit()

    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    result = await list_documents(scope, project.id)
    assert result.total == 1
    assert result.items[0].chunk_count == 1


@pytest.mark.asyncio
async def test_list_documents_project_not_found(db_session: AsyncSession):
    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    with pytest.raises(GuidedRecoveryError):
        await list_documents(scope, "nonexistent-project")


# ── delete_document ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_document_success(db_session: AsyncSession):
    project = await _seed_project(db_session)
    doc = Document(
        project_id=project.id,
        tenant_id=TENANT_ID,
        filename="delete-me.md",
        mime_type="text/markdown",
        size_bytes=50,
        status=DOCUMENT_STATUS_READY,
    )
    db_session.add(doc)
    await db_session.commit()

    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    await delete_document(scope, project.id, doc.id)

    # Verify it's gone
    result = await list_documents(scope, project.id)
    assert result.total == 0


@pytest.mark.asyncio
async def test_delete_document_project_not_found(db_session: AsyncSession):
    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    with pytest.raises(GuidedRecoveryError):
        await delete_document(scope, "nonexistent-project", "doc-id")


@pytest.mark.asyncio
async def test_delete_document_not_found(db_session: AsyncSession):
    project = await _seed_project(db_session)
    await db_session.commit()

    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    with pytest.raises(GuidedRecoveryError):
        await delete_document(scope, project.id, "nonexistent-doc")
