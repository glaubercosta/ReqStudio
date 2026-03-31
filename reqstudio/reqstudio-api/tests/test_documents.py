"""Tests for Stories 4.1 + 4.2 — Document upload, parsing, MIME validation, isolation.

Padrão: um único `client` + `tenant_a_token` / `tenant_b_token` via headers.
Coverage target: ≥ 80% em app/modules/documents/.
"""

import io
import pytest
from httpx import AsyncClient


# ── Auth helper ───────────────────────────────────────────────────────────────

def _auth(token: dict) -> dict:
    return {"Authorization": f"Bearer {token['access_token']}"}


# ── Project helper ────────────────────────────────────────────────────────────

async def _create_project(client: AsyncClient, token: dict, name: str = "Doc Project") -> str:
    resp = await client.post(
        "/api/v1/projects",
        json={"name": name},
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


# ── File helper ───────────────────────────────────────────────────────────────

def _md_file(content: str = "# Título\n\nConteúdo de teste.\n") -> list:
    return [("file", ("test.md", io.BytesIO(content.encode()), "text/markdown"))]


# ── Story 4.1: Upload ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_upload_markdown_returns_201(client: AsyncClient, tenant_a_token):
    project_id = await _create_project(client, tenant_a_token)
    md_content = "# SLA\n\nAcordo de nível de serviço.\n\n## Itens\n\nItem 1.\nItem 2.\n"

    resp = await client.post(
        f"/api/v1/projects/{project_id}/documents",
        files=_md_file(md_content),
        headers=_auth(tenant_a_token),
    )

    assert resp.status_code == 201, resp.text
    body = resp.json()["data"]
    assert body["filename"] == "test.md"
    assert body["status"] == "ready"
    assert body["chunk_count"] > 0
    assert body["size_bytes"] > 0
    assert body["tenant_id"] == tenant_a_token["tenant_id"]


@pytest.mark.asyncio
async def test_upload_creates_multiple_chunks(client: AsyncClient, tenant_a_token):
    project_id = await _create_project(client, tenant_a_token)
    # Conteúdo longo o suficiente para gerar múltiplos chunks (>1500 chars por seção)
    md_content = "# Seção 1\n\n" + ("Texto longo. " * 200) + "\n\n# Seção 2\n\n" + ("Mais texto. " * 200)

    resp = await client.post(
        f"/api/v1/projects/{project_id}/documents",
        files=_md_file(md_content),
        headers=_auth(tenant_a_token),
    )

    assert resp.status_code == 201
    assert resp.json()["data"]["chunk_count"] > 1


@pytest.mark.asyncio
async def test_upload_too_large_returns_413(client: AsyncClient, tenant_a_token):
    project_id = await _create_project(client, tenant_a_token)
    big = b"x" * (21 * 1024 * 1024)  # 21 MB

    resp = await client.post(
        f"/api/v1/projects/{project_id}/documents",
        files=[("file", ("big.md", io.BytesIO(big), "text/markdown"))],
        headers=_auth(tenant_a_token),
    )

    assert resp.status_code == 413
    assert "VALIDATION_ERROR" in resp.text


@pytest.mark.asyncio
async def test_upload_unsupported_mime_returns_415(client: AsyncClient, tenant_a_token):
    project_id = await _create_project(client, tenant_a_token)
    # Bytes mágicos de exe (MZ) — python-magic detecta como application/x-dosexec
    exe_bytes = b"MZ\x90\x00" + b"\x00" * 100

    resp = await client.post(
        f"/api/v1/projects/{project_id}/documents",
        files=[("file", ("malware.exe", io.BytesIO(exe_bytes), "application/octet-stream"))],
        headers=_auth(tenant_a_token),
    )

    assert resp.status_code == 415
    assert "VALIDATION_ERROR" in resp.text


@pytest.mark.asyncio
async def test_upload_to_nonexistent_project_returns_404(client: AsyncClient, tenant_a_token):
    resp = await client.post(
        "/api/v1/projects/projeto-nao-existe/documents",
        files=_md_file(),
        headers=_auth(tenant_a_token),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_upload_cross_tenant_project_returns_404(
    client: AsyncClient, tenant_a_token, tenant_b_token
):
    """Tenant A não consegue fazer upload ao projeto do Tenant B."""
    project_b_id = await _create_project(client, tenant_b_token, name="Doc Project B")

    resp = await client.post(
        f"/api/v1/projects/{project_b_id}/documents",
        files=_md_file(),
        headers=_auth(tenant_a_token),  # Tenant A tentando acessar projeto B
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_upload_requires_auth(client: AsyncClient, tenant_a_token):
    project_id = await _create_project(client, tenant_a_token)
    resp = await client.post(
        f"/api/v1/projects/{project_id}/documents",
        files=_md_file(),
        # sem headers de auth
    )
    assert resp.status_code == 401


# ── Story 4.2: Listagem ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_empty_project(client: AsyncClient, tenant_a_token):
    project_id = await _create_project(client, tenant_a_token)
    resp = await client.get(
        f"/api/v1/projects/{project_id}/documents",
        headers=_auth(tenant_a_token),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] == 0
    assert resp.json()["data"]["items"] == []


@pytest.mark.asyncio
async def test_list_returns_uploaded_documents(client: AsyncClient, tenant_a_token):
    project_id = await _create_project(client, tenant_a_token)

    for i in range(2):
        await client.post(
            f"/api/v1/projects/{project_id}/documents",
            files=_md_file(f"# Doc {i+1}\n\nConteúdo {i+1}.\n"),
            headers=_auth(tenant_a_token),
        )

    resp = await client.get(
        f"/api/v1/projects/{project_id}/documents",
        headers=_auth(tenant_a_token),
    )
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["total"] == 2
    assert len(body["items"]) == 2


@pytest.mark.asyncio
async def test_list_cross_tenant_isolation(
    client: AsyncClient, tenant_a_token, tenant_b_token
):
    """Tenant B não pode listar documentos do projeto A."""
    project_a_id = await _create_project(client, tenant_a_token, name="Project A")
    await client.post(
        f"/api/v1/projects/{project_a_id}/documents",
        files=_md_file("Documento secreto do Tenant A."),
        headers=_auth(tenant_a_token),
    )

    resp = await client.get(
        f"/api/v1/projects/{project_a_id}/documents",
        headers=_auth(tenant_b_token),  # Tenant B tentando acessar projeto A
    )
    assert resp.status_code == 404


# ── Story 4.2: Remoção ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_returns_204(client: AsyncClient, tenant_a_token):
    project_id = await _create_project(client, tenant_a_token)

    upload = await client.post(
        f"/api/v1/projects/{project_id}/documents",
        files=_md_file(),
        headers=_auth(tenant_a_token),
    )
    doc_id = upload.json()["data"]["id"]

    resp = await client.delete(
        f"/api/v1/projects/{project_id}/documents/{doc_id}",
        headers=_auth(tenant_a_token),
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_removes_from_list(client: AsyncClient, tenant_a_token):
    project_id = await _create_project(client, tenant_a_token)

    upload = await client.post(
        f"/api/v1/projects/{project_id}/documents",
        files=_md_file(),
        headers=_auth(tenant_a_token),
    )
    doc_id = upload.json()["data"]["id"]

    await client.delete(
        f"/api/v1/projects/{project_id}/documents/{doc_id}",
        headers=_auth(tenant_a_token),
    )

    list_resp = await client.get(
        f"/api/v1/projects/{project_id}/documents",
        headers=_auth(tenant_a_token),
    )
    assert list_resp.json()["data"]["total"] == 0


@pytest.mark.asyncio
async def test_delete_nonexistent_returns_404(client: AsyncClient, tenant_a_token):
    project_id = await _create_project(client, tenant_a_token)
    resp = await client.delete(
        f"/api/v1/projects/{project_id}/documents/documento-nao-existe",
        headers=_auth(tenant_a_token),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_cross_tenant_returns_404(
    client: AsyncClient, tenant_a_token, tenant_b_token
):
    """Tenant B não pode deletar documentos do Tenant A."""
    project_a_id = await _create_project(client, tenant_a_token, name="Project A Del")

    upload = await client.post(
        f"/api/v1/projects/{project_a_id}/documents",
        files=_md_file(),
        headers=_auth(tenant_a_token),
    )
    doc_id = upload.json()["data"]["id"]

    resp = await client.delete(
        f"/api/v1/projects/{project_a_id}/documents/{doc_id}",
        headers=_auth(tenant_b_token),  # Tenant B tentando deletar doc de A
    )
    assert resp.status_code == 404
