"""Testes do engine de elicitação — Story 5.5-2.

Cobre:
  - _compute_progress_summary: lógica de mapeamento step → checklist
  - _update_progress_summary: comportamento de isolamento e atualização

Testes unitários puros (sem DB).
"""

import pytest

from app.modules.engine.elicitation import _compute_progress_summary


# ── Testes de _compute_progress_summary ──────────────────────────────────────


def test_compute_progress_summary_step_0():
    """Step 0 ou None → todos os itens false."""
    result = _compute_progress_summary(None)
    assert result["context"] is False
    assert result["stakeholders"] is False
    assert result["goals"] is False
    assert result["flows"] is False
    assert result["nfr"] is False
    assert result["review"] is False


def test_compute_progress_summary_step_1():
    """Step 1 → apenas context true (AC 4: step >= 1)."""
    result = _compute_progress_summary({"current_step": 1})
    assert result["context"] is True
    assert result["stakeholders"] is False
    assert result["goals"] is False


def test_compute_progress_summary_step_2():
    """Step 2 → context e stakeholders true."""
    result = _compute_progress_summary({"current_step": 2})
    assert result["context"] is True
    assert result["stakeholders"] is True
    assert result["goals"] is False


def test_compute_progress_summary_step_3():
    """Step 3 → context, stakeholders e goals true."""
    result = _compute_progress_summary({"current_step": 3})
    assert result["goals"] is True
    assert result["flows"] is False


def test_compute_progress_summary_step_4():
    """Step 4 → flows true."""
    result = _compute_progress_summary({"current_step": 4})
    assert result["flows"] is True
    assert result["nfr"] is False


def test_compute_progress_summary_step_5():
    """Step 5 → nfr true (todos exceto review)."""
    result = _compute_progress_summary({"current_step": 5})
    assert result["nfr"] is True
    assert result["review"] is False  # review sempre False (manual)


def test_compute_progress_summary_review_always_false():
    """review nunca é true automaticamente."""
    for step in range(6):
        result = _compute_progress_summary({"current_step": step})
        assert result["review"] is False, f"review deveria ser False para step={step}"


def test_compute_progress_summary_empty_position():
    """workflow_position vazio → trata como step 0."""
    result = _compute_progress_summary({})
    assert result["context"] is False


def test_compute_progress_summary_returns_all_keys():
    """Resultado deve ter exatamente as 6 chaves do checklist."""
    result = _compute_progress_summary({"current_step": 3})
    expected_keys = {"context", "stakeholders", "goals", "flows", "nfr", "review"}
    assert set(result.keys()) == expected_keys


# ── Testes de _update_progress_summary ──────────────────────────────────────


@pytest.mark.asyncio
async def test_update_progress_summary_calls_db():
    """Verifica que o update faz a query via scope e atualiza o objeto."""
    from unittest.mock import AsyncMock, MagicMock
    from app.modules.engine.elicitation import _update_progress_summary

    # Mocks
    mock_db = AsyncMock()
    mock_scope = MagicMock()
    mock_scope.db = mock_db
    mock_scope.where_id.return_value = "where_stmt"  # fake stmt
    
    mock_project = MagicMock()
    mock_project.id = "proj-123"
    mock_db.scalar.return_value = mock_project
    
    mock_session = MagicMock()
    mock_session.project_id = "proj-123"
    mock_session.workflow_position = {"current_step": 2}
    
    # Executa
    await _update_progress_summary(mock_scope, mock_session)
    
    # Verifica
    mock_scope.where_id.assert_called()
    mock_db.scalar.assert_awaited()
    # No step 2, stakeholders e context devem ser True
    assert mock_project.progress_summary["context"] is True
    assert mock_project.progress_summary["stakeholders"] is True
    assert mock_project.progress_summary["goals"] is False
