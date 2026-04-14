"""Artifact business logic with TenantScope, versioning and coverage (Story 6.1, 6.3).

Handles CRUD for Artifacts, automatic snapshotting and coverage calculation.
"""

import json
import re
from collections.abc import Sequence
from typing import Any

from sqlalchemy import desc, select

from app.core.exceptions import not_found_error
from app.db.tenant import TenantScope
from app.modules.artifacts.models import ARTIFACT_STATUS_DRAFT, Artifact, ArtifactVersion
from app.modules.artifacts.renderers.markdown import render_artifact_to_markdown
from app.modules.artifacts.schemas import ArtifactCreate, ArtifactState, ArtifactUpdate
from app.modules.projects.models import Project

LOW_COVERAGE_THRESHOLD = 0.3
HIGH_COVERAGE_THRESHOLD = 0.7


def _slugify_filename_part(value: str) -> str:
    """Normaliza fragmentos de filename para download cross-browser."""
    slug = value.strip().lower().replace(" ", "_")
    slug = re.sub(r"[^a-z0-9_-]", "", slug)
    slug = re.sub(r"_+", "_", slug)
    return slug or "artifact"


def _clamp_coverage(value: float) -> float:
    """Normaliza cobertura para faixa [0.0, 1.0] com 2 casas."""
    return round(min(max(value, 0.0), 1.0), 2)


def _coverage_band(coverage: float) -> str:
    """Faixa de cobertura para mapeamento visual (UX-DR4)."""
    if coverage < LOW_COVERAGE_THRESHOLD:
        return "low"
    if coverage <= HIGH_COVERAGE_THRESHOLD:
        return "medium"
    return "high"


def _card_state(coverage: float) -> str:
    """Estado por seção/card para consumo em UI."""
    if coverage < LOW_COVERAGE_THRESHOLD:
        return "pending"
    if coverage <= HIGH_COVERAGE_THRESHOLD:
        return "active"
    return "complete"


def _calculate_coverage_snapshot(state: ArtifactState) -> dict[str, Any]:
    """Calcula cobertura total e por seção de forma determinística."""
    sections_snapshot: list[dict[str, Any]] = []
    for section in state.sections:
        normalized_coverage = _clamp_coverage(section.coverage)
        sections_snapshot.append(
            {
                "id": section.id,
                "title": section.title,
                "coverage": normalized_coverage,
                "coverage_band": _coverage_band(normalized_coverage),
                "card_state": _card_state(normalized_coverage),
            }
        )

    if not sections_snapshot:
        total_coverage = 0.0
    else:
        total_coverage = round(
            sum(s["coverage"] for s in sections_snapshot) / len(sections_snapshot),
            2,
        )

    return {
        "total_coverage": total_coverage,
        "sections": sections_snapshot,
    }


async def create_artifact(scope: TenantScope, data: ArtifactCreate) -> Artifact:
    """Cria um novo artefato para um projeto."""
    project = await scope.db.scalar(scope.where_id(Project, data.project_id))
    if not project:
        raise not_found_error("projeto")

    initial_state = {"sections": [], "metadata": {"total_coverage": 0.0}}
    artifact = Artifact(
        project_id=data.project_id,
        session_id=data.session_id,
        tenant_id=scope.tenant_id,
        artifact_type=data.artifact_type,
        title=data.title,
        artifact_state=initial_state,
        version=1,
        status=ARTIFACT_STATUS_DRAFT,
    )

    scope.db.add(artifact)
    await scope.db.flush()

    # Criar versão inicial (Snapshot 1)
    version = ArtifactVersion(
        artifact_id=artifact.id,
        tenant_id=scope.tenant_id,
        version=1,
        state_snapshot=artifact.artifact_state,
        change_reason="Criação inicial",
    )
    scope.db.add(version)

    return artifact


async def get_artifact(scope: TenantScope, artifact_id: str) -> Artifact:
    """Recupera um artefato pelo ID com isolamento de tenant."""
    artifact = await scope.db.scalar(scope.where_id(Artifact, artifact_id))
    if not artifact:
        raise not_found_error("artefato")
    return artifact


