"""LLM Client — abstração multi-provider com LiteLLM (Story 5.3).

Provides:
  - stream_completion(): async generator de chunks de texto
  - complete(): chamada síncrona (não-streaming) para uso interno
  - Cost tracking via métricas de tokens

LiteLLM normaliza a API entre providers:
  - "anthropic/claude-sonnet-4-20250514" → Anthropic API
  - "openai/gpt-4o" → OpenAI API
  - "ollama/llama3" → Ollama local

Configuração via settings:
  - LLM_MODEL: modelo principal
  - LLM_FALLBACK_MODEL: fallback automático
  - LLM_TIMEOUT: timeout em segundos
  - LLM_API_KEY: chave da API do provider
"""

import logging
import os
import time
from dataclasses import dataclass, field
from typing import AsyncGenerator

import litellm

from app.core.config import settings
from app.core.exceptions import ErrorCode, GuidedRecoveryError, Severity

logger = logging.getLogger(__name__)


@dataclass
class CompletionMetrics:
    """Métricas de uma chamada ao LLM para cost tracking.

    Popula OpenTelemetry spans para rastreabilidade.
    """
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    success: bool = True
    error: str | None = None


@dataclass
class CompletionChunk:
    """Chunk individual de uma resposta streaming."""
    content: str = ""
    done: bool = False
    metrics: CompletionMetrics | None = None


def _llm_unavailable_error(detail: str = "") -> GuidedRecoveryError:
    """Erro quando todos os providers LLM falharam."""
    return GuidedRecoveryError(
        code=ErrorCode.LLM_UNAVAILABLE,
        message="A IA está temporariamente indisponível.",
        help=f"Todos os provedores de IA estão fora do ar. Sua sessão está segura. Tente novamente em alguns minutos.{' (' + detail + ')' if detail else ''}",
        actions=[{"label": "Tentar novamente", "action": "retry"}],
        severity=Severity.RECOVERABLE,
        status_code=503,
    )


def _llm_timeout_error() -> GuidedRecoveryError:
    """Erro quando o LLM excedeu o timeout."""
    return GuidedRecoveryError(
        code=ErrorCode.LLM_UNAVAILABLE,
        message="A resposta da IA demorou demais.",
        help=f"O tempo limite de {settings.LLM_TIMEOUT}s foi excedido. Tente novamente — às vezes a IA precisa de mais tempo para respostas complexas.",
        actions=[{"label": "Tentar novamente", "action": "retry"}],
        severity=Severity.RECOVERABLE,
        status_code=504,
    )


def _get_model_list() -> list[str]:
    """Monta lista de modelos: principal + fallback."""
    models = [settings.LLM_MODEL]
    if settings.LLM_FALLBACK_MODEL:
        models.append(settings.LLM_FALLBACK_MODEL)
    return models


def _setup_api_key() -> None:
    """Configura a API key no ambiente para LiteLLM."""
    if settings.LLM_API_KEY:
        # LiteLLM detecta automaticamente baseado no provider
        # mas também aceita via variáveis de ambiente específicas
        model = settings.LLM_MODEL.lower()
        if "anthropic" in model:
            os.environ.setdefault("ANTHROPIC_API_KEY", settings.LLM_API_KEY)
        elif "openai" in model:
            os.environ.setdefault("OPENAI_API_KEY", settings.LLM_API_KEY)
        else:
            # Genérico — litellm usa API_KEY
            os.environ.setdefault("API_KEY", settings.LLM_API_KEY)


async def stream_completion(
    messages: list[dict[str, str]],
    model: str | None = None,
    timeout: int | None = None,
) -> AsyncGenerator[CompletionChunk, None]:
    """Streaming de resposta do LLM via LiteLLM.

    Args:
        messages:  Lista de mensagens no formato [{"role": ..., "content": ...}]
        model:     Override do modelo (default: settings.LLM_MODEL)
        timeout:   Override do timeout (default: settings.LLM_TIMEOUT)

    Yields:
        CompletionChunk com conteúdo parcial. Último chunk tem done=True e metrics.

    Raises:
        GuidedRecoveryError(LLM_UNAVAILABLE): se todos os providers falharam
        GuidedRecoveryError(LLM_UNAVAILABLE): se timeout excedido
    """
    _setup_api_key()

    target_model = model or settings.LLM_MODEL
    target_timeout = timeout or settings.LLM_TIMEOUT
    start_time = time.monotonic()

    metrics = CompletionMetrics(model=target_model)
    full_content = ""

    try:
        response = await litellm.acompletion(
            model=target_model,
            messages=messages,
            stream=True,
            timeout=target_timeout,
            fallbacks=_get_model_list()[1:] if len(_get_model_list()) > 1 else None,
        )

        async for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                full_content += delta.content
                yield CompletionChunk(content=delta.content, done=False)

            # Extrair métricas de usage se disponíveis
            if hasattr(chunk, "usage") and chunk.usage:
                metrics.input_tokens = getattr(chunk.usage, "prompt_tokens", 0) or 0
                metrics.output_tokens = getattr(chunk.usage, "completion_tokens", 0) or 0
                metrics.total_tokens = metrics.input_tokens + metrics.output_tokens

        # Chunk final com métricas
        metrics.latency_ms = (time.monotonic() - start_time) * 1000
        metrics.success = True

        # Tentar calcular custo via litellm
        try:
            cost = litellm.completion_cost(
                model=target_model,
                prompt=str(messages),
                completion=full_content,
            )
            metrics.cost_usd = cost or 0.0
        except Exception:
            metrics.cost_usd = 0.0

        logger.info(
            "LLM completion finished",
            extra={
                "model": metrics.model,
                "input_tokens": metrics.input_tokens,
                "output_tokens": metrics.output_tokens,
                "cost_usd": metrics.cost_usd,
                "latency_ms": round(metrics.latency_ms, 2),
            },
        )

        yield CompletionChunk(content="", done=True, metrics=metrics)

    except litellm.Timeout:
        metrics.latency_ms = (time.monotonic() - start_time) * 1000
        metrics.success = False
        metrics.error = "timeout"
        logger.error("LLM timeout", extra={"model": target_model, "timeout": target_timeout})
        raise _llm_timeout_error()

    except (litellm.APIConnectionError, litellm.APIError, litellm.ServiceUnavailableError) as e:
        metrics.latency_ms = (time.monotonic() - start_time) * 1000
        metrics.success = False
        metrics.error = str(e)
        logger.error("LLM unavailable", extra={"model": target_model, "error": str(e)})
        raise _llm_unavailable_error(str(e))

    except Exception as e:
        metrics.latency_ms = (time.monotonic() - start_time) * 1000
        metrics.success = False
        metrics.error = str(e)
        logger.error("LLM unexpected error", extra={"model": target_model, "error": str(e)})
        raise _llm_unavailable_error(str(e))


async def complete(
    messages: list[dict[str, str]],
    model: str | None = None,
    timeout: int | None = None,
) -> tuple[str, CompletionMetrics]:
    """Chamada não-streaming ao LLM. Retorna (content, metrics).

    Útil para chamadas internas (ex: gerar título de sessão).
    """
    full_content = ""
    final_metrics = CompletionMetrics()

    async for chunk in stream_completion(messages, model=model, timeout=timeout):
        full_content += chunk.content
        if chunk.done and chunk.metrics:
            final_metrics = chunk.metrics

    return full_content, final_metrics
