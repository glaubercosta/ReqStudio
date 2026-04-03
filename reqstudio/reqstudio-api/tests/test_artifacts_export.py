"""Integration tests for Artifact Export — Story 6.4.

Verifies:
- Markdown export (content and headers).
- JSON export (raw content and headers).
- Content-Disposition for browser download.
"""

import pytest
import json
from httpx import AsyncClient


# ── Helpers ───────────────────────────────────────────────────────────────────

def _auth(token: dict) -> dict:
    return {"Authorization": f"Bearer {token['access_token']}"}


async def _create_base_artifact(client: AsyncClient, token: dict) -> str:
    # 1. Create Project
    p_res = await client.post(
        "/api/v1/projects",
        json={"name": "Export Project", "business_domain": "Logistics"},
        headers=_auth(token)
    )
    project_id = p_res.json()["data"]["id"]
    
    # 2. Create Artifact
    state = {
        "sections": [{"id": "s1", "title": "Sec", "content": "Cont", "coverage": 1.0, "sources": []}],
        "metadata": {},
        "total_coverage": 1.0
    }
    a_res = await client.post(
        "/api/v1/artifacts/",
        json={"project_id": project_id, "artifact_type": "prd", "title": "Spec Export"},
        headers=_auth(token)
    )
    artifact_id = a_res.json()["data"]["id"]
    
    # Update to populate state
    await client.post(f"/api/v1/artifacts/{artifact_id}/update", json={"artifact_state": state}, headers=_auth(token))
    
    return artifact_id


# ── Tests ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_markdown(client: AsyncClient, tenant_a_token):
    artifact_id = await _create_base_artifact(client, tenant_a_token)
    
    res = await client.get(f"/api/v1/artifacts/{artifact_id}/export?format=markdown", headers=_auth(tenant_a_token))
    assert res.status_code == 200
    assert "text/markdown" in res.headers["Content-Type"]
    assert "attachment" in res.headers["Content-Disposition"]
    assert "v2.md" in res.headers["Content-Disposition"] # Version 1 (create) + 1 (update) = v2
    
    content = res.text
    assert "Artifact: Spec Export" in content
    assert "Version: 2" in content
    assert "## Sec" in content


@pytest.mark.asyncio
async def test_export_json_raw(client: AsyncClient, tenant_a_token):
    artifact_id = await _create_base_artifact(client, tenant_a_token)
    
    res = await client.get(f"/api/v1/artifacts/{artifact_id}/export?format=json", headers=_auth(tenant_a_token))
    assert res.status_code == 200
    assert "application/json" in res.headers["Content-Type"]
    
    # Verify it is raw JSON, not ApiResponse
    body = res.json()
    assert "sections" in body
    assert "data" not in body # No envelope


@pytest.mark.asyncio
async def test_export_technical_view(client: AsyncClient, tenant_a_token):
    artifact_id = await _create_base_artifact(client, tenant_a_token)
    
    res = await client.get(f"/api/v1/artifacts/{artifact_id}/export?format=markdown&view=technical", headers=_auth(tenant_a_token))
    content = res.text
    assert "View: Technical" in content
    assert "(`s1`)" in content # Technical ID
