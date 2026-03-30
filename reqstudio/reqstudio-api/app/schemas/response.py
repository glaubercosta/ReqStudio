"""Shared response wrappers for consistent API envelope (Story 3.1)."""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Envelope padrão da API ReqStudio.

    Todo endpoint retorna `{ "data": <T> }` para consistência.
    Erros retornam `{ "error": { ... } }` via GuidedRecoveryError.
    """

    data: T
