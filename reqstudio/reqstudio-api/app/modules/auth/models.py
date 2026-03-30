"""Auth domain models: User e Tenant.

Tenant é criado automaticamente no registro de usuário (Story 2.1).
RefreshToken será adicionado na Story 2.3.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Tenant(Base):
    """Tenant — unidade de isolamento de dados (organização/conta)."""

    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    # Relacionamento (não carregado por padrão)
    users: Mapped[list["User"]] = relationship("User", back_populates="tenant")


class User(Base):
    """User — conta de acesso ao ReqStudio.

    tenant_id referencia Tenant. Toda query de negócio filtra por tenant_id.
    Senha nunca armazenada em texto plano — apenas hashed_password (bcrypt).
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
