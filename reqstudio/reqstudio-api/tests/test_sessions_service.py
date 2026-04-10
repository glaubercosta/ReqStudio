"""Unit tests for sessions/service.py — targeting uncovered service functions.

Covers: _resolve_workflow_id, create_session, list_sessions, get_session,
update_session, add_message, list_messages with direct TenantScope usage.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import GuidedRecoveryError
from app.db.tenant import TenantScope
from app.modules.projects.models import PROJECT_STATUS_ACTIVE, Project
from app.modules.sessions.models import SESSION_STATUS_ACTIVE, Session
from app.modules.sessions.schemas import MessageCreate, SessionUpdate
from app.modules.sessions.service import (
    _resolve_workflow_id,
    add_message,
    create_session,
    get_session,
    list_messages,
    list_sessions,
    update_session,
)
from app.modules.workflows.models import Workflow

TENANT_ID = "t-sess-svc-001"


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _seed_project(db: AsyncSession, tenant_id: str = TENANT_ID) -> Project:
    project = Project(
        name="Projeto Teste",
        business_domain="Saúde",
        tenant_id=tenant_id,
        status=PROJECT_STATUS_ACTIVE,
    )
    db.add(project)
    await db.flush()
    return project


async def _seed_workflow(db: AsyncSession) -> Workflow:
    wf = Workflow(
        name="elicitation-briefing",
        description="Workflow de briefing",
        config={"max_iterations": 10},
    )
    db.add(wf)
    await db.flush()
    return wf


async def _seed_session(
    db: AsyncSession, project_id: str, workflow_id: str, tenant_id: str = TENANT_ID,
) -> Session:
    session = Session(
        project_id=project_id,
        workflow_id=workflow_id,
        tenant_id=tenant_id,
        status=SESSION_STATUS_ACTIVE,
    )
    db.add(session)
    await db.flush()
    return session


# ── _resolve_workflow_id ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_resolve_workflow_id_with_explicit_id(db_session: AsyncSession):
    wf = await _seed_workflow(db_session)
    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    result = await _resolve_workflow_id(scope, wf.id)
    assert result == wf.id


@pytest.mark.asyncio
async def test_resolve_workflow_id_default(db_session: AsyncSession):
    wf = await _seed_workflow(db_session)
    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    result = await _resolve_workflow_id(scope, None)
    assert result == wf.id


@pytest.mark.asyncio
async def test_resolve_workflow_id_not_found_raises(db_session: AsyncSession):
    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    with pytest.raises(GuidedRecoveryError):
        await _resolve_workflow_id(scope, "nonexistent-id")


@pytest.mark.asyncio
async def test_resolve_workflow_id_default_not_found_raises(db_session: AsyncSession):
    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    with pytest.raises(GuidedRecoveryError):
        await _resolve_workflow_id(scope, None)


# ── create_session ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_session_success(db_session: AsyncSession):
    project = await _seed_project(db_session)
    wf = await _seed_workflow(db_session)
    await db_session.commit()

    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    result = await create_session(scope, project.id)

    assert result.project_id == project.id
    assert result.tenant_id == TENANT_ID
    assert result.status == SESSION_STATUS_ACTIVE
    assert result.workflow_id == wf.id
    assert result.message_count == 0


@pytest.mark.asyncio
async def test_create_session_project_not_found(db_session: AsyncSession):
    await _seed_workflow(db_session)
    await db_session.commit()

    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    with pytest.raises(GuidedRecoveryError):
        await create_session(scope, "nonexistent-project-id")


@pytest.mark.asyncio
async def test_create_session_cross_tenant_project_not_found(db_session: AsyncSession):
    """Project belongs to another tenant → should raise not found."""
    project = await _seed_project(db_session, tenant_id="other-tenant")
    await _seed_workflow(db_session)
    await db_session.commit()

    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    with pytest.raises(GuidedRecoveryError):
        await create_session(scope, project.id)


# ── list_sessions ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_sessions_empty(db_session: AsyncSession):
    project = await _seed_project(db_session)
    await _seed_workflow(db_session)
    await db_session.commit()

    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    result = await list_sessions(scope, project.id)
    assert result.total == 0
    assert result.items == []
    assert result.pages == 0


@pytest.mark.asyncio
async def test_list_sessions_with_items(db_session: AsyncSession):
    project = await _seed_project(db_session)
    wf = await _seed_workflow(db_session)
    await _seed_session(db_session, project.id, wf.id)
    await _seed_session(db_session, project.id, wf.id)
    await db_session.commit()

    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    result = await list_sessions(scope, project.id)
    assert result.total == 2
    assert len(result.items) == 2


@pytest.mark.asyncio
async def test_list_sessions_pagination(db_session: AsyncSession):
    project = await _seed_project(db_session)
    wf = await _seed_workflow(db_session)
    for _ in range(5):
        await _seed_session(db_session, project.id, wf.id)
    await db_session.commit()

    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    result = await list_sessions(scope, project.id, page=1, size=2)
    assert result.total == 5
    assert len(result.items) == 2
    assert result.pages == 3


@pytest.mark.asyncio
async def test_list_sessions_with_status_filter(db_session: AsyncSession):
    project = await _seed_project(db_session)
    wf = await _seed_workflow(db_session)
    s1 = await _seed_session(db_session, project.id, wf.id)
    s1.status = "paused"
    await _seed_session(db_session, project.id, wf.id)  # active
    await db_session.commit()

    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    result = await list_sessions(scope, project.id, status=["paused"])
    assert result.total == 1
    assert result.items[0].status == "paused"


@pytest.mark.asyncio
async def test_list_sessions_cross_tenant_isolation(db_session: AsyncSession):
    project = await _seed_project(db_session, tenant_id="other-tenant")
    wf = await _seed_workflow(db_session)
    await _seed_session(db_session, project.id, wf.id, tenant_id="other-tenant")
    await db_session.commit()

    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    result = await list_sessions(scope, project.id)
    assert result.total == 0


# ── get_session ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_session_success(db_session: AsyncSession):
    project = await _seed_project(db_session)
    wf = await _seed_workflow(db_session)
    session = await _seed_session(db_session, project.id, wf.id)
    await db_session.commit()

    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    result = await get_session(scope, session.id)
    assert result.id == session.id
    assert result.message_count == 0


@pytest.mark.asyncio
async def test_get_session_not_found(db_session: AsyncSession):
    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    with pytest.raises(GuidedRecoveryError):
        await get_session(scope, "nonexistent-id")


@pytest.mark.asyncio
async def test_get_session_cross_tenant(db_session: AsyncSession):
    project = await _seed_project(db_session, tenant_id="other-tenant")
    wf = await _seed_workflow(db_session)
    session = await _seed_session(db_session, project.id, wf.id, tenant_id="other-tenant")
    await db_session.commit()

    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    with pytest.raises(GuidedRecoveryError):
        await get_session(scope, session.id)


# ── update_session ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_session_status(db_session: AsyncSession):
    project = await _seed_project(db_session)
    wf = await _seed_workflow(db_session)
    session = await _seed_session(db_session, project.id, wf.id)
    await db_session.commit()

    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    payload = SessionUpdate(status="paused")
    result = await update_session(scope, session.id, payload)
    assert result.status == "paused"


@pytest.mark.asyncio
async def test_update_session_not_found(db_session: AsyncSession):
    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    payload = SessionUpdate(status="paused")
    with pytest.raises(GuidedRecoveryError):
        await update_session(scope, "nonexistent-id", payload)


# ── add_message ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_message_success(db_session: AsyncSession):
    project = await _seed_project(db_session)
    wf = await _seed_workflow(db_session)
    session = await _seed_session(db_session, project.id, wf.id)
    await db_session.commit()

    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    payload = MessageCreate(content="Hello AI!", role="user")
    result = await add_message(scope, session.id, payload)
    assert result.content == "Hello AI!"
    assert result.role == "user"
    assert result.message_index == 0
    assert result.session_id == session.id
    assert result.tenant_id == TENANT_ID


@pytest.mark.asyncio
async def test_add_message_index_increments(db_session: AsyncSession):
    project = await _seed_project(db_session)
    wf = await _seed_workflow(db_session)
    session = await _seed_session(db_session, project.id, wf.id)
    await db_session.commit()

    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    msg0 = await add_message(scope, session.id, MessageCreate(content="First"))
    msg1 = await add_message(scope, session.id, MessageCreate(content="Second"))
    msg2 = await add_message(scope, session.id, MessageCreate(content="Third"))

    assert msg0.message_index == 0
    assert msg1.message_index == 1
    assert msg2.message_index == 2


@pytest.mark.asyncio
async def test_add_message_session_not_found(db_session: AsyncSession):
    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    payload = MessageCreate(content="Hello!")
    with pytest.raises(GuidedRecoveryError):
        await add_message(scope, "nonexistent-session", payload)


# ── list_messages ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_messages_empty(db_session: AsyncSession):
    project = await _seed_project(db_session)
    wf = await _seed_workflow(db_session)
    session = await _seed_session(db_session, project.id, wf.id)
    await db_session.commit()

    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    result = await list_messages(scope, session.id)
    assert result.total == 0
    assert result.items == []


@pytest.mark.asyncio
async def test_list_messages_with_pagination(db_session: AsyncSession):
    project = await _seed_project(db_session)
    wf = await _seed_workflow(db_session)
    session = await _seed_session(db_session, project.id, wf.id)
    await db_session.commit()

    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    for i in range(5):
        await add_message(scope, session.id, MessageCreate(content=f"Msg {i}"))

    result = await list_messages(scope, session.id, page=1, size=2)
    assert result.total == 5
    assert len(result.items) == 2
    assert result.pages == 3


@pytest.mark.asyncio
async def test_list_messages_session_not_found(db_session: AsyncSession):
    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    with pytest.raises(GuidedRecoveryError):
        await list_messages(scope, "nonexistent-session")


@pytest.mark.asyncio
async def test_list_messages_ordered_by_index(db_session: AsyncSession):
    project = await _seed_project(db_session)
    wf = await _seed_workflow(db_session)
    session = await _seed_session(db_session, project.id, wf.id)
    await db_session.commit()

    scope = TenantScope(db=db_session, tenant_id=TENANT_ID)
    await add_message(scope, session.id, MessageCreate(content="First"))
    await add_message(scope, session.id, MessageCreate(content="Second"))
    await add_message(scope, session.id, MessageCreate(content="Third"))

    result = await list_messages(scope, session.id)
    assert result.items[0].content == "First"
    assert result.items[1].content == "Second"
    assert result.items[2].content == "Third"
