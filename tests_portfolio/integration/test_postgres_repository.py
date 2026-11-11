from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from portfolio_app.db.models import PortfolioRecord
from portfolio_app.models.portfolio import Portfolio, PortfolioStatus
from portfolio_app.repositories.sqlalchemy_portfolio_repository import (
    SqlAlchemyPortfolioRepository,
)

NOW = datetime(2026, 11, 12, 8, 0, tzinfo=timezone.utc)


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


def test_repository_crud_filter_order_and_pagination(
    portfolio_postgres_engine: Engine,
) -> None:
    first = make_portfolio("PORT-3", created_at=NOW + timedelta(minutes=1))
    second = make_portfolio("PORT-1")
    third = make_portfolio(
        "PORT-2",
        owner="RATES-OPS",
        status=PortfolioStatus.INACTIVE,
        created_at=NOW + timedelta(minutes=1),
    )

    with Session(portfolio_postgres_engine, expire_on_commit=False) as session:
        repository = SqlAlchemyPortfolioRepository(session)
        for portfolio in (first, second, third):
            assert repository.create(portfolio) == portfolio
        updated = Portfolio(
            **{
                **first.__dict__,
                "name": "Renamed Portfolio",
                "updated_at": NOW + timedelta(minutes=5),
            }
        )
        assert repository.replace(updated) == updated
        session.commit()

    with Session(portfolio_postgres_engine) as session:
        repository = SqlAlchemyPortfolioRepository(session)
        assert repository.get(first.portfolio_id) == updated
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
        assert page == [third]


def test_rollback_discards_uncommitted_create(portfolio_postgres_engine: Engine) -> None:
    with Session(portfolio_postgres_engine, expire_on_commit=False) as session:
        repository = SqlAlchemyPortfolioRepository(session)
        portfolio = repository.create(make_portfolio("PORT-ROLLBACK"))
        session.rollback()

    with Session(portfolio_postgres_engine) as session:
        assert SqlAlchemyPortfolioRepository(session).get(portfolio.portfolio_id) is None


@pytest.mark.parametrize(
    ("field", "value"),
    [("name", ""), ("owner", ""), ("status", "ARCHIVED")],
)
def test_database_constraints_reject_invalid_records(
    portfolio_postgres_engine: Engine,
    field: str,
    value: str,
) -> None:
    values = {
        "portfolio_id": "PORT-INVALID",
        "name": "Portfolio",
        "owner": "CREDIT-OPS",
        "status": "ACTIVE",
        "created_at": NOW,
        "updated_at": NOW,
    }
    values[field] = value

    with Session(portfolio_postgres_engine) as session:
        session.add(PortfolioRecord(**values))
        with pytest.raises(IntegrityError):
            session.flush()
