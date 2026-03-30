from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class TenantMixin:
    """Mixin that adds tenant_id to all business models.

    Every query MUST filter by tenant_id.
    Use TenantScope (app/db/tenant.py) to enforce this automatically.
    """

    tenant_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )

# NOTE: models are NOT imported here to avoid circular imports.
# Import them explicitly wherever metadata discovery is needed:
#   - tests/conftest.py
#   - alembic/env.py
