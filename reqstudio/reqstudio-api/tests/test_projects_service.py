"""Unit tests for projects/service.py — targeting uncovered service functions.

Covers: create_project, list_projects, get_project, update_project
with direct TenantScope usage.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import GuidedRecoveryError
from app.db.tenant import TenantScope
from app.modules.projects.models import PROJECT_STATUS_ACTIVE
from app.modules.projects.schemas import ProjectCreate, ProjectUpdate
from app.modules.projects.service import (
    create_project,
    get_project,
    list_projects,
    update_project,
)

TENANT_ID = "t-proj-svc-001"


# ── create_project ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_project_success(db_session: AsyncSession):
    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    payload = ProjectCreate(name="Projeto Alpha", business_domain="Saúde")
    result = await create_project(scope, payload)

    assert result.name == "Projeto Alpha"
    assert result.business_domain == "Saúde"
    assert result.tenant_id == TENANT_ID
    assert result.status == PROJECT_STATUS_ACTIVE


@pytest.mark.asyncio
async def test_create_project_with_description(db_session: AsyncSession):
    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    payload = ProjectCreate(
        name="Projeto Beta",
        business_domain="Finanças",
        description="A finance project",
    )
    result = await create_project(scope, payload)
    assert result.description == "A finance project"


@pytest.mark.asyncio
async def test_create_project_without_optional_fields(db_session: AsyncSession):
    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    payload = ProjectCreate(name="Mínimo")
    result = await create_project(scope, payload)
    assert result.description is None


# ── list_projects ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_projects_empty(db_session: AsyncSession):
    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    result = await list_projects(scope)
    assert result.total == 0
    assert result.items == []
    assert result.pages == 0


@pytest.mark.asyncio
async def test_list_projects_returns_active_by_default(db_session: AsyncSession):
    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    await create_project(scope, ProjectCreate(name="P1"))
    await create_project(scope, ProjectCreate(name="P2"))

    result = await list_projects(scope)
    assert result.total == 2
    assert all(p.status == PROJECT_STATUS_ACTIVE for p in result.items)


@pytest.mark.asyncio
async def test_list_projects_pagination(db_session: AsyncSession):
    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    for i in range(5):
        await create_project(scope, ProjectCreate(name=f"Proj {i}"))

    result = await list_projects(scope, page=1, size=2)
    assert result.total == 5
    assert len(result.items) == 2
    assert result.pages == 3


@pytest.mark.asyncio
async def test_list_projects_filter_by_status(db_session: AsyncSession):
    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    await create_project(scope, ProjectCreate(name="Active Proj"))
    p2 = await create_project(scope, ProjectCreate(name="Archived Proj"))

    # Archive one project
    await update_project(scope, p2.id, ProjectUpdate(status="archived"))

    active_result = await list_projects(scope, status="active")
    assert active_result.total == 1
    assert active_result.items[0].name == "Active Proj"

    archived_result = await list_projects(scope, status="archived")
    assert archived_result.total == 1
    assert archived_result.items[0].name == "Archived Proj"


@pytest.mark.asyncio
async def test_list_projects_cross_tenant_isolation(db_session: AsyncSession):
    scope_a = TenantScope(db=db_session, tenant_id="tenant-a")
    scope_b = TenantScope(db=db_session, tenant_id="tenant-b")

    await create_project(scope_a, ProjectCreate(name="Proj A"))
    await create_project(scope_b, ProjectCreate(name="Proj B"))

    result_a = await list_projects(scope_a)
    assert result_a.total == 1
    assert result_a.items[0].name == "Proj A"

    result_b = await list_projects(scope_b)
    assert result_b.total == 1
    assert result_b.items[0].name == "Proj B"


# ── get_project ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_project_success(db_session: AsyncSession):
    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    created = await create_project(scope, ProjectCreate(name="Get Test"))

    result = await get_project(scope, created.id)
    assert result.id == created.id
    assert result.name == "Get Test"


@pytest.mark.asyncio
async def test_get_project_not_found(db_session: AsyncSession):
    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    with pytest.raises(GuidedRecoveryError):
        await get_project(scope, "nonexistent-id")


@pytest.mark.asyncio
async def test_get_project_cross_tenant(db_session: AsyncSession):
    scope_a = TenantScope(db=db_session, tenant_id="tenant-a")
    scope_b = TenantScope(db=db_session, tenant_id="tenant-b")

    created = await create_project(scope_a, ProjectCreate(name="Proj A"))

    # tenant-b should not see tenant-a's project
    with pytest.raises(GuidedRecoveryError):
        await get_project(scope_b, created.id)


# ── update_project ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_project_name(db_session: AsyncSession):
    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    created = await create_project(scope, ProjectCreate(name="Before"))

    result = await update_project(scope, created.id, ProjectUpdate(name="After"))
    assert result.name == "After"


@pytest.mark.asyncio
async def test_update_project_status_to_archived(db_session: AsyncSession):
    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    created = await create_project(scope, ProjectCreate(name="To Archive"))

    result = await update_project(scope, created.id, ProjectUpdate(status="archived"))
    assert result.status == "archived"


@pytest.mark.asyncio
async def test_update_project_not_found(db_session: AsyncSession):
    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    with pytest.raises(GuidedRecoveryError):
        await update_project(scope, "nonexistent-id", ProjectUpdate(name="X"))


@pytest.mark.asyncio
async def test_update_project_cross_tenant(db_session: AsyncSession):
    scope_a = TenantScope(db=db_session, tenant_id="tenant-a")
    scope_b = TenantScope(db=db_session, tenant_id="tenant-b")

    created = await create_project(scope_a, ProjectCreate(name="Proj A"))

    with pytest.raises(GuidedRecoveryError):
        await update_project(scope_b, created.id, ProjectUpdate(name="Hacked"))


@pytest.mark.asyncio
async def test_update_project_partial_update(db_session: AsyncSession):
    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    created = await create_project(
        scope,
        ProjectCreate(name="Partial", description="Original desc", business_domain="Saúde"),
    )

    # Only update description, name should stay the same
    result = await update_project(scope, created.id, ProjectUpdate(description="Updated desc"))
    assert result.name == "Partial"
    assert result.description == "Updated desc"
