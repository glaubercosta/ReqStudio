"""Project business logic with TenantScope enforcement (Story 3.1)."""

import math
from datetime import datetime

from sqlalchemy import func, select

from app.core.exceptions import not_found_error
from app.db.tenant import TenantScope
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
    offset = (page - 1) * size

    # Conta total (com filtro de status)
    count_stmt = (
        select(func.count())
        .select_from(Project)
        .where(Project.tenant_id == scope.tenant_id)
        .where(Project.status == status)
    )
    total: int = await scope.db.scalar(count_stmt) or 0

    # Busca página
    stmt = scope.select(Project, Project.status == status).offset(offset).limit(size)
    rows = await scope.db.scalars(stmt)
    items = [ProjectResponse.model_validate(p) for p in rows]

    return ProjectListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total > 0 else 0,
    )


async def get_project(scope: TenantScope, project_id: str) -> ProjectResponse:
    """Busca projeto por ID. Retorna 404 para IDs de outros tenants."""
    project = await scope.db.scalar(scope.where_id(Project, project_id))
    if not project:
        raise not_found_error("projeto")
    return ProjectResponse.model_validate(project)


async def update_project(
    scope: TenantScope,
    project_id: str,
    payload: ProjectUpdate,
) -> ProjectResponse:
    """Atualiza campos do projeto. Retorna 404 para IDs de outros tenants."""
    project = await scope.db.scalar(scope.where_id(Project, project_id))
    if not project:
        raise not_found_error("projeto")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(project, field, value)

    project.updated_at = datetime.utcnow().replace(microsecond=0)
    await scope.db.commit()
    await scope.db.refresh(project)
    return ProjectResponse.model_validate(project)
