from __future__ import annotations

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

EXPECTED_PORTFOLIO_DATABASE_REVISION = "20261112_0001"


class PortfolioDatabaseNotReady(RuntimeError):
    pass


def check_portfolio_database_readiness(
    engine: Engine,
    expected_revision: str = EXPECTED_PORTFOLIO_DATABASE_REVISION,
) -> None:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            revision = connection.execute(
                text("SELECT version_num FROM portfolio_alembic_version")
            ).scalar_one_or_none()
    except SQLAlchemyError as error:
        raise PortfolioDatabaseNotReady(
            "Portfolio PostgreSQL is unavailable or uninitialized"
        ) from error

    if revision != expected_revision:
        raise PortfolioDatabaseNotReady(
            f"Portfolio database revision is {revision!r}; expected {expected_revision!r}"
        )
