"""Pydantic schemas for Sessions and Messages CRUD (Story 5.1)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.sessions.models import VALID_MESSAGE_ROLES, VALID_SESSION_STATUSES
from app.schemas.response import PaginatedList


# ── Session Schemas ───────────────────────────────────────────────────────────


class SessionCreateBody(BaseModel):
    """Body do POST — project_id vem da URL, não do body."""

    workflow_id: str | None = Field(None, description="ID do workflow (default: briefing)")


class SessionUpdate(BaseModel):
    status: str | None = Field(None, description="active | paused | completed")

    def model_post_init(self, __context: Any) -> None:  # noqa: ANN401
        if self.status is not None and self.status not in VALID_SESSION_STATUSES:
            raise ValueError(f"status deve ser um de: {VALID_SESSION_STATUSES}")


class SessionResponse(BaseModel):
    id: str
    project_id: str
    tenant_id: str
    workflow_id: str
    workflow_position: dict[str, Any] | None
    status: str
    artifact_state: dict[str, Any] | None
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Backward-compatible alias — existing routers reference this name.
SessionListResponse = PaginatedList[SessionResponse]


# ── Message Schemas ───────────────────────────────────────────────────────────


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=50000, description="Conteúdo da mensagem")
    role: str = Field(default="user", description="user | assistant | system")

    def model_post_init(self, __context: Any) -> None:  # noqa: ANN401
        if self.role not in VALID_MESSAGE_ROLES:
            raise ValueError(f"role deve ser um de: {VALID_MESSAGE_ROLES}")


class MessageResponse(BaseModel):
    id: str
    session_id: str
    tenant_id: str
    role: str
    content: str
    message_index: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    latency_ms: float | None = None
    model: str | None = None
    metadata_: dict[str, Any] | None = Field(None, alias="metadata_")
    created_at: datetime

    model_config = {"from_attributes": True}


# Backward-compatible alias — existing routers reference this name.
MessageListResponse = PaginatedList[MessageResponse]
