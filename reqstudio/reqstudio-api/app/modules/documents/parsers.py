"""Document parsers — PDF e Markdown (Story 4.1).

Design:
  - Cada parser recebe bytes e retorna lista de strings (chunks de ~1000 chars)
  - Chunk size é conservador: contexto LLM médio suporta ~4k tokens ≈ ~16k chars
  - PDF: usa PyMuPDF (fitz) — rápido, sem dependência de poppler
  - Markdown: usa regex simples de separação por heading / parágrafo
"""

from __future__ import annotations

import re

CHUNK_SIZE = 1500  # caracteres por chunk
CHUNK_OVERLAP = 100  # sobreposição entre chunks para preservar contexto


def _split_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Divide texto em chunks de tamanho fixo com sobreposição."""
    text = text.strip()
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def parse_markdown(content: bytes) -> list[str]:
    """Extrai chunks de um arquivo Markdown.

    Estratégia: separa por headings (##) e parágrafos, depois divide por tamanho.
    """
    text = content.decode("utf-8", errors="replace")
    # Remove frontmatter YAML (--- ... ---)
    text = re.sub(r"^---.*?---\n", "", text, flags=re.DOTALL)
    # Divide por seções (## heading)
    sections = re.split(r"\n(?=#+\s)", text)
    chunks: list[str] = []
    for section in sections:
        chunks.extend(_split_text(section))
    return [c for c in chunks if len(c.strip()) > 10]


def parse_pdf(content: bytes) -> list[str]:
    """Extrai chunks de texto de um PDF usando PyMuPDF (fitz).

    Fallback gracioso: se fitz não estiver instalado, lança ImportError descritivo.
    """
    try:
        import fitz  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ImportError(
            "PyMuPDF (fitz) é necessário para parsing de PDF. Instale com: pip install pymupdf"
        ) from exc

    text_parts: list[str] = []
    with fitz.open(stream=content, filetype="pdf") as doc:
        for page in doc:
            page_text = page.get_text("text")
            if page_text.strip():
                text_parts.append(page_text)

    full_text = "\n\n".join(text_parts)
    return _split_text(full_text)
