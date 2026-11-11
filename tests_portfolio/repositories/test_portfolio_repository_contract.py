from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Callable

import pytest

from portfolio_app.models.portfolio import Portfolio, PortfolioStatus
from portfolio_app.repositories.in_memory_portfolio_repository import (
    InMemoryPortfolioRepository,
)
from portfolio_app.repositories.portfolio_repository import PortfolioRepository

RepositoryFactory = Callable[[], PortfolioRepository]
NOW = datetime(2026, 11, 12, 8, 0, tzinfo=timezone.utc)


@pytest.fixture(params=[InMemoryPortfolioRepository], ids=["in-memory"])
def repository_factory(request: pytest.FixtureRequest) -> RepositoryFactory:
    """The PostgreSQL implementation joins this contract in W3-07."""
    return request.param


def make_portfolio(portfolio_id: str, **changes: object) -> Portfolio:
    values: dict[str, object] = {
        "portfolio_id": portfolio_id,
        "name": f"Portfolio {portfolio_id}",
        "owner": "CREDIT-OPS",
        "status": PortfolioStatus.ACTIVE,
        "created_at": NOW,
        "updated_at": NOW,
    }
    values.update(changes)
    return Portfolio(**values)  # type: ignore[arg-type]


def test_new_repository_is_empty_and_missing_get_returns_none(
    repository_factory: RepositoryFactory,
) -> None:
    repository = repository_factory()

    assert repository.get("PORT-404") is None
    assert repository.list() == ([], 0)


def test_create_and_replace_round_trip_every_field_without_duplication(
    repository_factory: RepositoryFactory,
) -> None:
    repository = repository_factory()
    original = make_portfolio("PORT-201")
    updated = replace(
        original,
        name="Renamed portfolio",
        status=PortfolioStatus.INACTIVE,
        updated_at=NOW + timedelta(minutes=5),
    )

    assert repository.create(original) == original
    assert repository.get(original.portfolio_id) == original
    assert repository.replace(updated) == updated
    assert repository.get(original.portfolio_id) == updated
    assert repository.list() == ([updated], 1)


def test_list_filters_before_counting_and_pagination(
    repository_factory: RepositoryFactory,
) -> None:
    repository = repository_factory()
    items = (
        make_portfolio("PORT-3", created_at=NOW + timedelta(minutes=1)),
        make_portfolio("PORT-1"),
        make_portfolio(
            "PORT-2",
            owner="RATES-OPS",
            status=PortfolioStatus.INACTIVE,
            created_at=NOW + timedelta(minutes=1),
        ),
    )
    for item in items:
        repository.create(item)

    page, total = repository.list(limit=2, offset=0)
    assert total == 3
    assert [item.portfolio_id for item in page] == ["PORT-2", "PORT-3"]

    page, total = repository.list(
        status=PortfolioStatus.INACTIVE,
        owner="RATES-OPS",
        limit=1,
        offset=0,
    )
    assert total == 1
    assert page == [items[2]]


def test_returned_collection_cannot_remove_stored_items(
    repository_factory: RepositoryFactory,
) -> None:
    repository = repository_factory()
    item = make_portfolio("PORT-201")
    repository.create(item)

    returned, total = repository.list()
    returned.clear()

    assert total == 1
    assert repository.list() == ([item], 1)
