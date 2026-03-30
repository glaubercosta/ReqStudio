"""Global test fixtures.

Provides:
- AsyncClient for testing FastAPI endpoints
- In-memory SQLite async database (isolado do PostgreSQL de produção)
- Tenant IDs for multi-tenant isolation tests
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.modules.auth.models import RefreshToken, Tenant, User  # noqa: F401 — registers models in Base.metadata
from app.db.session import get_db
from app.main import app

# Fixed UUIDs for deterministic multi-tenant tests
TENANT_A_ID = "550e8400-e29b-41d4-a716-446655440001"
TENANT_B_ID = "550e8400-e29b-41d4-a716-446655440002"

# In-memory SQLite for tests (sem necessidade de PostgreSQL rodando)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
def tenant_a_id() -> str:
    """Tenant A identifier for isolation tests."""
    return TENANT_A_ID


@pytest.fixture
def tenant_b_id() -> str:
    """Tenant B identifier for isolation tests."""
    return TENANT_B_ID


@pytest.fixture
async def db_session():
    """Async SQLite in-memory session for unit tests."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    """Async HTTP client with overridden DB dependency (SQLite in-memory)."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Multi-tenant fixtures (Story 2.4) ─────────────────────────────────────────

_USER_A = {"email": "tenant_a@example.com", "password": "senhaA1234"}
_USER_B = {"email": "tenant_b@example.com", "password": "senhaB1234"}


@pytest.fixture
async def tenant_a_token(client: AsyncClient) -> dict[str, str]:
    """Registra usuário A e retorna {'access_token': ..., 'tenant_id': ...}."""
    reg = await client.post("/api/v1/auth/register", json=_USER_A)
    assert reg.status_code == 201, f"Register A failed: {reg.text}"
    tenant_id = reg.json()["data"]["tenant_id"]

    login = await client.post("/api/v1/auth/login", json=_USER_A)
    assert login.status_code == 200, f"Login A failed: {login.text}"
    return {"access_token": login.json()["data"]["access_token"], "tenant_id": tenant_id}


@pytest.fixture
async def tenant_b_token(client: AsyncClient) -> dict[str, str]:
    """Registra usuário B e retorna {'access_token': ..., 'tenant_id': ...}."""
    reg = await client.post("/api/v1/auth/register", json=_USER_B)
    assert reg.status_code == 201, f"Register B failed: {reg.text}"
    tenant_id = reg.json()["data"]["tenant_id"]

    login = await client.post("/api/v1/auth/login", json=_USER_B)
    assert login.status_code == 200, f"Login B failed: {login.text}"
    return {"access_token": login.json()["data"]["access_token"], "tenant_id": tenant_id}
