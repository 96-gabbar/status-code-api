from unittest.mock import create_autospec

from sqlalchemy.orm import Session

from app.repositories.sqlalchemy_exception_repository import (
    SqlAlchemyExceptionRepository,
)


def test_next_exception_id_uses_database_sequence() -> None:
    session = create_autospec(Session, instance=True)
    session.scalar.return_value = 10001
    repository = SqlAlchemyExceptionRepository(session)

    assert repository.next_exception_id() == "EXC-10001"
    session.scalar.assert_called_once()


def test_next_exception_id_rejects_missing_sequence_value() -> None:
    session = create_autospec(Session, instance=True)
    session.scalar.return_value = None
    repository = SqlAlchemyExceptionRepository(session)

    try:
        repository.next_exception_id()
    except RuntimeError as error:
        assert "sequence value" in str(error)
    else:
        raise AssertionError("Expected a missing sequence value to fail")
