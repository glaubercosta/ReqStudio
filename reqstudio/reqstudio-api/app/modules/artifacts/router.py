"""Artifacts API Router — Story 6.1, 6.2, 6.3, 6.4.

Endpoints for CRUD, Versioning, Rendering, Coverage and Export.
"""

from time import perf_counter

from fastapi import APIRouter, Depends, Query, Response

from app.db.tenant import TenantScope, get_tenant_scope
from app.modules.artifacts.schemas import (
    ArtifactCoverageResponse,
    ArtifactCreate,
    ArtifactRenderResponse,
    ArtifactResponse,
    ArtifactUpdate,
    ArtifactVersionResponse,
)
from app.modules.artifacts.service import (
    create_artifact,
    get_artifact,
    get_artifact_coverage,
    get_artifact_export,
    get_artifact_markdown,
    get_artifact_versions,
    get_project_artifacts,
    update_artifact,
)
from app.schemas.response import ApiResponse

router = APIRouter(prefix="/artifacts", tags=["Artifacts"])


@router.post("/", response_model=ApiResponse[ArtifactResponse])
async def route_create_artifact(
    data: ArtifactCreate, scope: TenantScope = Depends(get_tenant_scope)
) -> ApiResponse:
    """Cria um novo artefato (Story 6.1)."""
    artifact = await create_artifact(scope, data)
    return ApiResponse(data=artifact)


@router.get("/project/{project_id}", response_model=ApiResponse[list[ArtifactResponse]])
async def route_get_project_artifacts(
    project_id: str, scope: TenantScope = Depends(get_tenant_scope)
) -> ApiResponse:
    """Lista todos os artefatos de um projeto."""
    artifacts = await get_project_artifacts(scope, project_id)
    return ApiResponse(data=artifacts)


@router.get("/{artifact_id}", response_model=ApiResponse[ArtifactResponse])
async def route_get_artifact(
    artifact_id: str, scope: TenantScope = Depends(get_tenant_scope)
) -> ApiResponse:
    """Recupera o estado atual de um artefato."""
    artifact = await get_artifact(scope, artifact_id)
    return ApiResponse(data=artifact)


@router.get("/{artifact_id}/render", response_model=ApiResponse[ArtifactRenderResponse])
async def route_render_artifact(
    artifact_id: str,
    view: str = Query("business", pattern="^(business|technical)$"),
    show_ids: bool = Query(False),
    scope: TenantScope = Depends(get_tenant_scope),
) -> ApiResponse:
    """Renderiza o artefato em Markdown (visão 'business' ou 'technical')."""
    md = await get_artifact_markdown(
        scope,
        artifact_id,
        view=view,
        show_business_ids=show_ids,
    )
    return ApiResponse(data={"markdown": md})


@router.get("/{artifact_id}/coverage", response_model=ApiResponse[ArtifactCoverageResponse])
async def route_get_artifact_coverage(
    artifact_id: str, scope: TenantScope = Depends(get_tenant_scope)
) -> ApiResponse:
    """Retorna dados detalhados de cobertura (total e por seção)."""
    coverage = await get_artifact_coverage(scope, artifact_id)
    return ApiResponse(data=coverage)


@router.get("/{artifact_id}/export")
async def route_export_artifact(
    artifact_id: str,
    export_format: str = Query("markdown", alias="format", pattern="^(markdown|json)$"),
    view: str = Query("business", pattern="^(business|technical)$"),
    show_ids: bool = Query(False),
    scope: TenantScope = Depends(get_tenant_scope),
) -> Response:
    """Exporta o artefato para download (Markdown ou JSON)."""
    start = perf_counter()
    content, filename = await get_artifact_export(
        scope,
        artifact_id,
        export_format=export_format,
        view=view,
        show_business_ids=show_ids,
    )
    duration_ms = (perf_counter() - start) * 1000

    media_type = "text/markdown" if export_format == "markdown" else "application/json"

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Export-Duration-Ms": f"{duration_ms:.2f}",
        },
    )


@router.get("/{artifact_id}/versions", response_model=ApiResponse[list[ArtifactVersionResponse]])
async def route_get_versions(
    artifact_id: str, scope: TenantScope = Depends(get_tenant_scope)
) -> ApiResponse:
    """Recupera o histórico de versões/snapshots do artefato."""
    versions = await get_artifact_versions(scope, artifact_id)
    return ApiResponse(data=versions)


@router.post("/{artifact_id}/update", response_model=ApiResponse[ArtifactResponse])
async def route_update_artifact(
    artifact_id: str, data: ArtifactUpdate, scope: TenantScope = Depends(get_tenant_scope)
) -> ApiResponse:
    """Atualiza o estado do artefato e gera nova versão (AC 5)."""
    artifact = await update_artifact(scope, artifact_id, data)
    return ApiResponse(data=artifact)
