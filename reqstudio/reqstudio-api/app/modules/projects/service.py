"""Project business logic with TenantScope enforcement (Story 3.1)."""

from app.db.pagination import paginate
from app.db.tenant import TenantScope
from app.db.utils import apply_partial_update
from app.modules.projects.models import PROJECT_STATUS_ACTIVE, Project
from app.modules.projects.schemas import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)


async def create_project(scope: TenantScope, payload: ProjectCreate) -> ProjectResponse:
    """Cria um projeto vinculado ao tenant autenticado."""
    project = Project(
        name=payload.name,
        description=payload.description,
        business_domain=payload.business_domain,
        tenant_id=scope.tenant_id,
        status=PROJECT_STATUS_ACTIVE,
    )
    scope.db.add(project)
    await scope.db.commit()
    await scope.db.refresh(project)
    return ProjectResponse.model_validate(project)


async def list_projects(
    scope: TenantScope,
    status: str = PROJECT_STATUS_ACTIVE,
    page: int = 1,
    size: int = 20,
) -> ProjectListResponse:
    """Lista projetos do tenant com paginação e filtro por status."""
    return await paginate(
        scope=scope,
        model=Project,
        response_cls=ProjectResponse,
        page=page,
        size=size,
        extra_filters=[Project.status == status],
    )


async def get_project(scope: TenantScope, project_id: str) -> ProjectResponse:
    """Busca projeto por ID. Retorna 404 para IDs de outros tenants."""
    project = await scope.get_or_404(Project, project_id, "projeto")
    return ProjectResponse.model_validate(project)


async def update_project(
    scope: TenantScope,
    project_id: str,
    payload: ProjectUpdate,
) -> ProjectResponse:
    """Atualiza campos do projeto. Retorna 404 para IDs de outros tenants."""
    project = await scope.get_or_404(Project, project_id, "projeto")
    apply_partial_update(project, payload)
    await scope.db.commit()
    await scope.db.refresh(project)
    return ProjectResponse.model_validate(project)
