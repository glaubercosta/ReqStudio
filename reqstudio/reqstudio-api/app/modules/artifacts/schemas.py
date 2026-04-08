"""Artifact schemas using Pydantic v2 for data validation and API response (Story 6.1).

Defines the canonical structure of artifact_state and API envelopes.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.artifacts.models import (
    ARTIFACT_STATUS_COMPLETE,
    ARTIFACT_STATUS_DRAFT,
    ARTIFACT_TYPE_PRD,
    ARTIFACT_TYPE_TECHNICAL_SPEC,
    ARTIFACT_TYPE_USER_STORIES,
)


class ArtifactSection(BaseModel):
    """Representa uma seção estruturada dentro do artefato."""
    
    id: str = Field(..., description="Identificador único da seção (ex: 'func-reqs')")
    title: str = Field(..., description="Título visível da seção")
    content: str = Field("", description="Conteúdo em Markdown")
    coverage: float = Field(0.0, ge=0.0, le=1.0, description="Nível de exploração/certeza (0.0 a 1.0)")
    sources: list[str] = Field(default_factory=list, description="Lista de Message IDs que sustentam esta seção")
    last_updated: datetime | None = None


class ArtifactState(BaseModel):
    """Estado canônico completo do artefato (Serializado como JSONB)."""

    class ArtifactMetadata(BaseModel):
        """Metadados agregados do artefato."""

        total_coverage: float = Field(0.0, ge=0.0, le=1.0)

    sections: list[ArtifactSection] = Field(default_factory=list)
    metadata: ArtifactMetadata = Field(default_factory=ArtifactMetadata)

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_total_coverage(cls, raw: Any) -> Any:
        """Mantém compatibilidade com payload legado que usa total_coverage na raiz."""
        if not isinstance(raw, dict):
            return raw

        metadata = raw.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}

        if "total_coverage" not in metadata and "total_coverage" in raw:
            metadata["total_coverage"] = raw["total_coverage"]

        raw["metadata"] = metadata
        return raw


class ArtifactCreate(BaseModel):
    """Schema para criação inicial de um artefato."""

    project_id: str
    session_id: str | None = None
    artifact_type: Literal[
        ARTIFACT_TYPE_PRD,
        ARTIFACT_TYPE_USER_STORIES,
        ARTIFACT_TYPE_TECHNICAL_SPEC,
    ]
    title: str


class ArtifactUpdate(BaseModel):
    """Schema para atualização de estado do artefato."""

    artifact_state: ArtifactState
    change_reason: str | None = None
    changed_by: str | None = None
    status: Literal[ARTIFACT_STATUS_DRAFT, ARTIFACT_STATUS_COMPLETE] | None = None


class ArtifactResponse(BaseModel):
    """Schema completo de resposta do artefato."""
    
    id: str
    project_id: str
    session_id: str | None
    artifact_type: str
    title: str
    artifact_state: ArtifactState
    coverage_data: dict[str, Any] | None
    version: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArtifactVersionResponse(BaseModel):
    """Schema de resposta para histórico de versões."""
    
    id: str
    artifact_id: str
    version: int
    state_snapshot: ArtifactState
    change_reason: str | None
    changed_by: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArtifactRenderResponse(BaseModel):
    """Schema para resposta de renderização Markdown."""
    
    markdown: str


class ArtifactSectionCoverage(BaseModel):
    """Resumo de cobertura por seção."""
    id: str
    title: str
    coverage: float
    coverage_band: Literal["low", "medium", "high"]
    card_state: Literal["pending", "active", "complete"]


class ArtifactCoverageResponse(BaseModel):
    """Schema para resposta de cobertura detalhada."""
    artifact_id: str
    total_coverage: float
    sections: list[ArtifactSectionCoverage]
