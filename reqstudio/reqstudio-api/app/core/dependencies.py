"""FastAPI dependencies — autenticação e acesso ao banco.

get_db:           sessão async de banco (SQLAlchemy)
get_current_user: extrai User autenticado do JWT no header Authorization
get_tenant_id:    extrai tenant_id do JWT (atalho sem carregar o User do banco)
"""

import logging

from fastapi import Depends, Header
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ErrorCode, GuidedRecoveryError, Severity
from app.core.security import decode_token
from app.db.session import get_db
from app.modules.auth.models import User

logger = logging.getLogger(__name__)


def _extract_bearer(authorization: str | None) -> str:
    """Extrai o token do header Authorization: Bearer <token>."""
    if not authorization or not authorization.startswith("Bearer "):
        raise GuidedRecoveryError(
            code=ErrorCode.UNAUTHORIZED,
            message="Autenticação necessária.",
            help="Faça login para acessar este recurso.",
            actions=[{"label": "Fazer login", "route": "/login"}],
            severity=Severity.CRITICAL,
            status_code=401,
        )
    return authorization.removeprefix("Bearer ").strip()


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency: retorna o User autenticado a partir do JWT.

    Raises:
        GuidedRecoveryError: UNAUTHORIZED se token ausente/inválido.
        GuidedRecoveryError: TOKEN_EXPIRED se token expirado.
    """
    token = _extract_bearer(authorization)

    try:
        payload = decode_token(token)
    except JWTError:
        raise GuidedRecoveryError(
            code=ErrorCode.TOKEN_EXPIRED,
            message="Sua sessão expirou.",
            help="Faça login novamente para continuar.",
            actions=[{"label": "Fazer login", "route": "/login"}],
            severity=Severity.CRITICAL,
            status_code=401,
        )

    if payload.get("type") != "access":
        raise GuidedRecoveryError(
            code=ErrorCode.UNAUTHORIZED,
            message="Token de acesso inválido.",
            help="Use o token de acesso retornado no login.",
            actions=[],
            severity=Severity.CRITICAL,
            status_code=401,
        )

    user_id: str = payload["sub"]
    user = await db.scalar(select(User).where(User.id == user_id))

    if not user or not user.is_active:
        raise GuidedRecoveryError(
            code=ErrorCode.UNAUTHORIZED,
            message="Usuário não encontrado ou inativo.",
            help="Entre em contato com o suporte se o problema persistir.",
            actions=[],
            severity=Severity.CRITICAL,
            status_code=401,
        )

    return user


async def get_tenant_id(
    authorization: str | None = Header(default=None),
) -> str:
    """Dependency leve: extrai apenas o tenant_id do JWT sem ir ao banco."""
    token = _extract_bearer(authorization)

    try:
        payload = decode_token(token)
    except JWTError:
        raise GuidedRecoveryError(
            code=ErrorCode.TOKEN_EXPIRED,
            message="Sua sessão expirou.",
            help="Faça login novamente para continuar.",
            actions=[{"label": "Fazer login", "route": "/login"}],
            severity=Severity.CRITICAL,
            status_code=401,
        )

    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        raise GuidedRecoveryError(
            code=ErrorCode.UNAUTHORIZED,
            message="Token sem informação de tenant.",
            help="Faça login novamente.",
            actions=[],
            severity=Severity.CRITICAL,
            status_code=401,
        )

    return tenant_id
