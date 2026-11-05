from __future__ import annotations

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

EXPECTED_DATABASE_REVISION = "20261106_0001"


class DatabaseNotReady(RuntimeError):
    pass


def check_database_readiness(
    engine: Engine,
    expected_revision: str = EXPECTED_DATABASE_REVISION,
) -> None:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            revision = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one_or_none()
    except SQLAlchemyError as error:
        raise DatabaseNotReady("PostgreSQL is unavailable or uninitialized") from error

    if revision != expected_revision:
        raise DatabaseNotReady(f"Database revision is {revision!r}; expected {expected_revision!r}")
