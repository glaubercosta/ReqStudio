"""Integration tests for Artifact Coverage — Story 6.3.

Verifies:
- Automatic recalculation of total_coverage during update.
- Coverage endpoint data integrity.
- Coverage bands/states for UI mapping.
- Cross-tenant access isolation.
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
        json={"name": "Coverage Project", "business_domain": "QA"},
        headers=_auth(token),
    )
    project_id = p_res.json()["data"]["id"]

    # 2. Create Artifact
    a_res = await client.post(
        "/api/v1/artifacts/",
        json={"project_id": project_id, "artifact_type": "prd", "title": "Coverage Test"},
        headers=_auth(token),
    )
    return a_res.json()["data"]["id"]


# ── Tests ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_automatic_coverage_calculation(client: AsyncClient, tenant_a_token):
    artifact_id = await _create_base_artifact(client, tenant_a_token)

    # Updated state with 2 sections (0.5 and 1.0)
    state = {
        "sections": [
            {"id": "sec-1", "title": "S1", "content": "c1", "coverage": 0.5, "sources": []},
            {"id": "sec-2", "title": "S2", "content": "c2", "coverage": 1.0, "sources": []},
        ],
        "metadata": {"total_coverage": 0.0},  # Will be overwritten by backend
    }

    update_res = await client.post(
        f"/api/v1/artifacts/{artifact_id}/update",
        json={"artifact_state": state},
        headers=_auth(tenant_a_token),
    )
    assert update_res.status_code == 200
    data = update_res.json()["data"]

    # Average: (0.5 + 1.0) / 2 = 0.75
    assert data["artifact_state"]["metadata"]["total_coverage"] == 0.75


@pytest.mark.asyncio
async def test_get_coverage_endpoint(client: AsyncClient, tenant_a_token):
    artifact_id = await _create_base_artifact(client, tenant_a_token)

    # Update with 3 sections
    state = {
        "sections": [
            {"id": "s1", "title": "T1", "content": "...", "coverage": 0.2, "sources": []},
            {"id": "s2", "title": "T2", "content": "...", "coverage": 0.4, "sources": []},
            {"id": "s3", "title": "T3", "content": "...", "coverage": 0.6, "sources": []},
        ],
        "metadata": {"total_coverage": 0.0},
    }
    await client.post(
        f"/api/v1/artifacts/{artifact_id}/update",
        json={"artifact_state": state},
        headers=_auth(tenant_a_token),
    )

    # Get Coverage
    res = await client.get(
        f"/api/v1/artifacts/{artifact_id}/coverage", headers=_auth(tenant_a_token)
    )
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["artifact_id"] == artifact_id
    assert data["total_coverage"] == 0.4  # (0.2+0.4+0.6)/3
    assert len(data["sections"]) == 3
    assert data["sections"][0]["title"] == "T1"
    assert data["sections"][1]["coverage"] == 0.4
    assert data["sections"][0]["coverage_band"] == "low"
    assert data["sections"][0]["card_state"] == "pending"
    assert data["sections"][1]["coverage_band"] == "medium"
    assert data["sections"][1]["card_state"] == "active"


@pytest.mark.asyncio
async def test_get_coverage_empty_sections(client: AsyncClient, tenant_a_token):
    artifact_id = await _create_base_artifact(client, tenant_a_token)

    res = await client.get(
        f"/api/v1/artifacts/{artifact_id}/coverage", headers=_auth(tenant_a_token)
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total_coverage"] == 0.0
    assert data["sections"] == []


@pytest.mark.asyncio
async def test_get_coverage_bands_thresholds(client: AsyncClient, tenant_a_token):
    artifact_id = await _create_base_artifact(client, tenant_a_token)

    state = {
        "sections": [
            {"id": "s-low", "title": "Low", "content": "...", "coverage": 0.29, "sources": []},
            {"id": "s-mid-a", "title": "MidA", "content": "...", "coverage": 0.30, "sources": []},
            {"id": "s-mid-b", "title": "MidB", "content": "...", "coverage": 0.70, "sources": []},
            {"id": "s-high", "title": "High", "content": "...", "coverage": 0.71, "sources": []},
        ],
        "metadata": {
            "total_coverage": 1.0
        },  # intentionally wrong to validate backend recalculation
    }
    await client.post(
        f"/api/v1/artifacts/{artifact_id}/update",
        json={"artifact_state": state},
        headers=_auth(tenant_a_token),
    )

    res = await client.get(
        f"/api/v1/artifacts/{artifact_id}/coverage", headers=_auth(tenant_a_token)
    )
    assert res.status_code == 200
    data = res.json()["data"]
    by_id = {s["id"]: s for s in data["sections"]}

    assert by_id["s-low"]["coverage_band"] == "low"
    assert by_id["s-low"]["card_state"] == "pending"
    assert by_id["s-mid-a"]["coverage_band"] == "medium"
    assert by_id["s-mid-a"]["card_state"] == "active"
    assert by_id["s-mid-b"]["coverage_band"] == "medium"
    assert by_id["s-mid-b"]["card_state"] == "active"
    assert by_id["s-high"]["coverage_band"] == "high"
    assert by_id["s-high"]["card_state"] == "complete"
    assert data["total_coverage"] == 0.5  # (0.29 + 0.30 + 0.70 + 0.71)/4


@pytest.mark.asyncio
async def test_get_coverage_tenant_isolation(client: AsyncClient, tenant_a_token, tenant_b_token):
    artifact_id = await _create_base_artifact(client, tenant_a_token)

    res = await client.get(
        f"/api/v1/artifacts/{artifact_id}/coverage",
        headers=_auth(tenant_b_token),
    )
    assert res.status_code == 404
