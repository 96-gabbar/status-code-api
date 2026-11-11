from datetime import datetime, timedelta, timezone

import pytest

from portfolio_app.models.portfolio import PortfolioStatus
from portfolio_app.repositories.in_memory_portfolio_repository import (
    InMemoryPortfolioRepository,
)
from portfolio_app.services.portfolio_service import (
    CreatePortfolio,
    PortfolioAlreadyExistsError,
    PortfolioNotFoundError,
    PortfolioService,
    UpdatePortfolio,
)

NOW = datetime(2026, 11, 12, 8, 0, tzinfo=timezone.utc)


def create(service: PortfolioService, portfolio_id: str = "PORT-201"):
    return service.create(
        CreatePortfolio(
            portfolio_id=portfolio_id,
            name=f"Portfolio {portfolio_id}",
            owner="CREDIT-OPS",
        )
    )


def test_create_defaults_active_and_uses_utc_clock():
    service = PortfolioService(clock=lambda: NOW)
    portfolio = create(service)

    assert portfolio.status is PortfolioStatus.ACTIVE
    assert portfolio.created_at == NOW
    assert portfolio.updated_at == NOW
    assert service.get("PORT-201") == portfolio


def test_create_rejects_duplicate_identifier_without_replacing_existing():
    service = PortfolioService(clock=lambda: NOW)
    original = create(service)

    with pytest.raises(PortfolioAlreadyExistsError):
        create(service)

    assert service.get("PORT-201") == original


def test_create_normalizes_fields_and_enforces_domain_lengths():
    service = PortfolioService(clock=lambda: NOW)

    portfolio = service.create(
        CreatePortfolio(portfolio_id=" PORT-201 ", name=" Portfolio ", owner=" OPS ")
    )

    assert portfolio.portfolio_id == "PORT-201"
    assert portfolio.name == "Portfolio"
    assert portfolio.owner == "OPS"
    with pytest.raises(ValueError, match="name must not be blank"):
        service.create(CreatePortfolio(portfolio_id="PORT-2", name=" ", owner="OPS"))
    with pytest.raises(ValueError, match="owner must be at most 100"):
        service.create(CreatePortfolio(portfolio_id="PORT-3", name="Name", owner="x" * 101))


def test_get_and_update_missing_portfolio_raise_not_found():
    service = PortfolioService(clock=lambda: NOW)
    with pytest.raises(PortfolioNotFoundError):
        service.get("PORT-404")
    with pytest.raises(PortfolioNotFoundError):
        service.update("PORT-404", UpdatePortfolio(status=PortfolioStatus.INACTIVE))


def test_update_changes_only_supplied_fields_and_updated_at():
    times = iter([NOW, NOW + timedelta(minutes=5)])
    service = PortfolioService(clock=lambda: next(times))
    original = create(service)

    updated = service.update(
        original.portfolio_id,
        UpdatePortfolio(name="Renamed", status=PortfolioStatus.INACTIVE),
    )

    assert updated.name == "Renamed"
    assert updated.owner == original.owner
    assert updated.status is PortfolioStatus.INACTIVE
    assert updated.created_at == original.created_at
    assert updated.updated_at == NOW + timedelta(minutes=5)


def test_update_rejects_empty_command_and_blank_supplied_field():
    service = PortfolioService(clock=lambda: NOW)
    create(service)

    with pytest.raises(ValueError, match="At least one"):
        service.update("PORT-201", UpdatePortfolio())
    with pytest.raises(ValueError, match="owner must not be blank"):
        service.update("PORT-201", UpdatePortfolio(owner=" "))


def test_clock_must_be_timezone_aware():
    service = PortfolioService(clock=lambda: datetime(2026, 11, 12, 8, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        create(service)


def test_repository_instances_are_isolated():
    first = PortfolioService(clock=lambda: NOW)
    second = PortfolioService(clock=lambda: NOW)
    create(first)
    with pytest.raises(PortfolioNotFoundError):
        second.get("PORT-201")


def test_list_filters_orders_counts_then_paginates():
    times = iter(
        [
            NOW,
            NOW + timedelta(seconds=1),
            NOW + timedelta(seconds=1),
            NOW + timedelta(seconds=2),
        ]
    )
    service = PortfolioService(clock=lambda: next(times))
    create(service, "PORT-1")
    create(service, "PORT-3")
    third = create(service, "PORT-2")
    service.update("PORT-2", UpdatePortfolio(owner="RATES-OPS"))

    items, total = service.list(limit=2, offset=0)
    assert [item.portfolio_id for item in items] == ["PORT-2", "PORT-3"]
    assert total == 3

    items, total = service.list(owner="RATES-OPS", limit=20, offset=0)
    assert items == [service.get(third.portfolio_id)]
    assert total == 1


def test_service_depends_on_repository_protocol():
    repository = InMemoryPortfolioRepository()
    service = PortfolioService(repository=repository, clock=lambda: NOW)
    portfolio = create(service)
    assert repository.get(portfolio.portfolio_id) == portfolio
