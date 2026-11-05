from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text

from alembic import command


@pytest.fixture(scope="session")
def postgres_engine() -> Iterator[Engine]:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL integration tests")

    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.upgrade(config, "head")
    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(autouse=True)
def clean_postgres(postgres_engine: Engine) -> Iterator[None]:
    with postgres_engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE trade_exceptions RESTART IDENTITY"))
        connection.execute(text("ALTER SEQUENCE exception_id_seq RESTART WITH 10001"))
    yield
    with postgres_engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE trade_exceptions RESTART IDENTITY"))
        connection.execute(text("ALTER SEQUENCE exception_id_seq RESTART WITH 10001"))
