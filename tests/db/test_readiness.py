from __future__ import annotations

from unittest.mock import MagicMock, create_autospec

import pytest
from sqlalchemy import Engine
from sqlalchemy.exc import OperationalError

from app.db.readiness import DatabaseNotReady, check_database_readiness


def engine_with_revision(revision: str | None) -> tuple[Engine, MagicMock]:
    engine = create_autospec(Engine, instance=True)
    connection = MagicMock()
    engine.connect.return_value.__enter__.return_value = connection
    revision_result = MagicMock()
    revision_result.scalar_one_or_none.return_value = revision
    connection.execute.side_effect = [MagicMock(), revision_result]
    return engine, connection


def test_readiness_accepts_reachable_current_database() -> None:
    engine, connection = engine_with_revision("20261106_0001")

    check_database_readiness(engine)

    assert connection.execute.call_count == 2


@pytest.mark.parametrize("revision", [None, "old_revision"])
def test_readiness_rejects_missing_or_stale_revision(revision: str | None) -> None:
    engine, _ = engine_with_revision(revision)

    with pytest.raises(DatabaseNotReady, match="expected"):
        check_database_readiness(engine)


def test_readiness_maps_database_connection_errors() -> None:
    engine = create_autospec(Engine, instance=True)
    engine.connect.side_effect = OperationalError("connect", {}, Exception("offline"))

    with pytest.raises(DatabaseNotReady, match="unavailable or uninitialized"):
        check_database_readiness(engine)
