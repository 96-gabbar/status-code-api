from types import SimpleNamespace
from unittest.mock import create_autospec

import pytest
from sqlalchemy.orm import Session

from app.config import Settings
from app.dependencies import get_exception_service
from app.repositories.sqlalchemy_exception_repository import (
    SqlAlchemyExceptionRepository,
)
from app.services.exception_service import ExceptionService


def request_for(state: object) -> object:
    return SimpleNamespace(app=SimpleNamespace(state=state))


def test_memory_backend_reuses_application_service() -> None:
    expected = ExceptionService()
    state = SimpleNamespace(
        settings=Settings(_env_file=None, repository_backend="memory"),
        exception_service=expected,
    )
    dependency = get_exception_service(request_for(state))  # type: ignore[arg-type]

    assert next(dependency) is expected
    with pytest.raises(StopIteration):
        next(dependency)


def test_postgres_backend_commits_and_closes_after_success() -> None:
    session = create_autospec(Session, instance=True)
    state = SimpleNamespace(
        settings=Settings(_env_file=None, repository_backend="postgres"),
        session_factory=lambda: session,
    )
    dependency = get_exception_service(request_for(state))  # type: ignore[arg-type]

    service = next(dependency)

    assert isinstance(service.repository, SqlAlchemyExceptionRepository)
    assert service.repository.session is session
    with pytest.raises(StopIteration):
        next(dependency)
    session.commit.assert_called_once_with()
    session.rollback.assert_not_called()
    session.close.assert_called_once_with()


def test_postgres_backend_rolls_back_and_closes_after_failure() -> None:
    session = create_autospec(Session, instance=True)
    state = SimpleNamespace(
        settings=Settings(_env_file=None, repository_backend="postgres"),
        session_factory=lambda: session,
    )
    dependency = get_exception_service(request_for(state))  # type: ignore[arg-type]
    next(dependency)

    with pytest.raises(RuntimeError, match="request failed"):
        dependency.throw(RuntimeError("request failed"))

    session.commit.assert_not_called()
    session.rollback.assert_called_once_with()
    session.close.assert_called_once_with()
