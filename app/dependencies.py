from __future__ import annotations

from collections.abc import Iterator

from fastapi import Request

from app.repositories.sqlalchemy_exception_repository import (
    SqlAlchemyExceptionRepository,
)
from app.services.exception_service import ExceptionService


def get_exception_service(request: Request) -> Iterator[ExceptionService]:
    """Provide a service and own the transaction for one HTTP request."""
    settings = request.app.state.settings
    if settings.repository_backend == "memory":
        yield request.app.state.exception_service
        return

    session = request.app.state.session_factory()
    try:
        yield ExceptionService(SqlAlchemyExceptionRepository(session))
        session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()
