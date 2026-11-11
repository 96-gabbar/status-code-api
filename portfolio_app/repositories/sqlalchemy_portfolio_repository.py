from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from portfolio_app.db.mappers import to_domain, to_record
from portfolio_app.db.models import PortfolioRecord
from portfolio_app.models.portfolio import Portfolio, PortfolioStatus


class SqlAlchemyPortfolioRepository:
    """PostgreSQL repository; transaction ownership belongs to the caller."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, portfolio: Portfolio) -> Portfolio:
        record = to_record(portfolio)
        self.session.add(record)
        self.session.flush()
        return to_domain(record)

    def get(self, portfolio_id: str) -> Portfolio | None:
        record = self.session.get(PortfolioRecord, portfolio_id)
        return to_domain(record) if record is not None else None

    def replace(self, portfolio: Portfolio) -> Portfolio:
        record = self.session.get(PortfolioRecord, portfolio.portfolio_id)
        if record is None:
            raise KeyError(portfolio.portfolio_id)

        replacement = to_record(portfolio)
        for attribute in ("name", "owner", "status", "created_at", "updated_at"):
            setattr(record, attribute, getattr(replacement, attribute))
        self.session.flush()
        return to_domain(record)

    def list(
        self,
        *,
        status: PortfolioStatus | None = None,
        owner: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Portfolio], int]:
        filters = []
        if status is not None:
            filters.append(PortfolioRecord.status == status.value)
        if owner is not None:
            filters.append(PortfolioRecord.owner == owner)

        total = self.session.scalar(
            select(func.count()).select_from(PortfolioRecord).where(*filters)
        )
        records = self.session.scalars(
            select(PortfolioRecord)
            .where(*filters)
            .order_by(PortfolioRecord.created_at.desc(), PortfolioRecord.portfolio_id)
            .offset(offset)
            .limit(limit)
        ).all()
        return [to_domain(record) for record in records], int(total or 0)
