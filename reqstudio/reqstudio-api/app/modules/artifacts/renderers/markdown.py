"""Markdown renderer for Artifacts — Story 6.2.

Transforms Canonical JSON state into human-readable Markdown.
Supports 'business' and 'technical' views.
"""

import re

from app.modules.artifacts.schemas import ArtifactSection, ArtifactState

_GHERKIN_EN_RE = re.compile(r"\b(given|when|then)\b", flags=re.IGNORECASE)
_GHERKIN_PT_RE = re.compile(r"\b(dado|quando|ent[aã]o)\b", flags=re.IGNORECASE)


def _contains_gherkin(content: str) -> bool:
    """Detecta presença de passos Gherkin em inglês ou português."""
    return len(_GHERKIN_EN_RE.findall(content)) >= 3 or len(_GHERKIN_PT_RE.findall(content)) >= 3


def render_section_to_markdown(
    section: ArtifactSection,
    view: str,
    show_business_ids: bool = False,
) -> str:
    """Renderiza uma seção individual baseada na visualização solicitada."""

    header_level = "##"
    title = section.title
    content = section.content.strip()
    if not content:
        content = "_Sem conteúdo detalhado._"

    # Badge de cobertura baixa
    status_badge = ""
    if section.coverage < 0.3:
        status_badge = " > [!WARNING]\n> ⚠️ Pendente de aprofundamento\n\n"

    # Na visão técnica, podemos adicionar metadados extras ou formatação Gherkin
    if view == "technical":
        # Se detectarmos passos Gherkin, garantimos bloco de código quando necessário.
        if _contains_gherkin(content) and "```" not in content:
            content = f"```gherkin\n{content}\n```"

        # Adiciona ID técnico no cabeçalho para desenvolvedores
        title = f"{title} (`{section.id}`)"
    elif show_business_ids:
        title = f"{title} (`{section.id}`)"

    return f"{header_level} {title}\n\n{status_badge}{content}\n\n"


def render_artifact_to_markdown(
    title: str,
    state: ArtifactState,
    view: str = "business",
    show_business_ids: bool = False,
) -> str:
    """Transforma o estado completo do artefato em um documento Markdown."""

    lines = []

    # Cabeçalho Principal
    view_label = "Visão de Negócio" if view == "business" else "Especificação Técnica"
    coverage_pct = state.metadata.total_coverage * 100
    lines.append(f"# {title}")
    lines.append(f"> **Status**: {view_label} | **Cobertura Global**: {coverage_pct:.0f}%")
    lines.append("\n---\n")

    if not state.sections:
        lines.append("_Este artefato ainda não possui seções definidas._")
    else:
        for section in state.sections:
            lines.append(
                render_section_to_markdown(
                    section,
                    view=view,
                    show_business_ids=show_business_ids,
                )
            )

    # Rodapé de Versão
    lines.append("\n---\n")
    lines.append(f"_Gerado automaticamente pelo ReqStudio — {view_label}_")

    return "\n".join(lines)
