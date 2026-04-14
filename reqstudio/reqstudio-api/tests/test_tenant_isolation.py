"""Testes de isolamento multi-tenant — Story 2.4.

Valida que TenantScope garante que dados de um tenant
jamais sejam acessíveis por outro.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tenant import TenantScope

# ── Testes unitários do TenantScope ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_tenant_scope_select_filters_by_tenant(db_session: AsyncSession):
    """AC#1: TenantScope.select() aplica where(Model.tenant_id == tenant_id)."""
    from app.modules.auth.models import User

    scope = TenantScope(db=db_session, tenant_id="tenant-abc")
    stmt = scope.select(User)

    # Verifica que o SQL compilado contém o filtro de tenant
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "tenant-abc" in compiled


@pytest.mark.asyncio
async def test_tenant_scope_where_id_includes_tenant_filter(db_session: AsyncSession):
    """AC#1: where_id() combina filtro de tenant e id."""
    from app.modules.auth.models import User

    scope = TenantScope(db=db_session, tenant_id="t-123")
    stmt = scope.where_id(User, "user-456")

    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "t-123" in compiled
    assert "user-456" in compiled


@pytest.mark.asyncio
async def test_tenant_scope_raises_for_model_without_tenant_id(db_session: AsyncSession):
    """AC#5: model sem tenant_id levanta AttributeError (TenantMixin ausente)."""
    from sqlalchemy.orm import Mapped, mapped_column

    from app.db.base import Base

    class ModelSemTenant(Base):
        __tablename__ = "sem_tenant_test"
        id: Mapped[str] = mapped_column(primary_key=True)

    scope = TenantScope(db=db_session, tenant_id="t-xxx")
    with pytest.raises(AttributeError, match="tenant_id"):
        scope.select(ModelSemTenant)


# ── Testes de isolamento via API ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_tenant_a_data_not_visible_to_tenant_b(
    client: AsyncClient,
    tenant_a_token: dict[str, str],
    tenant_b_token: dict[str, str],
):
    """AC#4: /me de tenant A não retorna dados de tenant B."""
    # Tenant A acessa /me
    resp_a = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tenant_a_token['access_token']}"},
    )
    assert resp_a.status_code == 200
    user_a = resp_a.json()["data"]
    assert user_a["tenant_id"] == tenant_a_token["tenant_id"]

    # Tenant B acessa /me
    resp_b = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tenant_b_token['access_token']}"},
    )
    assert resp_b.status_code == 200
    user_b = resp_b.json()["data"]
    assert user_b["tenant_id"] == tenant_b_token["tenant_id"]

    # Garantir que os tenant_ids são diferentes
    assert user_a["tenant_id"] != user_b["tenant_id"]
    assert user_a["id"] != user_b["id"]


@pytest.mark.asyncio
async def test_tenant_ids_are_unique_per_user(
    client: AsyncClient,
    tenant_a_token: dict[str, str],
    tenant_b_token: dict[str, str],
):
    """AC#4: cada usuário tem seu próprio tenant — nenhum compartilhamento."""
    assert tenant_a_token["tenant_id"] != tenant_b_token["tenant_id"]


@pytest.mark.asyncio
async def test_token_contains_correct_tenant_id(
    client: AsyncClient,
    tenant_a_token: dict[str, str],
):
    """AC#2: JWT do tenant A embute o tenant_id correto nos claims."""
    from jose import jwt

    from app.core.config import settings

    payload = jwt.decode(
        tenant_a_token["access_token"],
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    assert payload["tenant_id"] == tenant_a_token["tenant_id"]


@pytest.mark.asyncio
async def test_tenant_scope_dependency_requires_auth(client: AsyncClient):
    """AC#2: get_tenant_scope requer JWT válido — sem token → 401."""
    # GET /me sem token = TenantScope indisponível
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"
