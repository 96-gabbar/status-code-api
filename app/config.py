from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="STATUS_CODE_API_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "development"
    repository_backend: Literal["memory", "postgres"] = "memory"
    database_url: SecretStr = Field(
        default=SecretStr(
            "postgresql+psycopg://status_code_api:status_code_api@localhost:5432/status_code_api"
        ),
        validation_alias=AliasChoices(
            "STATUS_CODE_API_DATABASE_URL",
            "DATABASE_URL",
        ),
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    sql_echo: bool = False
    portfolio_validation_enabled: bool = False
    portfolio_service_url: str = "http://portfolio-api:8001"
    portfolio_connect_timeout_seconds: float = Field(default=0.5, gt=0)
    portfolio_read_timeout_seconds: float = Field(default=1.0, gt=0)
    portfolio_retry_count: int = Field(default=1, ge=0, le=1)

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value


@lru_cache
def get_settings() -> Settings:
    return Settings()
