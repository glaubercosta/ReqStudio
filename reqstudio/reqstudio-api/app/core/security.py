"""Password hashing and JWT token utilities.

bcrypt: hashing direto (sem passlib — incompatível com bcrypt 4.x).
JWT: python-jose com algoritmo HS256.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


# ── Password ──────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Gera hash bcrypt de uma senha em texto plano."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha em texto plano corresponde ao hash bcrypt."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ── JWT ───────────────────────────────────────────────────────────────────────

def _make_token(extra_claims: dict[str, Any], expires_delta: timedelta) -> str:
    """Base interna para criação de JWTs."""
    now = datetime.now(timezone.utc)
    payload = {
        **extra_claims,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: str, tenant_id: str) -> str:
    """Cria access token JWT com claims user_id e tenant_id.

    Expira em ACCESS_TOKEN_EXPIRE_MINUTES (default: 15min).
    """
    return _make_token(
        extra_claims={"sub": user_id, "tenant_id": tenant_id, "type": "access"},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: str) -> str:
    """Cria refresh token JWT com sub=user_id.

    Expira em REFRESH_TOKEN_EXPIRE_DAYS (default: 7d).
    Rotation e reuse detection implementados na Story 2.3.
    """
    return _make_token(
        extra_claims={"sub": user_id, "type": "refresh"},
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decodifica e valida um JWT.

    Raises:
        JWTError: se token inválido, expirado ou assinatura incorreta.
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
