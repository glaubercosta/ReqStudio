"""Cross-cutting middleware: RequestId e Tenant.

RequestIdMiddleware — injeta UUID no header X-Request-ID de toda request/response.
TenantMiddleware   — extrai tenant_id do JWT access token (Story 2.2).
"""

import logging
import uuid

from jose import JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Adiciona um UUID único a cada request via header X-Request-ID.

    Se o cliente já enviar X-Request-ID, o valor é preservado.
    O mesmo ID é ecoado na response para rastreabilidade end-to-end.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class TenantMiddleware(BaseHTTPMiddleware):
    """Extrai e valida o tenant_id de cada request via JWT.

    O tenant_id é extraído do claim ``tenant_id`` do access token JWT
    presente no header ``Authorization: Bearer <token>``.

    Rotas públicas (listadas em SKIP_PATHS / SKIP_PREFIXES) não requerem tenant.
    """

    SKIP_PATHS: set[str] = {
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    SKIP_PREFIXES: tuple[str, ...] = (
        "/api/v1/auth/",
    )

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        if path in self.SKIP_PATHS or path.startswith(self.SKIP_PREFIXES):
            return await call_next(request)

        # Extract tenant_id from JWT access token (not from client header)
        tenant_id: str | None = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ").strip()
            try:
                from app.core.security import decode_token

                payload = decode_token(token)
                tenant_id = payload.get("tenant_id")
            except (JWTError, Exception):
                # Auth errors are handled by the endpoint dependencies;
                # middleware just sets tenant_id to None for unauthenticated requests.
                pass

        request.state.tenant_id = tenant_id
        return await call_next(request)
