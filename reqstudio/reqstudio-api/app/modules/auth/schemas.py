"""Auth Pydantic schemas — Story 2.1 + Story 2.2."""

from pydantic import BaseModel, EmailStr, field_validator

from app.core.exceptions import ErrorCode, GuidedRecoveryError, Severity

# ── Story 2.1: Registro ───────────────────────────────────────────────────────


class UserCreate(BaseModel):
    """Payload para registro de novo usuário."""

    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise GuidedRecoveryError(
                code=ErrorCode.WEAK_PASSWORD,
                message="A senha deve ter pelo menos 8 caracteres.",
                help="Escolha uma senha com 8 ou mais caracteres para proteger sua conta.",
                actions=[],
                severity=Severity.WARNING,
                status_code=422,
            )
        return v


class UserResponse(BaseModel):
    """Resposta após registro bem-sucedido."""

    id: str
    email: str
    tenant_id: str

    model_config = {"from_attributes": True}


class RegisterResponse(BaseModel):
    """Envelope de resposta do registro."""

    data: UserResponse


# ── Story 2.2: Login ──────────────────────────────────────────────────────────


class LoginRequest(BaseModel):
    """Payload de login."""

    email: EmailStr
    password: str


class TokenData(BaseModel):
    """Token de acesso retornado no corpo da response."""

    access_token: str
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    """Envelope de resposta do login."""

    data: TokenData
