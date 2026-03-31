"""Testes do SSE Endpoint — Story 5.5.

Cobre: streaming SSE, formato de events, erro, content-type.
LLM é mocked. HTTP via AsyncClient + StreamingResponse.
"""

import json

import pytest
from unittest.mock import patch
from httpx import AsyncClient

from app.integrations.llm_client import CompletionChunk, CompletionMetrics


# ── Helpers ───────────────────────────────────────────────────────────────────

def _auth(token: dict) -> dict:
    return {"Authorization": f"Bearer {token['access_token']}"}


async def _create_project(client: AsyncClient, token: dict) -> dict:
    payload = {"name": "Projeto SSE", "business_domain": "Saúde"}
    res = await client.post("/api/v1/projects", json=payload, headers=_auth(token))
    assert res.status_code == 201, res.text
    return res.json()["data"]


async def _create_session(client: AsyncClient, token: dict, project_id: str) -> dict:
    res = await client.post(
        f"/api/v1/projects/{project_id}/sessions",
        json={},
        headers=_auth(token),
    )
    assert res.status_code == 201, res.text
    return res.json()["data"]


async def _mock_llm_stream(*args, **kwargs):
    """Simula streaming."""
    yield CompletionChunk(content="Olá ", done=False)
    yield CompletionChunk(content="mundo!", done=False)
    yield CompletionChunk(
        content="", done=True,
        metrics=CompletionMetrics(
            model="mock", input_tokens=10, output_tokens=5,
            total_tokens=15, cost_usd=0.001, latency_ms=100, success=True,
        ),
    )


def _parse_sse_events(raw: str) -> list[dict]:
    """Parseia texto SSE em lista de {event, data}."""
    events = []
    for block in raw.strip().split("\n\n"):
        event_type = "message"
        data = ""
        for line in block.strip().split("\n"):
            if line.startswith("event: "):
                event_type = line[7:]
            elif line.startswith("data: "):
                data = line[6:]
        if data:
            events.append({"event": event_type, "data": json.loads(data)})
    return events


# ── SSE Streaming Tests ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_elicit_sse_returns_event_stream(client: AsyncClient, tenant_a_token, seed_workflows):
    """POST /sessions/{id}/elicit retorna content-type text/event-stream."""
    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])

    with patch("app.modules.sessions.router.elicit", side_effect=_mock_llm_stream):
        res = await client.post(
            f"/api/v1/sessions/{session['id']}/elicit",
            json={"content": "Olá IA!"},
            headers=_auth(tenant_a_token),
        )

    assert res.status_code == 200
    assert "text/event-stream" in res.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_elicit_sse_event_format(client: AsyncClient, tenant_a_token, seed_workflows):
    """SSE events seguem formato: event: message/done, data: JSON."""
    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])

    with patch("app.modules.sessions.router.elicit", side_effect=_mock_llm_stream):
        res = await client.post(
            f"/api/v1/sessions/{session['id']}/elicit",
            json={"content": "Teste formato"},
            headers=_auth(tenant_a_token),
        )

    events = _parse_sse_events(res.text)

    # 2 message events + 1 done event
    message_events = [e for e in events if e["event"] == "message"]
    done_events = [e for e in events if e["event"] == "done"]

    assert len(message_events) == 2
    assert len(done_events) == 1

    # Conteúdo dos chunks
    assert message_events[0]["data"]["content"] == "Olá "
    assert message_events[0]["data"]["done"] is False
    assert message_events[1]["data"]["content"] == "mundo!"

    # Done event com métricas
    assert done_events[0]["data"]["done"] is True
    assert done_events[0]["data"]["metrics"]["cost_usd"] == 0.001


@pytest.mark.asyncio
async def test_elicit_sse_error_event(client: AsyncClient, tenant_a_token, seed_workflows):
    """Erro no pipeline gera event: error."""
    project = await _create_project(client, tenant_a_token)
    session = await _create_session(client, tenant_a_token, project["id"])

    from app.core.exceptions import GuidedRecoveryError, ErrorCode, Severity

    async def _mock_error(*args, **kwargs):
        raise GuidedRecoveryError(
            code=ErrorCode.LLM_UNAVAILABLE,
            message="IA offline",
            help="Tente novamente",
            actions=[],
            severity=Severity.RECOVERABLE,
            status_code=503,
        )
        # yield necessário para que Python trate como async generator
        yield  # pragma: no cover

    with patch("app.modules.sessions.router.elicit", side_effect=_mock_error):
        res = await client.post(
            f"/api/v1/sessions/{session['id']}/elicit",
            json={"content": "Teste erro"},
            headers=_auth(tenant_a_token),
        )

    events = _parse_sse_events(res.text)
    error_events = [e for e in events if e["event"] == "error"]
    assert len(error_events) == 1
    assert error_events[0]["data"]["code"] == "LLM_UNAVAILABLE"


@pytest.mark.asyncio
async def test_elicit_sse_cross_tenant_returns_error(
    client: AsyncClient, tenant_a_token, tenant_b_token, seed_workflows,
):
    """Sessão de outro tenant → event: error no SSE."""
    project_a = await _create_project(client, tenant_a_token)
    session_a = await _create_session(client, tenant_a_token, project_a["id"])

    # Tenant B tenta elicitar na sessão de A
    res = await client.post(
        f"/api/v1/sessions/{session_a['id']}/elicit",
        json={"content": "Intruso!"},
        headers=_auth(tenant_b_token),
    )

    # SSE sempre retorna 200 — o erro vem no stream
    events = _parse_sse_events(res.text)
    error_events = [e for e in events if e["event"] == "error"]
    assert len(error_events) >= 1
