from __future__ import annotations

from datetime import datetime, timezone

from app.db.models import TradeExceptionRecord
from app.models.exception import ExceptionType, Severity, Status, TradeException


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Database timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


def to_record(item: TradeException) -> TradeExceptionRecord:
    return TradeExceptionRecord(
        exception_id=item.exception_id,
        portfolio_id=item.portfolio_id,
        transaction_id=item.transaction_id,
        type=item.type.value,
        severity=item.severity.value,
        status=item.status.value,
        description=item.description,
        assigned_to=item.assigned_to,
        created_at=_as_utc(item.created_at),
        updated_at=_as_utc(item.updated_at),
        resolution_code=item.resolution_code,
        resolution_notes=item.resolution_notes,
    )


def to_domain(record: TradeExceptionRecord) -> TradeException:
    return TradeException(
        exception_id=record.exception_id,
        portfolio_id=record.portfolio_id,
        transaction_id=record.transaction_id,
        type=ExceptionType(record.type),
        severity=Severity(record.severity),
        status=Status(record.status),
        description=record.description,
        assigned_to=record.assigned_to,
        created_at=_as_utc(record.created_at),
        updated_at=_as_utc(record.updated_at),
        resolution_code=record.resolution_code,
        resolution_notes=record.resolution_notes,
    )
