from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text

from alembic import command


@pytest.fixture(scope="session")
def portfolio_postgres_engine() -> Iterator[Engine]:
    database_url = os.getenv("TEST_PORTFOLIO_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_PORTFOLIO_DATABASE_URL is required for Portfolio integration tests")

    config = Config("portfolio_alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.upgrade(config, "head")
    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(autouse=True)
def clean_portfolio_postgres(portfolio_postgres_engine: Engine) -> Iterator[None]:
    with portfolio_postgres_engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE portfolios"))
    yield
    with portfolio_postgres_engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE portfolios"))
