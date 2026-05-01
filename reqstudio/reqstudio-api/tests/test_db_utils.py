"""Unit tests for app/db/utils.py — column-vs-field guard on apply_partial_update."""

import pytest
from pydantic import BaseModel

from app.db.utils import apply_partial_update
from app.modules.projects.models import Project


class _ValidUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class _DivergentUpdate(BaseModel):
    """A field that has no corresponding column on Project."""

    not_a_column: str | None = None


def test_apply_partial_update_writes_set_fields():
    project = Project(id="x", name="old", tenant_id="t-1", status="active")
    payload = _ValidUpdate(name="new")

    apply_partial_update(project, payload)

    assert project.name == "new"


def test_apply_partial_update_skips_unset_fields():
    project = Project(
        id="x", name="kept", description="kept-desc", tenant_id="t-1", status="active"
    )
    payload = _ValidUpdate(name="new")  # description not set

    apply_partial_update(project, payload)

    assert project.name == "new"
    assert project.description == "kept-desc"


def test_apply_partial_update_rejects_field_with_no_column():
    project = Project(id="x", name="n", tenant_id="t-1", status="active")
    payload = _DivergentUpdate(not_a_column="value")

    with pytest.raises(ValueError, match="not_a_column"):
        apply_partial_update(project, payload)


def test_apply_partial_update_no_op_on_empty_payload():
    project = Project(id="x", name="n", tenant_id="t-1", status="active")
    payload = _ValidUpdate()  # no fields set

    apply_partial_update(project, payload)  # should not raise

    assert project.name == "n"
