"""Projects router — CRUD endpoints (Story 3.1)."""

from fastapi import APIRouter, Depends, Query

from app.db.tenant import TenantScope, get_tenant_scope
from app.modules.projects import service
from app.modules.projects.schemas import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.schemas.response import ApiResponse

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ApiResponse[ProjectResponse], status_code=201)
async def create_project(
    payload: ProjectCreate,
    scope: TenantScope = Depends(get_tenant_scope),
) -> ApiResponse[ProjectResponse]:
    project = await service.create_project(scope, payload)
    return ApiResponse(data=project)


@router.get("", response_model=ApiResponse[ProjectListResponse])
async def list_projects(
    status: str = Query(default="active", description="active | archived"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    scope: TenantScope = Depends(get_tenant_scope),
) -> ApiResponse[ProjectListResponse]:
    result = await service.list_projects(scope, status=status, page=page, size=size)
    return ApiResponse(data=result)


@router.get("/{project_id}", response_model=ApiResponse[ProjectResponse])
async def get_project(
    project_id: str,
    scope: TenantScope = Depends(get_tenant_scope),
) -> ApiResponse[ProjectResponse]:
    project = await service.get_project(scope, project_id)
    return ApiResponse(data=project)


@router.patch("/{project_id}", response_model=ApiResponse[ProjectResponse])
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    scope: TenantScope = Depends(get_tenant_scope),
) -> ApiResponse[ProjectResponse]:
    project = await service.update_project(scope, project_id, payload)
    return ApiResponse(data=project)
