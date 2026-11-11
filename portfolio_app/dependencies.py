from __future__ import annotations

from collections.abc import Iterator

from fastapi import Request

from portfolio_app.repositories.sqlalchemy_portfolio_repository import (
    SqlAlchemyPortfolioRepository,
)
from portfolio_app.services.portfolio_service import PortfolioService


def get_portfolio_service(request: Request) -> Iterator[PortfolioService]:
    settings = request.app.state.settings
    if settings.repository_backend == "memory":
        yield request.app.state.portfolio_service
        return

    session = request.app.state.session_factory()
    try:
        yield PortfolioService(SqlAlchemyPortfolioRepository(session))
        session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()
