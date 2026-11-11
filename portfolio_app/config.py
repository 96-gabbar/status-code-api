from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class PortfolioSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PORTFOLIO_API_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "development"
    repository_backend: Literal["memory", "postgres"] = "memory"
    database_url: SecretStr = Field(
        default=SecretStr(
            "postgresql+psycopg://status_code_api:status_code_api@localhost:5432/portfolio_service"
        ),
        validation_alias=AliasChoices("PORTFOLIO_API_DATABASE_URL", "PORTFOLIO_DATABASE_URL"),
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    sql_echo: bool = False

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value


@lru_cache
def get_portfolio_settings() -> PortfolioSettings:
    return PortfolioSettings()
