from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Callable

import pytest

from app.models.exception import ExceptionType, Severity, Status, TradeException
from app.repositories.exception_repository import ExceptionRepository
from app.repositories.in_memory_exception_repository import (
    InMemoryExceptionRepository,
)

RepositoryFactory = Callable[[], ExceptionRepository]


@pytest.fixture(params=[InMemoryExceptionRepository], ids=["in-memory"])
def repository_factory(
    request: pytest.FixtureRequest,
) -> RepositoryFactory:
    """Extend this fixture with each repository implementation in Week 2."""
    return request.param


def make_exception(exception_id: str, **changes: object) -> TradeException:
    created_at = datetime(2026, 11, 6, 10, 30, tzinfo=timezone.utc)
    values: dict[str, object] = {
        "exception_id": exception_id,
        "portfolio_id": "PORT-201",
        "transaction_id": "TXN-918273",
        "type": ExceptionType.SETTLEMENT_MISMATCH,
        "severity": Severity.HIGH,
        "status": Status.OPEN,
        "description": "Expected settlement amount differs",
        "assigned_to": None,
        "created_at": created_at,
        "updated_at": created_at,
        "resolution_code": None,
        "resolution_notes": None,
    }
    values.update(changes)
    return TradeException(**values)  # type: ignore[arg-type]


def list_items(
    repository: ExceptionRepository,
    *,
    status: Status | None = None,
    severity: Severity | None = None,
    portfolio_id: str | None = None,
    exception_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[TradeException], int]:
    return repository.list(
        status=status,
        severity=severity,
        portfolio_id=portfolio_id,
        exception_type=exception_type,
        limit=limit,
        offset=offset,
    )


def test_new_repository_is_empty_and_missing_get_returns_none(
    repository_factory: RepositoryFactory,
) -> None:
    repository = repository_factory()

    assert list_items(repository) == ([], 0)
    assert repository.get("EXC-99999") is None


def test_public_ids_are_sequential(
    repository_factory: RepositoryFactory,
) -> None:
    repository = repository_factory()

    assert repository.next_exception_id() == "EXC-10001"
    assert repository.next_exception_id() == "EXC-10002"


def test_create_round_trips_every_domain_field(
    repository_factory: RepositoryFactory,
) -> None:
    repository = repository_factory()
    item = make_exception(repository.next_exception_id())

    assert repository.create(item) == item
    assert repository.get(item.exception_id) == item
    assert list_items(repository) == ([item], 1)


def test_multiple_created_items_remain_available(
    repository_factory: RepositoryFactory,
) -> None:
    repository = repository_factory()
    first = make_exception(repository.next_exception_id())
    second = make_exception(
        repository.next_exception_id(),
        portfolio_id="PORT-202",
        severity=Severity.LOW,
    )

    repository.create(first)
    repository.create(second)

    items, total = list_items(repository)
    assert total == 2
    assert set(item.exception_id for item in items) == {
        first.exception_id,
        second.exception_id,
    }
    assert repository.get(first.exception_id) == first
    assert repository.get(second.exception_id) == second


def test_replace_persists_changes_without_duplicating_the_item(
    repository_factory: RepositoryFactory,
) -> None:
    repository = repository_factory()
    original = make_exception(repository.next_exception_id())
    repository.create(original)
    updated = replace(
        original,
        severity=Severity.CRITICAL,
        description="Investigation escalated",
        updated_at=datetime(2026, 11, 6, 11, 0, tzinfo=timezone.utc),
    )

    assert repository.replace(updated) == updated
    assert repository.get(original.exception_id) == updated
    assert list_items(repository) == ([updated], 1)


def test_list_returns_a_collection_that_cannot_remove_stored_items(
    repository_factory: RepositoryFactory,
) -> None:
    repository = repository_factory()
    item = make_exception(repository.next_exception_id())
    repository.create(item)

    returned_items, total = list_items(repository)
    returned_items.clear()

    assert total == 1
    assert list_items(repository) == ([item], 1)


def test_list_filters_before_counting_and_pagination(
    repository_factory: RepositoryFactory,
) -> None:
    repository = repository_factory()
    created_at = datetime(2026, 11, 6, 10, 30, tzinfo=timezone.utc)
    matching_first = make_exception(
        repository.next_exception_id(),
        portfolio_id="PORT-201",
        severity=Severity.HIGH,
        created_at=created_at,
    )
    non_matching = make_exception(
        repository.next_exception_id(),
        portfolio_id="PORT-202",
        severity=Severity.LOW,
        created_at=created_at,
    )
    matching_second = make_exception(
        repository.next_exception_id(),
        portfolio_id="PORT-201",
        severity=Severity.HIGH,
        created_at=created_at,
    )
    for item in (matching_first, non_matching, matching_second):
        repository.create(item)

    items, total = list_items(
        repository,
        portfolio_id="PORT-201",
        severity=Severity.HIGH,
        limit=1,
        offset=1,
    )

    assert total == 2
    assert items == [matching_second]
