"""Integration tests for Artifact Export — Story 6.4.

Verifies:
- Markdown export (content and headers).
- JSON export (raw content and headers).
- Content-Disposition for browser download.
"""

import pytest
from httpx import AsyncClient

# ── Helpers ───────────────────────────────────────────────────────────────────


def _auth(token: dict) -> dict:
    return {"Authorization": f"Bearer {token['access_token']}"}


async def _create_base_artifact(client: AsyncClient, token: dict) -> str:
    # 1. Create Project
    p_res = await client.post(
        "/api/v1/projects",
        json={"name": "Export Project", "business_domain": "Logistics"},
        headers=_auth(token),
    )
    project_id = p_res.json()["data"]["id"]

    # 2. Create Artifact
    state = {
        "sections": [
            {"id": "s1", "title": "Sec", "content": "Cont", "coverage": 1.0, "sources": []}
        ],
        "metadata": {"total_coverage": 1.0},
    }
    a_res = await client.post(
        "/api/v1/artifacts/",
        json={"project_id": project_id, "artifact_type": "prd", "title": "Spec Export"},
        headers=_auth(token),
    )
    artifact_id = a_res.json()["data"]["id"]

    # Update to populate state
    await client.post(
        f"/api/v1/artifacts/{artifact_id}/update",
        json={"artifact_state": state},
        headers=_auth(token),
    )

    return artifact_id


# ── Tests ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_export_markdown(client: AsyncClient, tenant_a_token):
    artifact_id = await _create_base_artifact(client, tenant_a_token)

    res = await client.get(
        f"/api/v1/artifacts/{artifact_id}/export?format=markdown", headers=_auth(tenant_a_token)
    )
    assert res.status_code == 200
    assert "text/markdown" in res.headers["Content-Type"]
    assert "attachment" in res.headers["Content-Disposition"]
    assert "v2.md" in res.headers["Content-Disposition"]  # Version 1 (create) + 1 (update) = v2
    assert float(res.headers["X-Export-Duration-Ms"]) >= 0.0

    content = res.text
    assert "Project: Export Project" in content
    assert "Artifact: Spec Export" in content
    assert "Version: 2" in content
    assert "Coverage: 100%" in content
    assert "## Sec" in content


@pytest.mark.asyncio
async def test_export_json_raw(client: AsyncClient, tenant_a_token):
    artifact_id = await _create_base_artifact(client, tenant_a_token)

    res = await client.get(
        f"/api/v1/artifacts/{artifact_id}/export?format=json", headers=_auth(tenant_a_token)
    )
    assert res.status_code == 200
    assert "application/json" in res.headers["Content-Type"]

    # Verify it is raw JSON, not ApiResponse
    body = res.json()
    assert "sections" in body
    assert "data" not in body  # No envelope


@pytest.mark.asyncio
async def test_export_technical_view(client: AsyncClient, tenant_a_token):
    artifact_id = await _create_base_artifact(client, tenant_a_token)

    res = await client.get(
        f"/api/v1/artifacts/{artifact_id}/export?format=markdown&view=technical",
        headers=_auth(tenant_a_token),
    )
    content = res.text
    assert "View: Technical" in content
    assert "(`s1`)" in content  # Technical ID


@pytest.mark.asyncio
async def test_export_business_view_hides_ids_by_default(client: AsyncClient, tenant_a_token):
    artifact_id = await _create_base_artifact(client, tenant_a_token)

    res = await client.get(
        f"/api/v1/artifacts/{artifact_id}/export?format=markdown&view=business",
        headers=_auth(tenant_a_token),
    )
    assert res.status_code == 200
    content = res.text
    assert "View: Business" in content
    assert "(`s1`)" not in content


@pytest.mark.asyncio
async def test_export_rejects_invalid_view(client: AsyncClient, tenant_a_token):
    artifact_id = await _create_base_artifact(client, tenant_a_token)

    res = await client.get(
        f"/api/v1/artifacts/{artifact_id}/export?format=markdown&view=invalid",
        headers=_auth(tenant_a_token),
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_export_rejects_invalid_format(client: AsyncClient, tenant_a_token):
    artifact_id = await _create_base_artifact(client, tenant_a_token)

    res = await client.get(
        f"/api/v1/artifacts/{artifact_id}/export?format=xml",
        headers=_auth(tenant_a_token),
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_export_filename_is_sanitized(client: AsyncClient, tenant_a_token):
    p_res = await client.post(
        "/api/v1/projects",
        json={"name": "Export Project", "business_domain": "Logistics"},
        headers=_auth(tenant_a_token),
    )
    project_id = p_res.json()["data"]["id"]
    a_res = await client.post(
        "/api/v1/artifacts/",
        json={"project_id": project_id, "artifact_type": "prd", "title": 'Spec "A/B"; Final'},
        headers=_auth(tenant_a_token),
    )
    artifact_id = a_res.json()["data"]["id"]

    await client.post(
        f"/api/v1/artifacts/{artifact_id}/update",
        json={"artifact_state": {"sections": [], "metadata": {"total_coverage": 0.0}}},
        headers=_auth(tenant_a_token),
    )

    res = await client.get(
        f"/api/v1/artifacts/{artifact_id}/export?format=markdown",
        headers=_auth(tenant_a_token),
    )
    assert res.status_code == 200
    assert 'filename="reqstudio_spec_ab_final_' in res.headers["Content-Disposition"]


@pytest.mark.asyncio
async def test_export_respects_tenant_isolation(
    client: AsyncClient, tenant_a_token, tenant_b_token
):
    artifact_id = await _create_base_artifact(client, tenant_a_token)

    res = await client.get(
        f"/api/v1/artifacts/{artifact_id}/export?format=json",
        headers=_auth(tenant_b_token),
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_export_markdown_nfr3_baseline_50_pages_equivalent(
    client: AsyncClient, tenant_a_token
):
    p_res = await client.post(
        "/api/v1/projects",
        json={"name": "Perf Project", "business_domain": "Operations"},
        headers=_auth(tenant_a_token),
    )
    project_id = p_res.json()["data"]["id"]
    a_res = await client.post(
        "/api/v1/artifacts/",
        json={"project_id": project_id, "artifact_type": "prd", "title": "Perf Export"},
        headers=_auth(tenant_a_token),
    )
    artifact_id = a_res.json()["data"]["id"]

    # Baseline sintética para NFR3: 50 seções com conteúdo denso (~50 páginas equivalentes).
    sections = []
    paragraph = (
        "Requisito detalhado com critérios de negócio e regras operacionais. " * 30
    ).strip()
    for i in range(1, 51):
        sections.append(
            {
                "id": f"s{i}",
                "title": f"Secao {i}",
                "content": paragraph,
                "coverage": 0.8,
                "sources": [],
            }
        )

    await client.post(
        f"/api/v1/artifacts/{artifact_id}/update",
        json={"artifact_state": {"sections": sections, "metadata": {"total_coverage": 0.0}}},
        headers=_auth(tenant_a_token),
    )

    res = await client.get(
        f"/api/v1/artifacts/{artifact_id}/export?format=markdown&view=business",
        headers=_auth(tenant_a_token),
    )
    assert res.status_code == 200
    duration_ms = float(res.headers["X-Export-Duration-Ms"])
    assert duration_ms <= 5000.0
