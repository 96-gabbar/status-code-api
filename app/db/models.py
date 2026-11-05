from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Index, Sequence, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

exception_id_sequence = Sequence(
    "exception_id_seq",
    start=10001,
    metadata=Base.metadata,
)


class TradeExceptionRecord(Base):
    __tablename__ = "trade_exceptions"
    __table_args__ = (
        CheckConstraint(
            "exception_id ~ '^EXC-[0-9]+$'",
            name="ck_trade_exceptions_exception_id_format",
        ),
        CheckConstraint(
            "type IN ('SETTLEMENT_MISMATCH', 'MISSING_REFERENCE_DATA', "
            "'POSITION_MISMATCH', 'PRICE_VARIANCE', 'CASH_BREAK', 'OTHER')",
            name="ck_trade_exceptions_type",
        ),
        CheckConstraint(
            "severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name="ck_trade_exceptions_severity",
        ),
        CheckConstraint(
            "status IN ('OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED')",
            name="ck_trade_exceptions_status",
        ),
        CheckConstraint(
            "char_length(portfolio_id) BETWEEN 1 AND 64",
            name="ck_trade_exceptions_portfolio_id_length",
        ),
        CheckConstraint(
            "char_length(transaction_id) BETWEEN 1 AND 64",
            name="ck_trade_exceptions_transaction_id_length",
        ),
        CheckConstraint(
            "char_length(description) BETWEEN 1 AND 2000",
            name="ck_trade_exceptions_description_length",
        ),
        CheckConstraint(
            "assigned_to IS NULL OR char_length(assigned_to) BETWEEN 1 AND 100",
            name="ck_trade_exceptions_assigned_to_length",
        ),
        CheckConstraint(
            "resolution_code IS NULL OR char_length(resolution_code) BETWEEN 1 AND 100",
            name="ck_trade_exceptions_resolution_code_length",
        ),
        CheckConstraint(
            "resolution_notes IS NULL OR char_length(resolution_notes) BETWEEN 1 AND 2000",
            name="ck_trade_exceptions_resolution_notes_length",
        ),
        Index("ix_trade_exceptions_portfolio_id", "portfolio_id"),
        Index("ix_trade_exceptions_severity", "severity"),
        Index("ix_trade_exceptions_status", "status"),
        Index("ix_trade_exceptions_created_id", "created_at", "id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    exception_id: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    portfolio_id: Mapped[str] = mapped_column(String(64), nullable=False)
    transaction_id: Mapped[str] = mapped_column(String(64), nullable=False)
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    assigned_to: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolution_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
