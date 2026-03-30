from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class TenantMixin:
    """Mixin that adds tenant_id to all business models.

    Every query MUST filter by tenant_id.
    Tested via multi-tenant fixture in conftest.py.
    """

    tenant_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )


# Import all models here so Alembic can discover them via Base.metadata
# noqa: E402 — imports after class definitions are intentional
from app.modules.auth.models import RefreshToken, Tenant, User  # noqa: F401, E402
