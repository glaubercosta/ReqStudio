"""Application configuration via Pydantic BaseSettings.

Validates all environment variables at startup (fail fast).
Uses SettingsConfigDict (Pydantic v2) — NOT legacy class Config.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    DATABASE_TEST_URL: str = "postgresql+asyncpg://reqstudio:reqstudio@db:5432/reqstudio_test"

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
    JWT_SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
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


settings = Settings()
