"""Shared pagination helpers to eliminate repeated offset/count/pages logic.

Usage in a service function:

    from app.db.pagination import paginate

    async def list_projects(scope, status, page, size):
        base_filter = Project.status == status
        return await paginate(
            scope=scope,
            model=Project,
            response_cls=ProjectResponse,
            page=page,
            size=size,
            extra_filters=[base_filter],
        )
"""

import math
from collections.abc import Callable, Sequence
from typing import Any, TypeVar

from sqlalchemy import func, select
from sqlalchemy.sql import Select

from app.db.tenant import TenantScope
from app.schemas.response import PaginatedList

ResponseT = TypeVar("ResponseT")


async def paginate(
    scope: TenantScope,
    model: type[Any],
    response_cls: type[ResponseT],
    page: int = 1,
    size: int = 20,
    extra_filters: Sequence[Any] | None = None,
    order_by: Any | None = None,
    row_mapper: Callable[..., ResponseT] | None = None,
) -> PaginatedList[ResponseT]:
    """Execute a paginated tenant-scoped query and return a PaginatedList.

    Args:
        scope:          TenantScope with db session and tenant_id.
        model:          SQLAlchemy model class (must have TenantMixin).
        response_cls:   Pydantic schema class for items (used with model_validate
                        unless row_mapper is provided).
        page:           1-based page number.
        size:           Page size.
        extra_filters:  Additional SQLAlchemy where-clauses beyond tenant_id.
        order_by:       Optional column expression to order by (e.g. Model.created_at.desc()).
        row_mapper:     Optional custom function to map a model row to response_cls.
                        If not provided, uses ``response_cls.model_validate(row)``.

    Returns:
        PaginatedList[ResponseT] with items, total, page, size, pages.
    """
    filters = list(extra_filters or [])
    offset = (page - 1) * size

    # Count total matching rows
    count_stmt = (
        select(func.count())
        .select_from(model)
        .where(model.tenant_id == scope.tenant_id)
    )
    for f in filters:
        count_stmt = count_stmt.where(f)
    total: int = await scope.db.scalar(count_stmt) or 0

    # Fetch page
    stmt: Select = scope.select(model, *filters)
    if order_by is not None:
        stmt = stmt.order_by(order_by)
    stmt = stmt.offset(offset).limit(size)
    rows = await scope.db.scalars(stmt)

    mapper = row_mapper or (lambda row: response_cls.model_validate(row))
    items = [mapper(row) for row in rows]

    return PaginatedList(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total > 0 else 0,
    )
