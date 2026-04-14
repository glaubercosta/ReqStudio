"""Testes dos error handlers — Story 1.4 AC#3, #4, #5."""

import pytest
from httpx import AsyncClient

from app.core.exceptions import (
    ErrorCode,
    GuidedRecoveryError,
    Severity,
    internal_error,
    session_expired_error,
    validation_error,
)

# --- Unit tests: GuidedRecoveryError ---


def test_guided_recovery_error_to_dict():
    """AC#3: GuidedRecoveryError serializa corretamente."""
    err = GuidedRecoveryError(
        code=ErrorCode.SESSION_EXPIRED,
        message="Sessão expirada.",
        help="Volte à lista de projetos.",
        actions=[{"label": "Voltar", "route": "/projects"}],
        severity=Severity.RECOVERABLE,
        status_code=401,
    )
    d = err.to_dict()
    assert "error" in d
    assert d["error"]["code"] == ErrorCode.SESSION_EXPIRED
    assert d["error"]["message"] == "Sessão expirada."
    assert d["error"]["help"] == "Volte à lista de projetos."
    assert d["error"]["severity"] == Severity.RECOVERABLE
    assert len(d["error"]["actions"]) == 1


def test_error_code_enum_has_required_codes():
    """AC#5: Catálogo contém códigos iniciais obrigatórios."""
    assert ErrorCode.SESSION_EXPIRED == "SESSION_EXPIRED"
    assert ErrorCode.VALIDATION_ERROR == "VALIDATION_ERROR"
    assert ErrorCode.INTERNAL_ERROR == "INTERNAL_ERROR"


def test_factory_functions_produce_valid_errors():
    """Factories produzem erros válidos com todos os campos."""
    for err in [session_expired_error(), internal_error(), validation_error("campo inválido")]:
        d = err.to_dict()
        assert "code" in d["error"]
        assert "message" in d["error"]
        assert "help" in d["error"]
        assert "actions" in d["error"]
        assert "severity" in d["error"]


# --- Integration tests: error handlers via HTTP ---


@pytest.mark.asyncio
async def test_404_returns_guided_recovery(client: AsyncClient):
    """AC#4: Rotas inexistentes retornam formato Guided Recovery."""
    response = await client.get("/nonexistent-route")
    assert response.status_code == 404
    body = response.json()
    assert "error" in body
    assert "code" in body["error"]
    assert "message" in body["error"]
    assert "help" in body["error"]


@pytest.mark.asyncio
async def test_error_response_includes_request_id(client: AsyncClient):
    """AC#1 + AC#4: Error responses incluem X-Request-ID no header."""
    response = await client.get("/nonexistent-route")
    assert "x-request-id" in response.headers


@pytest.mark.asyncio
async def test_health_returns_200_not_error(client: AsyncClient):
    """Smoke: /health não aciona nenhum error handler."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
