from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.mappers import to_domain, to_record
from app.db.models import TradeExceptionRecord, exception_id_sequence
from app.models.exception import Severity, Status, TradeException


class SqlAlchemyExceptionRepository:
    """PostgreSQL repository; transaction ownership belongs to the caller."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, item: TradeException) -> TradeException:
        record = to_record(item)
        self.session.add(record)
        self.session.flush()
        return to_domain(record)

    def get(self, exception_id: str) -> TradeException | None:
        record = self.session.scalar(
            select(TradeExceptionRecord).where(TradeExceptionRecord.exception_id == exception_id)
        )
        return to_domain(record) if record is not None else None

    def list(
        self,
        *,
        status: Status | None,
        severity: Severity | None,
        portfolio_id: str | None,
        exception_type: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[TradeException], int]:
        filters = []
        if status is not None:
            filters.append(TradeExceptionRecord.status == status.value)
        if severity is not None:
            filters.append(TradeExceptionRecord.severity == severity.value)
        if portfolio_id is not None:
            filters.append(TradeExceptionRecord.portfolio_id == portfolio_id)
        if exception_type is not None:
            filters.append(TradeExceptionRecord.type == exception_type)

        total = self.session.scalar(
            select(func.count()).select_from(TradeExceptionRecord).where(*filters)
        )
        records = self.session.scalars(
            select(TradeExceptionRecord)
            .where(*filters)
            .order_by(TradeExceptionRecord.created_at, TradeExceptionRecord.id)
            .offset(offset)
            .limit(limit)
        ).all()
        return [to_domain(record) for record in records], int(total or 0)

    def replace(self, item: TradeException) -> TradeException:
        record = self.session.scalar(
            select(TradeExceptionRecord).where(
                TradeExceptionRecord.exception_id == item.exception_id
            )
        )
        if record is None:
            raise KeyError(item.exception_id)

        replacement = to_record(item)
        for attribute in (
            "portfolio_id",
            "transaction_id",
            "type",
            "severity",
            "status",
            "description",
            "assigned_to",
            "created_at",
            "updated_at",
            "resolution_code",
            "resolution_notes",
        ):
            setattr(record, attribute, getattr(replacement, attribute))
        self.session.flush()
        return to_domain(record)

    def next_exception_id(self) -> str:
        value = self.session.scalar(select(exception_id_sequence.next_value()))
        if value is None:
            raise RuntimeError("PostgreSQL did not return an exception ID sequence value")
        return f"EXC-{value}"
