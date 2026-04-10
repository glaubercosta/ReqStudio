"""Application configuration via Pydantic BaseSettings.

Validates all environment variables at startup (fail fast).
Uses SettingsConfigDict (Pydantic v2) — NOT legacy class Config.
"""

import logging

from pydantic_settings import BaseSettings, SettingsConfigDict

_JWT_PLACEHOLDER = "change-me-in-production-use-openssl-rand-hex-32"

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """ReqStudio API configuration.

    All values can be overridden via environment variables or .env file.
    Missing required variables will cause startup failure.
    """

    # --- API ---
    API_PORT: int = 8000
    API_HOST: str = "0.0.0.0"
    DEBUG: bool = False
    TESTING: bool = False  # Set to True in test environments to skip migrations

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://reqstudio:reqstudio@db:5432/reqstudio"
    DATABASE_TEST_URL: str = (
        "postgresql+asyncpg://reqstudio:reqstudio@db:5432/reqstudio_test"
    )

    # --- Postgres (Docker Compose) ---
    POSTGRES_USER: str = "reqstudio"
    POSTGRES_PASSWORD: str = "reqstudio"
    POSTGRES_DB: str = "reqstudio"
    DB_PORT: int = 5432

    # --- CORS ---
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    # --- Frontend ---
    FRONTEND_PORT: int = 5173

    # --- JWT ---
    JWT_SECRET_KEY: str = _JWT_PLACEHOLDER
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- LLM (Story 5.3) ---
    LLM_MODEL: str = "anthropic/claude-sonnet-4-20250514"
    LLM_FALLBACK_MODEL: str | None = None
    LLM_TIMEOUT: int = 60  # seconds
    LLM_MAX_CONTEXT_TOKENS: int = 8000
    LLM_API_KEY: str = ""  # ANTHROPIC_API_KEY ou equivalente

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def validate_production_secrets(self) -> None:
        """Reject insecure defaults when not in DEBUG/TESTING mode.

        Must be called after instantiation (not in __init__) because
        Pydantic BaseSettings loads env vars during construction.
        """
        if self.DEBUG or self.TESTING:
            return
        if self.JWT_SECRET_KEY == _JWT_PLACEHOLDER:
            raise SystemExit(
                "FATAL: JWT_SECRET_KEY is still the default placeholder. "
                "Set a strong random key via environment variable: "
                "export JWT_SECRET_KEY=$(openssl rand -hex 32)"
            )


settings = Settings()
settings.validate_production_secrets()
