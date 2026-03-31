"""Testes do LLM Client — Story 5.3.

Cobre: streaming, timeout, unavailable, cost tracking, complete().
Todos os testes usam mock do litellm — sem chamadas reais.

Read-Before-Write: test_context_builder.py (Lição 11).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass

from app.integrations.llm_client import (
    stream_completion,
    complete,
    CompletionChunk,
    CompletionMetrics,
    _get_model_list,
)
from app.core.exceptions import GuidedRecoveryError


# ── Helpers ───────────────────────────────────────────────────────────────────

# Classes de exceção distintas para que os except clauses não colidam
class _MockTimeout(Exception):
    pass

class _MockAPIConnectionError(Exception):
    pass

class _MockAPIError(Exception):
    pass

class _MockServiceUnavailableError(Exception):
    pass


def _setup_mock_litellm(mock_litellm):
    """Configura exceções distintas no mock do litellm."""
    mock_litellm.Timeout = _MockTimeout
    mock_litellm.APIConnectionError = _MockAPIConnectionError
    mock_litellm.APIError = _MockAPIError
    mock_litellm.ServiceUnavailableError = _MockServiceUnavailableError


@dataclass
class MockDelta:
    content: str | None = None


@dataclass
class MockChoice:
    delta: MockDelta | None = None


@dataclass
class MockUsage:
    prompt_tokens: int = 10
    completion_tokens: int = 20


@dataclass
class MockStreamChunk:
    choices: list[MockChoice] | None = None
    usage: MockUsage | None = None


async def _mock_stream_response(chunks: list[str]):
    """Async generator que simula resposta streaming do LiteLLM."""
    for i, text in enumerate(chunks):
        is_last = i == len(chunks) - 1
        yield MockStreamChunk(
            choices=[MockChoice(delta=MockDelta(content=text))],
            usage=MockUsage(prompt_tokens=10, completion_tokens=20) if is_last else None,
        )


SAMPLE_MESSAGES = [
    {"role": "system", "content": "Você é um assistente."},
    {"role": "user", "content": "Olá!"},
]


# ── Streaming Tests ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stream_completion_yields_chunks():
    """Streaming retorna chunks parciais e chunk final com done=True."""
    mock_response = _mock_stream_response(["Olá", ", ", "como", " vai?"])

    with patch("app.integrations.llm_client.litellm") as mock_litellm:
        _setup_mock_litellm(mock_litellm)
        mock_litellm.acompletion = AsyncMock(return_value=mock_response)
        mock_litellm.completion_cost = MagicMock(return_value=0.001)

        chunks = []
        async for chunk in stream_completion(SAMPLE_MESSAGES):
            chunks.append(chunk)

        content_chunks = [c for c in chunks if not c.done]
        done_chunks = [c for c in chunks if c.done]

        assert len(content_chunks) == 4
        assert len(done_chunks) == 1
        assert content_chunks[0].content == "Olá"
        assert done_chunks[0].metrics is not None


@pytest.mark.asyncio
async def test_stream_completion_assembles_full_content():
    """O conteúdo acumulado dos chunks forma a resposta completa."""
    mock_response = _mock_stream_response(["Parte 1", " — ", "Parte 2"])

    with patch("app.integrations.llm_client.litellm") as mock_litellm:
        _setup_mock_litellm(mock_litellm)
        mock_litellm.acompletion = AsyncMock(return_value=mock_response)
        mock_litellm.completion_cost = MagicMock(return_value=0.0)

        full = ""
        async for chunk in stream_completion(SAMPLE_MESSAGES):
            full += chunk.content

        assert full == "Parte 1 — Parte 2"


@pytest.mark.asyncio
async def test_stream_completion_metrics():
    """Chunk final contém métricas de latência e tokens."""
    mock_response = _mock_stream_response(["response"])

    with patch("app.integrations.llm_client.litellm") as mock_litellm:
        _setup_mock_litellm(mock_litellm)
        mock_litellm.acompletion = AsyncMock(return_value=mock_response)
        mock_litellm.completion_cost = MagicMock(return_value=0.005)

        final_metrics = None
        async for chunk in stream_completion(SAMPLE_MESSAGES):
            if chunk.done:
                final_metrics = chunk.metrics

        assert final_metrics is not None
        assert final_metrics.success is True
        assert final_metrics.latency_ms > 0
        assert final_metrics.cost_usd == 0.005


# ── Timeout Tests ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stream_completion_timeout_raises_guided_error():
    """Timeout do LLM levanta GuidedRecoveryError com status 504."""
    with patch("app.integrations.llm_client.litellm") as mock_litellm:
        _setup_mock_litellm(mock_litellm)
        mock_litellm.acompletion = AsyncMock(side_effect=_MockTimeout("timeout"))

        with pytest.raises(GuidedRecoveryError) as exc_info:
            async for _ in stream_completion(SAMPLE_MESSAGES):
                pass

        assert exc_info.value.status_code == 504
        assert exc_info.value.code == "LLM_UNAVAILABLE"


# ── Unavailable Tests ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stream_completion_api_error_raises_guided_error():
    """Erro de API do LLM levanta GuidedRecoveryError com status 503."""
    with patch("app.integrations.llm_client.litellm") as mock_litellm:
        _setup_mock_litellm(mock_litellm)
        mock_litellm.acompletion = AsyncMock(side_effect=_MockAPIError("service down"))

        with pytest.raises(GuidedRecoveryError) as exc_info:
            async for _ in stream_completion(SAMPLE_MESSAGES):
                pass

        assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_stream_completion_connection_error_raises_guided_error():
    """Erro de conexão levanta GuidedRecoveryError com status 503."""
    with patch("app.integrations.llm_client.litellm") as mock_litellm:
        _setup_mock_litellm(mock_litellm)
        mock_litellm.acompletion = AsyncMock(side_effect=_MockAPIConnectionError("no connection"))

        with pytest.raises(GuidedRecoveryError) as exc_info:
            async for _ in stream_completion(SAMPLE_MESSAGES):
                pass

        assert exc_info.value.status_code == 503


# ── Complete (non-streaming) ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_complete_returns_full_content_and_metrics():
    """complete() acumula chunks e retorna (content, metrics)."""
    mock_response = _mock_stream_response(["Hello", " world"])

    with patch("app.integrations.llm_client.litellm") as mock_litellm:
        _setup_mock_litellm(mock_litellm)
        mock_litellm.acompletion = AsyncMock(return_value=mock_response)
        mock_litellm.completion_cost = MagicMock(return_value=0.002)

        content, metrics = await complete(SAMPLE_MESSAGES)

        assert content == "Hello world"
        assert metrics.success is True
        assert metrics.cost_usd == 0.002


# ── Configuration ────────────────────────────────────────────────────────────


def test_get_model_list_without_fallback():
    """Sem fallback, retorna apenas o modelo principal."""
    with patch("app.integrations.llm_client.settings") as mock_settings:
        mock_settings.LLM_MODEL = "anthropic/claude-sonnet-4-20250514"
        mock_settings.LLM_FALLBACK_MODEL = None
        models = _get_model_list()
        assert models == ["anthropic/claude-sonnet-4-20250514"]


def test_get_model_list_with_fallback():
    """Com fallback, retorna principal + fallback."""
    with patch("app.integrations.llm_client.settings") as mock_settings:
        mock_settings.LLM_MODEL = "anthropic/claude-sonnet-4-20250514"
        mock_settings.LLM_FALLBACK_MODEL = "openai/gpt-4o-mini"
        models = _get_model_list()
        assert models == ["anthropic/claude-sonnet-4-20250514", "openai/gpt-4o-mini"]
