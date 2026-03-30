"""Global test fixtures.

Provides:
- AsyncClient for testing FastAPI endpoints
- In-memory SQLite async database (isolado do PostgreSQL de produção)
- Tenant IDs for multi-tenant isolation tests
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base  # noqa: F401 — imports all models via base.py
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
