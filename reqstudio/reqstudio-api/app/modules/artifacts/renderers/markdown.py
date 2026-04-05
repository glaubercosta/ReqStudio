"""Markdown renderer for Artifacts — Story 6.2.

Transforms Canonical JSON state into human-readable Markdown.
Supports 'business' and 'technical' views.
"""

from app.modules.artifacts.schemas import ArtifactState, ArtifactSection

def render_section_to_markdown(section: ArtifactSection, view: str) -> str:
    """Renderiza uma seção individual baseada na visualização solicitada."""
    
    header_level = "##"
    title = section.title
    content = section.content.strip()
    
    # Badge de cobertura baixa
    status_badge = ""
    if section.coverage < 0.3:
        status_badge = " > [!WARNING]\n> ⚠️ **Conteúdo Pendente**: Esta seção ainda não foi explorada suficientemente.\n\n"

    # Na visão técnica, podemos adicionar metadados extras ou formatação Gherkin
    if view == "technical":
        # Se detectarmos 'Given/When/Then', garantimos que esteja em um bloco de código se não estiver
        if "Given" in content and "When" in content and "Then" in content:
            if "```" not in content:
                content = f"```gherkin\n{content}\n```"
        
        # Adiciona ID técnico no cabeçalho para desenvolvedores
        title = f"{title} (`{section.id}`)"

    return f"{header_level} {title}\n\n{status_badge}{content}\n\n"


def render_artifact_to_markdown(title: str, state: ArtifactState, view: str = "business") -> str:
    """Transforma o estado completo do artefato em um documento Markdown."""
    
    lines = []
    
    # Cabeçalho Principal
    view_label = "Visão de Negócio" if view == "business" else "Especificação Técnica"
    lines.append(f"# {title}")
    lines.append(
        f"> **Status**: {view_label} | **Cobertura Global**: {state.metadata.total_coverage*100:.0f}%"
    )
    lines.append("\n---\n")

    if not state.sections:
        lines.append("_Este artefato ainda não possui seções definidas._")
    else:
        for section in state.sections:
            lines.append(render_section_to_markdown(section, view))

    # Rodapé de Versão
    lines.append("\n---\n")
    lines.append(f"_Gerado automaticamente pelo ReqStudio — {view_label}_")

    return "\n".join(lines)
