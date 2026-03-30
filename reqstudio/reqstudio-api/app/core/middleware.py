"""Cross-cutting middleware: RequestId e Tenant.

RequestIdMiddleware — injeta UUID no header X-Request-ID de toda request/response.
TenantMiddleware   — placeholder: extrai X-Tenant-ID do header (JWT na Story 2.2).
"""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


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
    """Extrai e valida o tenant_id de cada request.

    MVP (Story 1.4): lê o header X-Tenant-ID como placeholder.
    Story 2.2: substituir por extração do JWT claim `tenant_id`.

    Rotas públicas (listadas em SKIP_PATHS) não requerem tenant.
    """

    SKIP_PATHS: set[str] = {
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        # TODO (Story 2.2): extrair tenant_id do JWT access token
        tenant_id = request.headers.get("X-Tenant-ID")
        request.state.tenant_id = tenant_id

        return await call_next(request)
