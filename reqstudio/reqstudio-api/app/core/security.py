"""Password hashing and JWT token utilities.

bcrypt: hashing direto (sem passlib — incompatível com bcrypt 4.x).
JWT: python-jose com algoritmo HS256.
jti (JWT ID): UUID adicionado ao refresh token para garantir unicidade
              mesmo quando dois tokens são criados no mesmo segundo.
"""

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any
from uuid import uuid4

import bcrypt
from jose import jwt

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


def hash_token(token: str) -> str:
    """Retorna SHA-256 hex do token — para armazenamento seguro no banco.

    Nunca armazene o token bruto. Armazene apenas o hash.
    """
    return sha256(token.encode("utf-8")).hexdigest()


# ── JWT ───────────────────────────────────────────────────────────────────────


def _make_token(extra_claims: dict[str, Any], expires_delta: timedelta) -> str:
    """Base interna para criação de JWTs."""
    now = datetime.now(UTC)
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
    """Cria refresh token JWT com sub=user_id e jti único.

    jti (JWT ID) é um UUID que garante unicidade mesmo criado no mesmo segundo.
    Expira em REFRESH_TOKEN_EXPIRE_DAYS (default: 7d).
    """
    return _make_token(
        extra_claims={
            "sub": user_id,
            "type": "refresh",
            "jti": str(uuid4()),  # garante hash único mesmo criado no mesmo instante
        },
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
