"""Document Pydantic schemas (Story 4.1 + 4.2)."""

from datetime import datetime

from pydantic import BaseModel


class DocumentChunkResponse(BaseModel):
    id: str
    chunk_index: int
    content: str

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    id: str
    project_id: str
    filename: str
    mime_type: str
    size_bytes: int
    status: str
    chunk_count: int
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
