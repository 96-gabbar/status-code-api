from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config import Settings

CONFIGURATION_VARIABLES = (
    "STATUS_CODE_API_ENVIRONMENT",
    "STATUS_CODE_API_REPOSITORY_BACKEND",
    "STATUS_CODE_API_DATABASE_URL",
    "DATABASE_URL",
    "STATUS_CODE_API_LOG_LEVEL",
    "STATUS_CODE_API_SQL_ECHO",
)


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in CONFIGURATION_VARIABLES:
        monkeypatch.delenv(variable, raising=False)


def settings_without_env_file() -> Settings:
    return Settings(_env_file=None)


def test_development_defaults_are_safe_for_unit_tests() -> None:
    settings = settings_without_env_file()

    assert settings.environment == "development"
    assert settings.repository_backend == "memory"
    assert settings.log_level == "INFO"
    assert settings.sql_echo is False
    assert settings.database_url.get_secret_value().startswith("postgresql+psycopg://")


def test_prefixed_environment_variables_override_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("STATUS_CODE_API_ENVIRONMENT", "test")
    monkeypatch.setenv("STATUS_CODE_API_REPOSITORY_BACKEND", "postgres")
    monkeypatch.setenv(
        "STATUS_CODE_API_DATABASE_URL",
        "postgresql+psycopg://user:secret@database:5432/test_database",
    )
    monkeypatch.setenv("STATUS_CODE_API_LOG_LEVEL", "debug")
    monkeypatch.setenv("STATUS_CODE_API_SQL_ECHO", "true")

    settings = settings_without_env_file()

    assert settings.environment == "test"
    assert settings.repository_backend == "postgres"
    assert settings.database_url.get_secret_value().endswith("/test_database")
    assert settings.log_level == "DEBUG"
    assert settings.sql_echo is True


def test_standard_database_url_alias_is_supported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:secret@database:5432/alias_database",
    )

    assert settings_without_env_file().database_url.get_secret_value().endswith("/alias_database")


@pytest.mark.parametrize(
    ("variable", "value"),
    [
        ("STATUS_CODE_API_ENVIRONMENT", "staging"),
        ("STATUS_CODE_API_REPOSITORY_BACKEND", "sqlite"),
        ("STATUS_CODE_API_LOG_LEVEL", "TRACE"),
        ("STATUS_CODE_API_SQL_ECHO", "sometimes"),
    ],
)
def test_invalid_configuration_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    variable: str,
    value: str,
) -> None:
    monkeypatch.setenv(variable, value)

    with pytest.raises(ValidationError):
        settings_without_env_file()


def test_database_credentials_are_masked_in_text_and_repr(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "postgresql+psycopg://user:do-not-log@database:5432/status_code_api"
    monkeypatch.setenv("DATABASE_URL", secret)

    settings = settings_without_env_file()

    assert "do-not-log" not in str(settings.database_url)
    assert "do-not-log" not in repr(settings)
    assert "**********" in repr(settings)
