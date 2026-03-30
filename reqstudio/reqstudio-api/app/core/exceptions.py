"""Guided Recovery Error system.

Todo erro visível ao usuário DEVE ser um GuidedRecoveryError.
Erros sem `help` e `actions` são proibidos (ver architecture.md § Anti-patterns).
"""

from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    """Catálogo de códigos de erro do ReqStudio.

    Story 1.4: catálogo inicial.
    Epics subsequentes adicionam novos códigos conforme necessário.
    """

    # --- Sessão ---
    SESSION_EXPIRED = "SESSION_EXPIRED"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"

    # --- Validação ---
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_PAYLOAD = "INVALID_PAYLOAD"

    # --- Auth (Story 2.x) ---
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    EMAIL_ALREADY_EXISTS = "EMAIL_ALREADY_EXISTS"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    WEAK_PASSWORD = "WEAK_PASSWORD"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_REUSE_DETECTED = "TOKEN_REUSE_DETECTED"  # Story 2.3

    # --- Tenant ---
    TENANT_NOT_FOUND = "TENANT_NOT_FOUND"
    TENANT_ISOLATION_VIOLATION = "TENANT_ISOLATION_VIOLATION"

    # --- Recursos ---
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # --- Infraestrutura ---
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    LLM_UNAVAILABLE = "LLM_UNAVAILABLE"


class Severity(StrEnum):
    """Severidade do erro para o frontend renderizar o feedback adequado."""

    RECOVERABLE = "recoverable"   # Usuário pode tentar de novo
    WARNING = "warning"           # Atenção mas não bloqueia
    CRITICAL = "critical"         # Requer intervenção (ex: re-login)


class GuidedRecoveryError(Exception):
    """Erro estruturado que guia o usuário para a recuperação.

    Todo erro visível ao usuário deve ser lançado como GuidedRecoveryError.
    O error_handlers.py serializa este objeto no formato:
        { "error": { "code": ..., "message": ..., "help": ...,
                     "actions": [...], "severity": ... } }

    Attrs:
        code:     ErrorCode enum — identificador único do erro
        message:  Mensagem amigável em linguagem de negócio (não técnica)
        help:     Explicação do que está acontecendo e o que o usuário pode fazer
        actions:  Lista de ações sugeridas com label e route/action
        severity: Nível de severidade para renderização no frontend
        status_code: HTTP status code da response (default: 400)
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        help: str,  # noqa: A002
        actions: list[dict[str, Any]] | None = None,
        severity: Severity = Severity.RECOVERABLE,
        status_code: int = 400,
    ) -> None:
        self.code = code
        self.message = message
        self.help = help
        self.actions = actions or []
        self.severity = severity
        self.status_code = status_code
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Serializa para o formato de erro da API."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "help": self.help,
                "actions": self.actions,
                "severity": self.severity,
            }
        }


# ---------------------------------------------------------------------------
# Erros pré-definidos (use como factory para consistência)
# ---------------------------------------------------------------------------

def session_expired_error() -> GuidedRecoveryError:
    return GuidedRecoveryError(
        code=ErrorCode.SESSION_EXPIRED,
        message="Sua sessão de trabalho expirou por inatividade.",
        help="Sessões são preservadas automaticamente. Volte à lista de projetos para retomar de onde parou.",
        actions=[
            {"label": "Voltar aos projetos", "route": "/projects"},
            {"label": "Tentar novamente", "action": "retry"},
        ],
        severity=Severity.RECOVERABLE,
        status_code=401,
    )


def internal_error(detail: str = "") -> GuidedRecoveryError:
    return GuidedRecoveryError(
        code=ErrorCode.INTERNAL_ERROR,
        message="Ocorreu um erro inesperado.",
        help=f"Instabilidade temporária. Sua sessão está segura. Tente novamente em alguns segundos.{' (' + detail + ')' if detail else ''}",
        actions=[
            {"label": "Tentar novamente", "action": "retry"},
        ],
        severity=Severity.RECOVERABLE,
        status_code=500,
    )


def validation_error(detail: str) -> GuidedRecoveryError:
    return GuidedRecoveryError(
        code=ErrorCode.VALIDATION_ERROR,
        message="Os dados enviados são inválidos.",
        help=detail,
        actions=[],
        severity=Severity.WARNING,
        status_code=422,
    )


def rate_limit_error() -> GuidedRecoveryError:
    return GuidedRecoveryError(
        code=ErrorCode.RATE_LIMIT_EXCEEDED,
        message="Muitas requisições em curto período.",
        help="Aguarde alguns segundos e tente novamente.",
        actions=[{"label": "Tentar novamente", "action": "retry"}],
        severity=Severity.WARNING,
        status_code=429,
    )
