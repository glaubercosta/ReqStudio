from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, create_refresh_token
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterResponse,
    TokenData,
    UserCreate,
    UserResponse,
)
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

REFRESH_TOKEN_COOKIE = "refresh_token"


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registro de novo usuário",
)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    """POST /api/v1/auth/register."""
    service = AuthService(db)
    user = await service.register(payload)
    return RegisterResponse(
        data=UserResponse(id=user.id, email=user.email, tenant_id=user.tenant_id)
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login e emissão de tokens JWT",
)
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """POST /api/v1/auth/login."""
    service = AuthService(db)
    user = await service.authenticate(payload.email, payload.password)

    access_token = create_access_token(user_id=user.id, tenant_id=user.tenant_id)
    refresh_token = create_refresh_token(user_id=user.id)

    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/v1/auth/refresh",
    )

    return LoginResponse(data=TokenData(access_token=access_token))


@router.get(
    "/me",
    response_model=RegisterResponse,
    summary="Retorna dados do usuário autenticado",
)
async def me(current_user: User = Depends(get_current_user)) -> RegisterResponse:
    """GET /api/v1/auth/me — requer Bearer token válido."""
    return RegisterResponse(
        data=UserResponse(
            id=current_user.id,
            email=current_user.email,
            tenant_id=current_user.tenant_id,
        )
    )
