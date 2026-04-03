"""Artifact schemas using Pydantic v2 for data validation and API response (Story 6.1).

Defines the canonical structure of artifact_state and API envelopes.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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
    
    sections: list[ArtifactSection] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    total_coverage: float = Field(0.0, ge=0.0, le=1.0)


class ArtifactCreate(BaseModel):
    """Schema para criação inicial de um artefato."""
    
    project_id: str
    session_id: str | None = None
    artifact_type: str
    title: str


class ArtifactUpdate(BaseModel):
    """Schema para atualização de estado do artefato."""
    
    artifact_state: ArtifactState
    change_reason: str | None = None
    status: str | None = None


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


class ArtifactCoverageResponse(BaseModel):
    """Schema para resposta de cobertura detalhada."""
    artifact_id: str
    total_coverage: float
    sections: list[ArtifactSectionCoverage]
