"""Auth domain models: User, Tenant, RefreshToken.

RefreshToken adicionado na Story 2.3 (rotation + reuse detection).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    """UTC now como naive datetime (compatível com SQLite em testes)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Tenant(Base):
    """Tenant — unidade de isolamento de dados."""

    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    users: Mapped[list["User"]] = relationship("User", back_populates="tenant")


class User(Base):
    """User — conta de acesso ao ReqStudio."""

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
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )


class RefreshToken(Base):
    """RefreshToken — registro stateful de refresh tokens (Story 2.3).

    Armazena apenas o SHA-256 hash do token, nunca o token bruto.

    Lifecycle:
        - Criado no login e no refresh (rotation)
        - used_at preenchido quando token é consumido no refresh
        - revoked_at preenchido quando token é revogado (reuse detection)
        - Reuse detection: se used_at já está preenchido → compromisso de segurança
          → revoga TODOS os tokens do user
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    @property
    def is_valid(self) -> bool:
        """True se token não foi usado, não foi revogado e não expirou."""
        # Usa naive UTC para compatibilidade com SQLite (testes) e PostgreSQL (produção)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        expires = self.expires_at
        if expires.tzinfo is not None:
            expires = expires.replace(tzinfo=None)
        return (
            self.used_at is None
            and self.revoked_at is None
            and expires > now
        )