async def update_artifact(scope: TenantScope, artifact_id: str, data: ArtifactUpdate) -> Artifact:
    """Atualiza o estado do artefato, recalcula cobertura e gera nova versão."""
    artifact = await get_artifact(scope, artifact_id)

    # Recalcular cobertura antes de salvar
    state = data.artifact_state
    coverage_snapshot = _calculate_coverage_snapshot(state)
    state.metadata.total_coverage = coverage_snapshot["total_coverage"]

    # Atualizar objeto Artifact
    artifact.version += 1
    artifact.artifact_state = state.model_dump()
    artifact.coverage_data = {
        "total": state.metadata.total_coverage,
        "band": _coverage_band(state.metadata.total_coverage),
    }  # Snapshot rápido para dashboard

    if data.status:
        artifact.status = data.status

    scope.db.add(artifact)

    # Criar nova entrada de histórico
    version = ArtifactVersion(
        artifact_id=artifact.id,
        tenant_id=scope.tenant_id,
        version=artifact.version,
        state_snapshot=artifact.artifact_state,
        change_reason=data.change_reason or f"Atualização versão {artifact.version}",
        changed_by=data.changed_by,
    )
    scope.db.add(version)

    await scope.db.flush()
    return artifact


async def get_artifact_versions(scope: TenantScope, artifact_id: str) -> Sequence[ArtifactVersion]:
    """Lista o histórico de versões de um artefato."""
    await get_artifact(scope, artifact_id)

    stmt = (
        select(ArtifactVersion)
        .where(ArtifactVersion.artifact_id == artifact_id)
        .where(ArtifactVersion.tenant_id == scope.tenant_id)
        .order_by(desc(ArtifactVersion.version))
    )
    result = await scope.db.scalars(stmt)
    return result.all()


async def get_project_artifacts(scope: TenantScope, project_id: str) -> Sequence[Artifact]:
    """Lista todos os artefatos de um projeto."""
    stmt = (
        select(Artifact)
        .where(Artifact.project_id == project_id)
        .where(Artifact.tenant_id == scope.tenant_id)
        .order_by(desc(Artifact.created_at))
    )
    result = await scope.db.scalars(stmt)
    return result.all()


async def get_artifact_markdown(
    scope: TenantScope,
    artifact_id: str,
    view: str = "business",
    show_business_ids: bool = False,
) -> str:
    """Recupera o artefato e renderiza como Markdown."""
    artifact = await get_artifact(scope, artifact_id)
    state = ArtifactState.model_validate(artifact.artifact_state)
    return render_artifact_to_markdown(
        artifact.title,
        state,
        view=view,
        show_business_ids=show_business_ids,
    )


async def get_artifact_export(
    scope: TenantScope,
    artifact_id: str,
    export_format: str = "markdown",
    view: str = "business",
    show_business_ids: bool = False,
) -> tuple[str, str]:
    """Prepara o conteúdo e o nome do arquivo para exportação."""
    artifact = await get_artifact(scope, artifact_id)
    project = await scope.db.scalar(scope.where_id(Project, artifact.project_id))

    clean_title = _slugify_filename_part(artifact.title)
    timestamp = artifact.updated_at.strftime("%Y%m%d")
    total_coverage = float(artifact.artifact_state.get("metadata", {}).get("total_coverage", 0.0))

    if export_format == "json":
        content = json.dumps(artifact.artifact_state, indent=2, ensure_ascii=False)
        filename = f"reqstudio_{clean_title}_{timestamp}_v{artifact.version}.json"
        return content, filename

    # Default: Markdown
    md_content = await get_artifact_markdown(
        scope,
        artifact_id,
        view=view,
        show_business_ids=show_business_ids,
    )

    # Adicionar Header de Exportação
    header = (
        f"---\n"
        f"Project: {project.name if project else artifact.project_id}\n"
        f"Artifact: {artifact.title}\n"
        f"Version: {artifact.version}\n"
        f"Coverage: {total_coverage * 100:.0f}%\n"
        f"View: {view.capitalize()}\n"
        f"Export Date: {timestamp}\n"
        f"---\n\n"
    )

    filename = f"reqstudio_{clean_title}_{timestamp}_v{artifact.version}.md"
    return header + md_content, filename


async def get_artifact_coverage(scope: TenantScope, artifact_id: str) -> dict:
    """Retorna dados resumidos de cobertura para widgets e indicadores."""
    artifact = await get_artifact(scope, artifact_id)
    state = ArtifactState.model_validate(artifact.artifact_state)
    snapshot = _calculate_coverage_snapshot(state)

    return {
        "artifact_id": artifact.id,
        "total_coverage": snapshot["total_coverage"],
        "sections": snapshot["sections"],
    }
