"""Global error handlers for FastAPI.

Registra handlers para:
  - GuidedRecoveryError  → serializa no formato { "error": {...} }
  - RequestValidationError → converte em GuidedRecoveryError VALIDATION_ERROR
  - HTTPException        → converte em GuidedRecoveryError quando possível
  - Exception genérica   → INTERNAL_ERROR com log de segurança
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    ErrorCode,
    GuidedRecoveryError,
    Severity,
    internal_error,
    validation_error,
)

logger = logging.getLogger(__name__)

# Mapeamento HTTP status → ErrorCode para erros genéricos
_HTTP_CODE_MAP: dict[int, ErrorCode] = {
    401: ErrorCode.UNAUTHORIZED,
    403: ErrorCode.FORBIDDEN,
    404: ErrorCode.RESOURCE_NOT_FOUND,
    429: ErrorCode.RATE_LIMIT_EXCEEDED,
}


def register_error_handlers(app: FastAPI) -> None:
    """Registra todos os error handlers na instância FastAPI."""

    @app.exception_handler(GuidedRecoveryError)
    async def guided_recovery_handler(
        request: Request, exc: GuidedRecoveryError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        logger.warning(
            "GuidedRecoveryError",
            extra={
                "error_code": exc.code,
                "severity": exc.severity,
                "request_id": request_id,
                "path": str(request.url),
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
            headers={"X-Request-ID": request_id},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        detail = "; ".join(
            f"{' → '.join(str(loc) for loc in err['loc'])}: {err['msg']}"
            for err in exc.errors()
        )
        err = validation_error(detail)
        request_id = getattr(request.state, "request_id", "unknown")
        return JSONResponse(
            status_code=err.status_code,
            content=err.to_dict(),
            headers={"X-Request-ID": request_id},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        error_code = _HTTP_CODE_MAP.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
        err = GuidedRecoveryError(
            code=error_code,
            message=str(exc.detail),
            help="Se o problema persistir, entre em contato com o suporte.",
            actions=[{"label": "Voltar ao início", "route": "/"}],
            severity=Severity.RECOVERABLE,
            status_code=exc.status_code,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=err.to_dict(),
            headers={"X-Request-ID": request_id},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        logger.exception(
            "Unhandled exception",
            extra={"request_id": request_id, "path": str(request.url)},
        )

        # Never expose internal exception details to clients, even in DEBUG.
        # The exception is already logged above via logger.exception().
        err = internal_error(detail="")

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=err.to_dict(),
            headers={"X-Request-ID": request_id},
        )
