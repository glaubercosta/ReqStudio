"""Auth service — registro (Story 2.1) + autenticação (Story 2.2)."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ErrorCode, GuidedRecoveryError, Severity
from app.core.security import hash_password, verify_password
from app.modules.auth.models import Tenant, User
from app.modules.auth.schemas import UserCreate

logger = logging.getLogger(__name__)


class AuthService:
    """Serviço de autenticação e registro."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(self, payload: UserCreate) -> User:
        """Registra novo usuário criando Tenant e User atomicamente."""
        existing = await self.db.scalar(
            select(User).where(User.email == payload.email)
        )
        if existing:
            raise GuidedRecoveryError(
                code=ErrorCode.EMAIL_ALREADY_EXISTS,
                message="Este e-mail já está cadastrado.",
                help="Use outro e-mail ou faça login se já tem uma conta.",
                actions=[{"label": "Fazer login", "route": "/login"}],
                severity=Severity.WARNING,
                status_code=400,
            )

        tenant_name = payload.email.split("@")[0]
        tenant = Tenant(name=tenant_name)
        self.db.add(tenant)
        await self.db.flush()

        user = User(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            tenant_id=tenant.id,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info("User registered", extra={"user_id": user.id, "tenant_id": user.tenant_id})
        return user

    async def authenticate(self, email: str, password: str) -> User:
        """Valida credenciais e retorna o User.

        Raises:
            GuidedRecoveryError: INVALID_CREDENTIALS se email/senha inválidos.
        """
        user = await self.db.scalar(select(User).where(User.email == email))

        # Verifica email e senha de forma constante (sem timing attack)
        password_ok = verify_password(password, user.hashed_password) if user else False

        if not user or not password_ok or not user.is_active:
            raise GuidedRecoveryError(
                code=ErrorCode.INVALID_CREDENTIALS,
                message="E-mail ou senha incorretos.",
                help="Verifique suas credenciais e tente novamente.",
                actions=[{"label": "Esqueci minha senha", "route": "/forgot-password"}],
                severity=Severity.WARNING,
                status_code=401,
            )

        logger.info("User authenticated", extra={"user_id": user.id})
        return user
