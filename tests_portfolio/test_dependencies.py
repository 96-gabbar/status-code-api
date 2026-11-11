from types import SimpleNamespace
from unittest.mock import create_autospec

import pytest
from sqlalchemy.orm import Session

from portfolio_app.config import PortfolioSettings
from portfolio_app.dependencies import get_portfolio_service
from portfolio_app.repositories.sqlalchemy_portfolio_repository import (
    SqlAlchemyPortfolioRepository,
)
from portfolio_app.services.portfolio_service import PortfolioService


def request_for(state: object) -> object:
    return SimpleNamespace(app=SimpleNamespace(state=state))


def test_memory_backend_reuses_application_service() -> None:
    expected = PortfolioService()
    state = SimpleNamespace(
        settings=PortfolioSettings(_env_file=None, repository_backend="memory"),
        portfolio_service=expected,
    )
    dependency = get_portfolio_service(request_for(state))  # type: ignore[arg-type]

    assert next(dependency) is expected
    with pytest.raises(StopIteration):
        next(dependency)


def test_postgres_backend_commits_and_closes_after_success() -> None:
    session = create_autospec(Session, instance=True)
    state = SimpleNamespace(
        settings=PortfolioSettings(_env_file=None, repository_backend="postgres"),
        session_factory=lambda: session,
    )
    dependency = get_portfolio_service(request_for(state))  # type: ignore[arg-type]

    service = next(dependency)

    assert isinstance(service.repository, SqlAlchemyPortfolioRepository)
    assert service.repository.session is session
    with pytest.raises(StopIteration):
        next(dependency)
    session.commit.assert_called_once_with()
    session.rollback.assert_not_called()
    session.close.assert_called_once_with()


def test_postgres_backend_rolls_back_and_closes_after_failure() -> None:
    session = create_autospec(Session, instance=True)
    state = SimpleNamespace(
        settings=PortfolioSettings(_env_file=None, repository_backend="postgres"),
        session_factory=lambda: session,
    )
    dependency = get_portfolio_service(request_for(state))  # type: ignore[arg-type]
    next(dependency)

    with pytest.raises(RuntimeError, match="request failed"):
        dependency.throw(RuntimeError("request failed"))

    session.commit.assert_not_called()
    session.rollback.assert_called_once_with()
    session.close.assert_called_once_with()
