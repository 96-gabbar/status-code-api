from __future__ import annotations

import pytest
from pydantic import ValidationError

from portfolio_app.config import PortfolioSettings


def test_safe_defaults_use_memory_and_dedicated_database() -> None:
    settings = PortfolioSettings(_env_file=None)

    assert settings.repository_backend == "memory"
    assert settings.database_url.get_secret_value().endswith("/portfolio_service")
    assert settings.log_level == "INFO"


def test_portfolio_environment_variables_override_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PORTFOLIO_API_REPOSITORY_BACKEND", "postgres")
    monkeypatch.setenv(
        "PORTFOLIO_DATABASE_URL",
        "postgresql+psycopg://user:secret@portfolio-db:5432/portfolio_test",
    )
    monkeypatch.setenv("PORTFOLIO_API_LOG_LEVEL", "debug")

    settings = PortfolioSettings(_env_file=None)

    assert settings.repository_backend == "postgres"
    assert settings.database_url.get_secret_value().endswith("/portfolio_test")
    assert settings.log_level == "DEBUG"


def test_invalid_repository_backend_is_rejected() -> None:
    with pytest.raises(ValidationError):
        PortfolioSettings(_env_file=None, repository_backend="sqlite")
