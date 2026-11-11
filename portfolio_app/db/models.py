from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from portfolio_app.db.base import PortfolioBase


class PortfolioRecord(PortfolioBase):
    __tablename__ = "portfolios"
    __table_args__ = (
        CheckConstraint(
            "char_length(portfolio_id) BETWEEN 1 AND 64",
            name="ck_portfolios_portfolio_id_length",
        ),
        CheckConstraint(
            "char_length(name) BETWEEN 1 AND 200",
            name="ck_portfolios_name_length",
        ),
        CheckConstraint(
            "char_length(owner) BETWEEN 1 AND 100",
            name="ck_portfolios_owner_length",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_portfolios_status",
        ),
        Index("ix_portfolios_owner", "owner"),
        Index("ix_portfolios_status", "status"),
        Index("ix_portfolios_created_id", "created_at", "portfolio_id"),
    )

    portfolio_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    owner: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
