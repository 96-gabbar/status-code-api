from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from portfolio_app.db.mappers import to_domain, to_record
from portfolio_app.db.models import PortfolioRecord
from portfolio_app.models.portfolio import Portfolio, PortfolioStatus

NOW = datetime(2026, 11, 12, 8, 0, tzinfo=timezone.utc)


def make_portfolio(**changes: object) -> Portfolio:
    values: dict[str, object] = {
        "portfolio_id": "PORT-201",
        "name": "Asia Credit Opportunities",
        "owner": "CREDIT-OPS",
        "status": PortfolioStatus.ACTIVE,
        "created_at": NOW,
        "updated_at": NOW,
    }
    values.update(changes)
    return Portfolio(**values)  # type: ignore[arg-type]


def test_domain_record_round_trip_preserves_every_field() -> None:
    portfolio = make_portfolio(status=PortfolioStatus.INACTIVE)

    record = to_record(portfolio)

    assert to_domain(record) == portfolio
    assert record.status == "INACTIVE"


def test_mapping_normalizes_aware_timestamps_to_utc() -> None:
    india = timezone(timedelta(hours=5, minutes=30))
    portfolio = make_portfolio(
        created_at=datetime(2026, 11, 12, 13, 30, tzinfo=india),
        updated_at=datetime(2026, 11, 12, 13, 35, tzinfo=india),
    )

    mapped = to_domain(to_record(portfolio))

    assert mapped.created_at == NOW
    assert mapped.updated_at == NOW + timedelta(minutes=5)


@pytest.mark.parametrize("field", ["created_at", "updated_at"])
def test_mapping_rejects_naive_timestamps(field: str) -> None:
    portfolio = make_portfolio(**{field: datetime(2026, 11, 12, 8, 0)})

    with pytest.raises(ValueError, match="timezone-aware"):
        to_record(portfolio)


def test_mapping_rejects_unknown_persisted_status() -> None:
    record = to_record(make_portfolio())
    record.status = "ARCHIVED"

    with pytest.raises(ValueError, match="ARCHIVED"):
        to_domain(record)


def test_table_metadata_contains_owned_constraints_and_query_indexes() -> None:
    table = PortfolioRecord.__table__
    constraint_names = {constraint.name for constraint in table.constraints}
    index_names = {index.name for index in table.indexes}

    assert {
        "ck_portfolios_portfolio_id_length",
        "ck_portfolios_name_length",
        "ck_portfolios_owner_length",
        "ck_portfolios_status",
    } <= constraint_names
    assert {
        "ix_portfolios_owner",
        "ix_portfolios_status",
        "ix_portfolios_created_id",
    } == index_names
