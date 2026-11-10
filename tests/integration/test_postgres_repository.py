from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.models.exception import Severity, Status
from app.repositories.sqlalchemy_exception_repository import (
    SqlAlchemyExceptionRepository,
)
from app.schemas.exception import CreateExceptionRequest, UpdateExceptionRequest
from app.services.exception_service import ExceptionService


def payload(index: int = 1, severity: Severity = Severity.HIGH) -> CreateExceptionRequest:
    return CreateExceptionRequest(
        portfolio_id=f"PORT-{index}",
        transaction_id=f"TXN-{index}",
        type="SETTLEMENT_MISMATCH",
        severity=severity,
        description=f"Settlement mismatch {index}",
    )


def test_repository_persists_create_get_replace_filter_and_pagination(
    postgres_engine: Engine,
) -> None:
    with Session(postgres_engine, expire_on_commit=False) as session:
        service = ExceptionService(SqlAlchemyExceptionRepository(session))
        first = service.create(payload(1, Severity.HIGH))
        service.create(payload(2, Severity.LOW))
        third = service.create(payload(3, Severity.HIGH))
        updated = service.update(
            first.exception_id,
            UpdateExceptionRequest(description="Escalated investigation"),
        )
        session.commit()

    with Session(postgres_engine) as session:
        service = ExceptionService(SqlAlchemyExceptionRepository(session))
        assert service.get(first.exception_id) == updated
        items, total = service.list(
            status=Status.OPEN,
            severity=Severity.HIGH,
            portfolio_id=None,
            exception_type="SETTLEMENT_MISMATCH",
            limit=1,
            offset=1,
        )

    assert total == 2
    assert [item.exception_id for item in items] == [third.exception_id]


def test_concurrent_creates_allocate_unique_public_ids(postgres_engine: Engine) -> None:
    def create_one(index: int) -> str:
        with Session(postgres_engine, expire_on_commit=False) as session:
            service = ExceptionService(SqlAlchemyExceptionRepository(session))
            item = service.create(payload(index))
            session.commit()
            return item.exception_id

    with ThreadPoolExecutor(max_workers=8) as executor:
        identifiers = list(executor.map(create_one, range(1, 21)))

    assert len(identifiers) == 20
    assert len(set(identifiers)) == 20
    assert all(identifier.startswith("EXC-") for identifier in identifiers)


def test_rollback_discards_uncommitted_create(postgres_engine: Engine) -> None:
    with Session(postgres_engine, expire_on_commit=False) as session:
        service = ExceptionService(SqlAlchemyExceptionRepository(session))
        item = service.create(payload())
        session.rollback()

    with Session(postgres_engine) as session:
        repository = SqlAlchemyExceptionRepository(session)
        assert repository.get(item.exception_id) is None
