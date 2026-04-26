"""Shared database utilities for common service patterns."""

from datetime import datetime

from pydantic import BaseModel

from app.db.base import Base


def apply_partial_update(entity: Base, payload: BaseModel) -> None:
    """Apply a partial update from a Pydantic schema to a SQLAlchemy model.

    Encapsulates the repeated pattern:
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(entity, field, value)
        entity.updated_at = datetime.utcnow().replace(microsecond=0)

    Args:
        entity:  SQLAlchemy model instance to update.
        payload: Pydantic schema with only set fields to apply.
    """
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(entity, field, value)
    if hasattr(entity, "updated_at"):
        entity.updated_at = datetime.utcnow().replace(microsecond=0)  # type: ignore[assignment]
