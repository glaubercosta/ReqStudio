"""Token counting utilities for Context Builder (Story 5.2).

MVP: estimativa baseada em caracteres (4 chars ≈ 1 token).
Suficientemente preciso para português/inglês sem adicionar dependência de tiktoken.
V2: substituir por tiktoken para contagem exata por modelo.
"""


def estimate_tokens(text: str) -> int:
    """Estima número de tokens em um texto.

    Usa a heurística de ~4 caracteres por token,
    que é razoável para conteúdo misto pt-BR/en.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


def estimate_messages_tokens(messages: list[dict[str, str]]) -> int:
    """Estima tokens totais de uma lista de mensagens no formato LLM.

    Cada mensagem tem overhead de ~4 tokens (role markers, delimiters).
    """
    total = 0
    for msg in messages:
        total += 4  # overhead por mensagem (role, delimiters)
        total += estimate_tokens(msg.get("content", ""))
    total += 2  # overhead de início/fim da conversa
    return total
