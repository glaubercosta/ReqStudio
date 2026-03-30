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
    JWT_SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
