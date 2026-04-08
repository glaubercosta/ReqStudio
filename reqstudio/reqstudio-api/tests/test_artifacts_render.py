"""Integration tests for Artifact Rendering — Story 6.2.

Verifies:
- Business view rendering.
- Technical view rendering (Detects Gherkin).
- Coverage-based warnings.
- 6.2x hardening: section parity, optional IDs toggle, robust Gherkin PT/EN and placeholders.
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
        json={"name": "Render Project", "business_domain": "Finance"},
        headers=_auth(token)
    )
    project_id = p_res.json()["data"]["id"]
    
    # 2. Create Artifact
    a_res = await client.post(
        "/api/v1/artifacts/",
        json={"project_id": project_id, "artifact_type": "prd", "title": "Spec 1.0"},
        headers=_auth(token)
    )
    return a_res.json()["data"]["id"]


# ── Tests ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_render_business_view(client: AsyncClient, tenant_a_token):
    artifact_id = await _create_base_artifact(client, tenant_a_token)
    
    # Update with some content
    state = {
        "sections": [
            {"id": "intro", "title": "Introdução", "content": "Texto de negócio.", "coverage": 1.0, "sources": []}
        ],
        "metadata": {"total_coverage": 1.0}
    }
    await client.post(f"/api/v1/artifacts/{artifact_id}/update", json={"artifact_state": state}, headers=_auth(tenant_a_token))
    
    # Render
    res = await client.get(f"/api/v1/artifacts/{artifact_id}/render?view=business", headers=_auth(tenant_a_token))
    assert res.status_code == 200
    md = res.json()["data"]["markdown"]
    
    assert "# Spec 1.0" in md
    assert "Visão de Negócio" in md
    assert "## Introdução" in md
    assert "Texto de negócio." in md
    assert "Introdução (intro)" not in md # Technical detail hidden


@pytest.mark.asyncio
async def test_render_technical_view_with_gherkin(client: AsyncClient, tenant_a_token):
    artifact_id = await _create_base_artifact(client, tenant_a_token)
    
    # Update with Gherkin content
    state = {
        "sections": [
            {"id": "req-1", "title": "Login", "content": "Given user at login\nWhen enters pass\nThen redirect dashboard.", "coverage": 1.0, "sources": []}
        ],
        "metadata": {"total_coverage": 1.0}
    }
    await client.post(f"/api/v1/artifacts/{artifact_id}/update", json={"artifact_state": state}, headers=_auth(tenant_a_token))
    
    # Render Technical
    res = await client.get(f"/api/v1/artifacts/{artifact_id}/render?view=technical", headers=_auth(tenant_a_token))
    assert res.status_code == 200
    md = res.json()["data"]["markdown"]
    
    assert "Especificação Técnica" in md
    assert "## Login (`req-1`)" in md # Technical ID present
    assert "```gherkin" in md # Auto-detected Gherkin block


@pytest.mark.asyncio
async def test_render_low_coverage_warning(client: AsyncClient, tenant_a_token):
    artifact_id = await _create_base_artifact(client, tenant_a_token)
    
    # Update with Low Coverage
    state = {
        "sections": [
            {"id": "draft-sec", "title": "Ponto Obscuro", "content": "Só uma ideia...", "coverage": 0.1, "sources": []}
        ],
        "metadata": {"total_coverage": 0.1}
    }
    await client.post(f"/api/v1/artifacts/{artifact_id}/update", json={"artifact_state": state}, headers=_auth(tenant_a_token))
    
    # Render
    res = await client.get(f"/api/v1/artifacts/{artifact_id}/render", headers=_auth(tenant_a_token))
    md = res.json()["data"]["markdown"]
    
    assert "⚠️ Pendente de aprofundamento" in md
    assert "[!WARNING]" in md


@pytest.mark.asyncio
async def test_render_business_view_show_ids_toggle(client: AsyncClient, tenant_a_token):
    artifact_id = await _create_base_artifact(client, tenant_a_token)

    state = {
        "sections": [
            {"id": "s-1", "title": "Objetivo", "content": "Texto", "coverage": 1.0, "sources": []}
        ],
        "metadata": {"total_coverage": 1.0}
    }
    await client.post(
        f"/api/v1/artifacts/{artifact_id}/update",
        json={"artifact_state": state},
        headers=_auth(tenant_a_token),
    )

    default_res = await client.get(
        f"/api/v1/artifacts/{artifact_id}/render?view=business",
        headers=_auth(tenant_a_token),
    )
    default_md = default_res.json()["data"]["markdown"]
    assert "## Objetivo (`s-1`)" not in default_md

    with_ids_res = await client.get(
        f"/api/v1/artifacts/{artifact_id}/render?view=business&show_ids=true",
        headers=_auth(tenant_a_token),
    )
    with_ids_md = with_ids_res.json()["data"]["markdown"]
    assert "## Objetivo (`s-1`)" in with_ids_md


@pytest.mark.asyncio
async def test_render_preserves_section_order_in_both_views(client: AsyncClient, tenant_a_token):
    artifact_id = await _create_base_artifact(client, tenant_a_token)

    state = {
        "sections": [
            {"id": "s-1", "title": "Primeira", "content": "A", "coverage": 1.0, "sources": []},
            {"id": "s-2", "title": "Segunda", "content": "B", "coverage": 1.0, "sources": []},
            {"id": "s-3", "title": "Terceira", "content": "C", "coverage": 1.0, "sources": []},
        ],
        "metadata": {"total_coverage": 1.0}
    }
    await client.post(
        f"/api/v1/artifacts/{artifact_id}/update",
        json={"artifact_state": state},
        headers=_auth(tenant_a_token),
    )

    business_res = await client.get(
        f"/api/v1/artifacts/{artifact_id}/render?view=business&show_ids=true",
        headers=_auth(tenant_a_token),
    )
    technical_res = await client.get(
        f"/api/v1/artifacts/{artifact_id}/render?view=technical",
        headers=_auth(tenant_a_token),
    )

    business_md = business_res.json()["data"]["markdown"]
    technical_md = technical_res.json()["data"]["markdown"]

    business_pos = [business_md.index(f"`{sec_id}`") for sec_id in ("s-1", "s-2", "s-3")]
    technical_pos = [technical_md.index(f"`{sec_id}`") for sec_id in ("s-1", "s-2", "s-3")]

    assert business_pos == sorted(business_pos)
    assert technical_pos == sorted(technical_pos)


@pytest.mark.asyncio
async def test_render_technical_gherkin_portuguese_case_insensitive_no_double_wrap(client: AsyncClient, tenant_a_token):
    artifact_id = await _create_base_artifact(client, tenant_a_token)

    state = {
        "sections": [
            {
                "id": "pt-1",
                "title": "Cenário PT",
                "content": "dado usuário autenticado\nquando clicar em sair\nentão deve encerrar sessão",
                "coverage": 1.0,
                "sources": [],
            },
            {
                "id": "en-1",
                "title": "Cenário EN",
                "content": "```gherkin\nGiven user is logged in\nWhen click logout\nThen session ends\n```",
                "coverage": 1.0,
                "sources": [],
            },
        ],
        "metadata": {"total_coverage": 1.0}
    }
    await client.post(
        f"/api/v1/artifacts/{artifact_id}/update",
        json={"artifact_state": state},
        headers=_auth(tenant_a_token),
    )

    res = await client.get(
        f"/api/v1/artifacts/{artifact_id}/render?view=technical",
        headers=_auth(tenant_a_token),
    )
    md = res.json()["data"]["markdown"]

    assert "dado usuário autenticado" in md
    assert md.count("```gherkin") == 2


@pytest.mark.asyncio
async def test_render_empty_section_uses_canonical_placeholder(client: AsyncClient, tenant_a_token):
    artifact_id = await _create_base_artifact(client, tenant_a_token)

    state = {
        "sections": [
            {"id": "empty-1", "title": "Seção vazia", "content": "   ", "coverage": 0.9, "sources": []}
        ],
        "metadata": {"total_coverage": 0.9}
    }
    await client.post(
        f"/api/v1/artifacts/{artifact_id}/update",
        json={"artifact_state": state},
        headers=_auth(tenant_a_token),
    )

    res = await client.get(
        f"/api/v1/artifacts/{artifact_id}/render?view=business",
        headers=_auth(tenant_a_token),
    )
    md = res.json()["data"]["markdown"]
    assert "_Sem conteúdo detalhado._" in md


@pytest.mark.asyncio
async def test_render_rejects_invalid_view(client: AsyncClient, tenant_a_token):
    artifact_id = await _create_base_artifact(client, tenant_a_token)

    res = await client.get(
        f"/api/v1/artifacts/{artifact_id}/render?view=invalid",
        headers=_auth(tenant_a_token),
    )
    assert res.status_code == 422
