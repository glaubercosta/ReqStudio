"""FastAPI application factory — atualizado na Story 1.4.

Inclui:
  - RequestIdMiddleware e TenantMiddleware
  - GuidedRecovery error handlers
  - Rate limiting via slowapi
  - CORS configurável via settings
  - OpenTelemetry / structured logging
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.error_handlers import register_error_handlers
from app.core.middleware import RequestIdMiddleware, TenantMiddleware
from app.core.telemetry import setup_telemetry
from app.db.migrations import run_migrations_on_startup
from app.modules.auth.router import router as auth_router
from app.modules.documents.router import router as documents_router
from app.modules.projects.router import router as projects_router
from app.modules.sessions.router import router as sessions_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG001
    """Application lifespan: run startup tasks before yielding to handlers."""
    # Run Alembic in a worker thread to avoid nested event-loop issues.
    await asyncio.to_thread(run_migrations_on_startup)
    yield
    # shutdown logic goes here if needed in the future


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    # Telemetria e logging estruturado antes de tudo
    setup_telemetry()

    app = FastAPI(
        title="ReqStudio API",
        description="Plataforma de elicitação de requisitos assistida por IA",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # --- Rate Limiting (slowapi) ---
    try:
        from slowapi import Limiter, _rate_limit_exceeded_handler
        from slowapi.errors import RateLimitExceeded
        from slowapi.util import get_remote_address

        limiter = Limiter(key_func=get_remote_address)
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        logger.info("Rate limiting enabled via slowapi")
    except ImportError:
        logger.warning("slowapi not installed — rate limiting disabled")

    # --- CORS ---
    origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.modules.artifacts.router import router as artifacts_router

    # --- Custom Middleware ---
    app.add_middleware(TenantMiddleware)
    app.add_middleware(RequestIdMiddleware)

    # --- Global Error Handlers ---
    register_error_handlers(app)

    # --- Routes ---
    app.include_router(auth_router)
    app.include_router(projects_router, prefix="/api/v1")
    app.include_router(documents_router, prefix="/api/v1")
    app.include_router(sessions_router, prefix="/api/v1")
    app.include_router(artifacts_router, prefix="/api/v1")

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "ok"}

    logger.info("ReqStudio API created", extra={"debug": settings.DEBUG})
    return app


app = create_app()
