"""Auth service — Story 2.1 (registro) + Story 2.2 (login) + Story 2.3 (refresh)."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ErrorCode, GuidedRecoveryError, Severity
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.modules.auth.models import RefreshToken, Tenant, User
from app.modules.auth.schemas import UserCreate

logger = logging.getLogger(__name__)


class AuthService:
    """Serviço de autenticação e registro."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Story 2.1: Registro ───────────────────────────────────────────────────

    async def register(self, payload: UserCreate) -> User:
        """Registra novo usuário criando Tenant e User atomicamente."""
        existing = await self.db.scalar(select(User).where(User.email == payload.email))
        if existing:
            raise GuidedRecoveryError(
                code=ErrorCode.EMAIL_ALREADY_EXISTS,
                message="Este e-mail já está cadastrado.",
                help="Use outro e-mail ou faça login se já tem uma conta.",
                actions=[{"label": "Fazer login", "route": "/login"}],
                severity=Severity.WARNING,
                status_code=400,
            )

        tenant = Tenant(name=payload.email.split("@")[0])
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

    # ── Story 2.2: Login ──────────────────────────────────────────────────────

    async def authenticate(self, email: str, password: str) -> tuple[User, str]:
        """Valida credenciais, cria RefreshToken e retorna (user, refresh_token_jwt).

        Raises:
            GuidedRecoveryError: INVALID_CREDENTIALS se credenciais inválidas.
        """
        user = await self.db.scalar(select(User).where(User.email == email))
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

        refresh_jwt = create_refresh_token(user_id=user.id)
        await self._persist_refresh_token(user_id=user.id, token=refresh_jwt)

        logger.info("User authenticated", extra={"user_id": user.id})
        return user, refresh_jwt

    async def _persist_refresh_token(self, user_id: str, token: str) -> RefreshToken:
        """Persiste um RefreshToken no banco (armazena apenas o hash)."""
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        rt = RefreshToken(
            user_id=user_id,
            token_hash=hash_token(token),
            expires_at=expires_at,
        )
        self.db.add(rt)
        await self.db.flush()
        return rt

    # ── Story 2.3: Refresh com Rotation ──────────────────────────────────────

    async def refresh(self, refresh_jwt: str) -> tuple[str, str]:
        """Emite novos tokens com rotation e detecção de reuse.

        Args:
            refresh_jwt: JWT do refresh_token recebido do cookie.

        Returns:
            Tuple (access_token, new_refresh_token).

        Raises:
            GuidedRecoveryError: SESSION_EXPIRED se token expirado ou inválido.
            GuidedRecoveryError: TOKEN_REUSE_DETECTED se token já foi usado.
        """
        from jose import JWTError

        # 1. Validar assinatura e expiração do JWT
        try:
            payload = decode_token(refresh_jwt)
        except JWTError:
            raise GuidedRecoveryError(
                code=ErrorCode.SESSION_EXPIRED,
                message="Sua sessão expirou.",
                help="Faça login novamente para continuar.",
                actions=[{"label": "Fazer login", "route": "/login"}],
                severity=Severity.CRITICAL,
                status_code=401,
            )

        if payload.get("type") != "refresh":
            raise GuidedRecoveryError(
                code=ErrorCode.SESSION_EXPIRED,
                message="Token inválido.",
                help="Faça login novamente.",
                actions=[],
                severity=Severity.CRITICAL,
                status_code=401,
            )

        # 2. Buscar token no banco pelo hash
        token_hash = hash_token(refresh_jwt)
        rt = await self.db.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )

        if not rt:
            raise GuidedRecoveryError(
                code=ErrorCode.SESSION_EXPIRED,
                message="Token de sessão não encontrado.",
                help="Faça login novamente.",
                actions=[{"label": "Fazer login", "route": "/login"}],
                severity=Severity.CRITICAL,
                status_code=401,
            )

        # 3. Reuse detection: token já foi usado → comprometimento de segurança
        if rt.used_at is not None:
            logger.warning(
                "Refresh token reuse detected — revoking all user tokens",
                extra={"user_id": rt.user_id, "token_id": rt.id},
            )
            await self._revoke_all_user_tokens(rt.user_id)
            raise GuidedRecoveryError(
                code=ErrorCode.TOKEN_REUSE_DETECTED,
                message="Atividade suspeita detectada na sua conta.",
                help="Por segurança, todas as sessões foram encerradas. Faça login novamente.",
                actions=[{"label": "Fazer login", "route": "/login"}],
                severity=Severity.CRITICAL,
                status_code=401,
            )

        # 4. Verificar se foi revogado
        if rt.revoked_at is not None:
            raise GuidedRecoveryError(
                code=ErrorCode.SESSION_EXPIRED,
                message="Sessão encerrada.",
                help="Faça login novamente para continuar.",
                actions=[{"label": "Fazer login", "route": "/login"}],
                severity=Severity.CRITICAL,
                status_code=401,
            )

        # 5. Verificar expiração (dupla verificação — JWT já valida, mas banco é fonte de verdade)
        if not rt.is_valid:
            raise GuidedRecoveryError(
                code=ErrorCode.SESSION_EXPIRED,
                message="Sua sessão expirou.",
                help="Faça login novamente para continuar.",
                actions=[{"label": "Fazer login", "route": "/login"}],
                severity=Severity.CRITICAL,
                status_code=401,
            )

        # 6. Rotation: marcar token atual como usado e criar novo
        rt.used_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.db.flush()

        user_id = rt.user_id
        user = await self.db.get(User, user_id)
        if not user or not user.is_active:
            raise GuidedRecoveryError(
                code=ErrorCode.SESSION_EXPIRED,
                message="Usuário não encontrado.",
                help="Faça login novamente.",
                actions=[],
                severity=Severity.CRITICAL,
                status_code=401,
            )

        new_access_token = create_access_token(user_id=user.id, tenant_id=user.tenant_id)
        new_refresh_jwt = create_refresh_token(user_id=user.id)
        await self._persist_refresh_token(user_id=user.id, token=new_refresh_jwt)

        await self.db.commit()

        logger.info("Token refreshed (rotation)", extra={"user_id": user.id})
        return new_access_token, new_refresh_jwt

    async def _revoke_all_user_tokens(self, user_id: str) -> None:
        """Revoga todos os refresh tokens ativos de um usuário."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await self.db.commit()
