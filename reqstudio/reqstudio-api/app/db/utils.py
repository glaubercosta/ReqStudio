"""Shared database utilities for common service patterns."""

from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import inspect

from app.db.base import Base


def apply_partial_update(entity: Base, payload: BaseModel) -> None:
    """Apply a partial update from a Pydantic schema to a SQLAlchemy model.

    Encapsulates the repeated pattern:
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(entity, field, value)
        entity.updated_at = datetime.utcnow().replace(microsecond=0)

    Validates that every field in the payload corresponds to a mapped column
    on the entity — a divergent name would otherwise silently set an unmapped
    attribute (the bug this guard exists to prevent).

    Args:
        entity:  SQLAlchemy model instance to update.
        payload: Pydantic schema with only set fields to apply.

    Raises:
        ValueError: if any payload field has no corresponding column on the entity.
    """
    data = payload.model_dump(exclude_unset=True)
    if data:
        valid_attrs = {a.key for a in inspect(type(entity)).mapper.column_attrs}
        unknown = set(data.keys()) - valid_attrs
        if unknown:
            raise ValueError(
                f"apply_partial_update: schema fields {sorted(unknown)} "
                f"are not mapped columns on {type(entity).__name__}. "
                "Drop them from the *Update schema or apply them manually."
            )
    for field, value in data.items():
        setattr(entity, field, value)
    if hasattr(entity, "updated_at"):
        entity.updated_at = datetime.utcnow().replace(microsecond=0)  # type: ignore[assignment]
