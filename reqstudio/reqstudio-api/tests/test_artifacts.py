"""Integration tests for Artifacts module — Story 6.1.

Covers:
- Creation and initial versioning.
- Multi-tenancy isolation (Tenant A vs Tenant B).
- Automatic version snapshotting on update.
- Version history retrieval.
"""

import pytest
from httpx import AsyncClient

# ── Helpers ───────────────────────────────────────────────────────────────────


def _auth(token: dict) -> dict:
    return {"Authorization": f"Bearer {token['access_token']}"}


async def _create_project(client: AsyncClient, token: dict) -> str:
    res = await client.post(
        "/api/v1/projects",
        json={"name": "Projeto Alpha", "business_domain": "Tech"},
        headers=_auth(token),
    )
    return res.json()["data"]["id"]


# ── Tests ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_artifact_initial_version(client: AsyncClient, tenant_a_token):
    project_id = await _create_project(client, tenant_a_token)

    payload = {"project_id": project_id, "artifact_type": "prd", "title": "PRD Inicial"}

    res = await client.post("/api/v1/artifacts/", json=payload, headers=_auth(tenant_a_token))
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["title"] == "PRD Inicial"
    assert data["version"] == 1
    assert data["artifact_state"]["sections"] == []
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_update_artifact_creates_new_version(client: AsyncClient, tenant_a_token):
    project_id = await _create_project(client, tenant_a_token)

    # Create
    create_res = await client.post(
        "/api/v1/artifacts/",
        json={"project_id": project_id, "artifact_type": "prd", "title": "PRD v1"},
        headers=_auth(tenant_a_token),
    )
    artifact_id = create_res.json()["data"]["id"]

    # Update
    update_payload = {
        "artifact_state": {
            "sections": [
                {
                    "id": "sec-1",
                    "title": "Introdução",
                    "content": "Texto alpha",
                    "coverage": 0.5,
                    "sources": [],
                }
            ],
            "metadata": {"total_coverage": 0.1},
        },
        "change_reason": "Adicionada introdução",
        "changed_by": "dev-user",
    }

    update_res = await client.post(
        f"/api/v1/artifacts/{artifact_id}/update",
        json=update_payload,
        headers=_auth(tenant_a_token),
    )
    assert update_res.status_code == 200
    data = update_res.json()["data"]

    assert data["version"] == 2
    assert len(data["artifact_state"]["sections"]) == 1

    # Verify Version History
    history_res = await client.get(
        f"/api/v1/artifacts/{artifact_id}/versions", headers=_auth(tenant_a_token)
    )
    versions = history_res.json()["data"]
    assert len(versions) == 2
    assert versions[0]["version"] == 2
    assert versions[1]["version"] == 1
    assert versions[0]["change_reason"] == "Adicionada introdução"
    assert versions[0]["changed_by"] == "dev-user"


@pytest.mark.asyncio
async def test_artifact_tenant_isolation(client: AsyncClient, tenant_a_token, tenant_b_token):
    # Tenant A creates project and artifact
    project_a_id = await _create_project(client, tenant_a_token)
    res_create = await client.post(
        "/api/v1/artifacts/",
        json={"project_id": project_a_id, "artifact_type": "prd", "title": "Artifact A"},
        headers=_auth(tenant_a_token),
    )
    artifact_a_id = res_create.json()["data"]["id"]

    # Tenant B tries to GET Tenant A's artifact -> 404
    res_get = await client.get(f"/api/v1/artifacts/{artifact_a_id}", headers=_auth(tenant_b_token))
    assert res_get.status_code == 404

    # Tenant B tries to UPDATE Tenant A's artifact -> 404
    res_update = await client.post(
        f"/api/v1/artifacts/{artifact_a_id}/update",
        json={"artifact_state": {"sections": [], "metadata": {"total_coverage": 0.0}}},
        headers=_auth(tenant_b_token),
    )
    assert res_update.status_code == 404


@pytest.mark.asyncio
async def test_get_project_artifacts(client: AsyncClient, tenant_a_token):
    project_id = await _create_project(client, tenant_a_token)

    await client.post(
        "/api/v1/artifacts/",
        json={"project_id": project_id, "artifact_type": "prd", "title": "Arts 1"},
        headers=_auth(tenant_a_token),
    )
    await client.post(
        "/api/v1/artifacts/",
        json={"project_id": project_id, "artifact_type": "user_stories", "title": "Arts 2"},
        headers=_auth(tenant_a_token),
    )

    res = await client.get(f"/api/v1/artifacts/project/{project_id}", headers=_auth(tenant_a_token))
    assert res.status_code == 200
    assert len(res.json()["data"]) == 2
