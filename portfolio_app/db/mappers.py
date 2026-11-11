from __future__ import annotations

from datetime import datetime, timezone

from portfolio_app.db.models import PortfolioRecord
from portfolio_app.models.portfolio import Portfolio, PortfolioStatus


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Database timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


def to_record(portfolio: Portfolio) -> PortfolioRecord:
    return PortfolioRecord(
        portfolio_id=portfolio.portfolio_id,
        name=portfolio.name,
        owner=portfolio.owner,
        status=portfolio.status.value,
        created_at=_as_utc(portfolio.created_at),
        updated_at=_as_utc(portfolio.updated_at),
    )


def to_domain(record: PortfolioRecord) -> Portfolio:
    return Portfolio(
        portfolio_id=record.portfolio_id,
        name=record.name,
        owner=record.owner,
        status=PortfolioStatus(record.status),
        created_at=_as_utc(record.created_at),
        updated_at=_as_utc(record.updated_at),
    )
