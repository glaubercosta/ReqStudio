"""Tests for configuration — Story 1.1 AC#5.

Testa comportamento e estrutura da configuração, não valores hardcoded
que variam por ambiente (.env do desenvolvedor pode sobrescrever defaults).
"""

from app.core.config import Settings


def test_settings_loads_correctly():
    """Settings carrega sem erros e tem todos os campos obrigatórios."""
    s = Settings()
    assert isinstance(s.API_PORT, int)
    assert s.API_PORT > 0
    assert isinstance(s.DEBUG, bool)
    assert "asyncpg" in s.DATABASE_URL
    assert s.POSTGRES_USER  # não vazio
    assert s.POSTGRES_PASSWORD  # não vazio
    assert s.POSTGRES_DB  # não vazio


def test_settings_cors_origins_is_string():
    """ALLOWED_ORIGINS é uma string não-vazia (valor varia por ambiente)."""
    s = Settings()
    assert isinstance(s.ALLOWED_ORIGINS, str)
    assert len(s.ALLOWED_ORIGINS) > 0
    assert "localhost" in s.ALLOWED_ORIGINS


def test_settings_database_url_structure():
    """DATABASE_URL tem o formato correto para asyncpg."""
    s = Settings()
    assert s.DATABASE_URL.startswith("postgresql+asyncpg://")
    assert "@" in s.DATABASE_URL


def test_settings_defaults_when_no_env(monkeypatch):
    """Com variáveis de ambiente limpas, settings usa os defaults corretos."""
    # Remove variáveis que o .env do ambiente pode sobrescrever
    for var in ("API_PORT", "ALLOWED_ORIGINS", "FRONTEND_PORT", "DEBUG"):
        monkeypatch.delenv(var, raising=False)

    # Cria nova instância sem ler do .env do ambiente
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.API_PORT == 8000
    assert s.DEBUG is False
    assert "localhost:5173" in s.ALLOWED_ORIGINS
