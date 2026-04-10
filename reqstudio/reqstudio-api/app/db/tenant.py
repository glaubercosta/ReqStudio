"""TenantScope — Utilitário de isolamento multi-tenant (Story 2.4).

Toda query de negócio DEVE usar TenantScope.select() para garantir
que dados de um tenant não sejam acessíveis por outro.

Uso típico em um endpoint:

    @router.get("/projects")
    async def list_projects(
        scope: TenantScope = Depends(get_tenant_scope),
    ):
        projects = await scope.db.scalars(scope.select(Project))
        return list(projects)

Isso garante que o filtro `tenant_id == scope.tenant_id` esteja
**sempre** presente, impedindo leakage de dados cross-tenant.
"""

from typing import Any, Type

from fastapi import Depends
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.core.dependencies import get_tenant_id
from app.db.session import get_db


class TenantScope:
    """Encapsula AsyncSession com filtro automático por tenant_id.

    Substitui o uso direto de `select(Model)` em endpoints de negócio.
    Garante que todo acesso a dados respeite a fronteira do tenant.

    Attributes:
        db:        Sessão AsyncSQL (injetável via Depends)
        tenant_id: ID do tenant extraído do JWT

    Anti-patterns (PROIBIDOS):
        - `select(Project)` sem filtro → vazamento cross-tenant
        - `db.scalar(select(Project).where(Project.id == id))` sem tenant_id
    """

    def __init__(self, db: AsyncSession, tenant_id: str) -> None:
        self.db = db
        self.tenant_id = tenant_id

    def select(self, model: Type[Any], *extra_filters: Any) -> Select:
        """Constrói uma query SELECT com where(Model.tenant_id == self.tenant_id).

        Args:
            model:          Classe SQLAlchemy com atributo `tenant_id`
            extra_filters:  Filtros adicionais (ex: Model.status == "active")

        Returns:
            Select com filtro de tenant aplicado.

        Example:
            # Busca projects do tenant autenticado com status active
            stmt = scope.select(Project, Project.status == "active")
            projects = await scope.db.scalars(stmt)

        Raises:
            AttributeError: se o model não tiver `tenant_id` (indica TenantMixin ausente)
        """
        if not hasattr(model, "tenant_id"):
            raise AttributeError(
                f"Model {model.__name__} não possui tenant_id. "
                "Aplique TenantMixin para garantir isolamento multi-tenant."
            )

        stmt = sa_select(model).where(model.tenant_id == self.tenant_id)
        for f in extra_filters:
            stmt = stmt.where(f)
        return stmt

    def where_id(self, model: Type[Any], record_id: str) -> Select:
        """Constrói SELECT por ID com filtro de tenant.

        Retorna 404 implícito: se o ID não pertencer ao tenant,
        o resultado será vazio — nunca um 403, conforme architecture.md.

        Example:
            project = await scope.db.scalar(scope.where_id(Project, project_id))
            if not project:
                raise not_found_error("projeto")
        """
        return self.select(model).where(model.id == record_id)

    async def get_or_404(self, model: Type[Any], record_id: str, label: str = "recurso") -> Any:
        """Busca registro por ID no tenant ou levanta 404.

        Encapsula o padrão repetido:
            obj = await scope.db.scalar(scope.where_id(Model, id))
            if not obj:
                raise not_found_error("label")

        Args:
            model:     Classe SQLAlchemy com TenantMixin
            record_id: UUID do registro
            label:     Nome amigável para mensagem de erro (ex: "projeto", "sessão")

        Returns:
            A instância do modelo encontrada.

        Raises:
            GuidedRecoveryError: 404 se não encontrado ou pertence a outro tenant.
        """
        from app.core.exceptions import not_found_error

        obj = await self.db.scalar(self.where_id(model, record_id))
        if not obj:
            raise not_found_error(label)
        return obj


async def get_tenant_scope(
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
) -> TenantScope:
    """FastAPI dependency: retorna TenantScope com tenant_id do JWT.

    Injete em qualquer endpoint que acesse dados de negócio:

        @router.get("/projects")
        async def list_projects(scope: TenantScope = Depends(get_tenant_scope)):
            ...
    """
    return TenantScope(db=db, tenant_id=tenant_id)
