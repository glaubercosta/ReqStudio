"""Pydantic schemas for Project CRUD (Story 3.1)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.projects.models import VALID_STATUSES


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Nome do projeto")
    description: str | None = Field(None, max_length=2000)
    business_domain: str | None = Field(None, max_length=100)


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    business_domain: str | None = None
    status: str | None = Field(None, description="active | archived")
    progress_summary: dict[str, Any] | None = None

    def model_post_init(self, __context: Any) -> None:  # noqa: ANN401
        if self.status is not None and self.status not in VALID_STATUSES:
            raise ValueError(f"status deve ser um de: {VALID_STATUSES}")


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str | None
    business_domain: str | None
    status: str
    progress_summary: dict[str, Any] | None
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int
    size: int
    pages: int
