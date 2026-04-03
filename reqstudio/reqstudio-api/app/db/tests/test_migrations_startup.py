"""Unit tests for app.db.migrations.run_migrations_on_startup.

These tests are purely unit-level — they mock ``alembic.command.upgrade``
and ``sys.exit`` so no real database is needed.
"""

import importlib
import sys
from unittest.mock import MagicMock, call, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reload_module():
    """Force-reload migrations module to clear any cached settings state."""
    import app.db.migrations as mod
    importlib.reload(mod)
    return mod


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRunMigrationsOnStartup:
    """Tests for run_migrations_on_startup()."""

    def test_skips_migrations_in_test_environment(self, monkeypatch):
        """When TESTING=True, alembic upgrade must NOT be called."""
        monkeypatch.setenv("TESTING", "true")
        mod = _reload_module()
        monkeypatch.setattr(mod.settings, "TESTING", True)

        with patch.object(mod.command, "upgrade") as mock_upgrade:
            mod.run_migrations_on_startup()

        mock_upgrade.assert_not_called()

    def test_calls_upgrade_head_when_not_testing(self, monkeypatch):
        """When TESTING=False, alembic upgrade must be called with 'head'."""
        mod = _reload_module()
        monkeypatch.setattr(mod.settings, "TESTING", False)

        with patch.object(mod.command, "upgrade") as mock_upgrade, \
             patch.object(mod, "_get_alembic_config", return_value=MagicMock()):
            mod.run_migrations_on_startup()

        mock_upgrade.assert_called_once()
        _, revision = mock_upgrade.call_args[0]
        assert revision == "head", f"Expected 'head', got {revision!r}"

    def test_exits_with_code_1_on_migration_failure(self, monkeypatch):
        """When upgrade raises, sys.exit(1) must be called."""
        mod = _reload_module()
        monkeypatch.setattr(mod.settings, "TESTING", False)

        with patch.object(mod, "_get_alembic_config", return_value=MagicMock()), \
             patch.object(mod.command, "upgrade", side_effect=Exception("DB down")), \
             patch.object(mod.sys, "exit") as mock_exit:
            mod.run_migrations_on_startup()

        mock_exit.assert_called_once_with(1)

    def test_no_exit_on_success(self, monkeypatch):
        """When upgrade succeeds, sys.exit must NOT be called."""
        mod = _reload_module()
        monkeypatch.setattr(mod.settings, "TESTING", False)

        with patch.object(mod, "_get_alembic_config", return_value=MagicMock()), \
             patch.object(mod.command, "upgrade"), \
             patch.object(mod.sys, "exit") as mock_exit:
            mod.run_migrations_on_startup()

        mock_exit.assert_not_called()

    def test_alembic_config_uses_head_revision(self, monkeypatch):
        """Verify the exact revision string passed to upgrade is 'head'."""
        mod = _reload_module()
        monkeypatch.setattr(mod.settings, "TESTING", False)

        captured = {}

        def fake_upgrade(cfg, revision):
            captured["revision"] = revision

        with patch.object(mod, "_get_alembic_config", return_value=MagicMock()), \
             patch.object(mod.command, "upgrade", side_effect=fake_upgrade):
            mod.run_migrations_on_startup()

        assert captured.get("revision") == "head"

    def test_skip_logs_info_message(self, monkeypatch, caplog):
        """Skipped migrations should produce a recognisable INFO log."""
        import logging

        mod = _reload_module()
        monkeypatch.setattr(mod.settings, "TESTING", True)

        with patch.object(mod.command, "upgrade"):
            with caplog.at_level(logging.INFO, logger="app.db.migrations"):
                mod.run_migrations_on_startup()

        assert any("test environment" in record.message.lower() for record in caplog.records)

    def test_failure_logs_critical_message(self, monkeypatch, caplog):
        """Migration failure should produce a CRITICAL log."""
        import logging

        mod = _reload_module()
        monkeypatch.setattr(mod.settings, "TESTING", False)

        with patch.object(mod, "_get_alembic_config", return_value=MagicMock()), \
             patch.object(mod.command, "upgrade", side_effect=Exception("forced error")), \
             patch.object(mod.sys, "exit"):
            with caplog.at_level(logging.CRITICAL, logger="app.db.migrations"):
                mod.run_migrations_on_startup()

        assert any(record.levelname == "CRITICAL" for record in caplog.records)
