from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.db.mappers import to_domain, to_record
from app.models.exception import ExceptionType, Severity, Status, TradeException


def make_exception(**changes: object) -> TradeException:
    created_at = datetime(2026, 11, 6, 10, 30, tzinfo=timezone.utc)
    values: dict[str, object] = {
        "exception_id": "EXC-10001",
        "portfolio_id": "PORT-201",
        "transaction_id": "TXN-918273",
        "type": ExceptionType.SETTLEMENT_MISMATCH,
        "severity": Severity.HIGH,
        "status": Status.INVESTIGATING,
        "description": "Expected settlement amount differs",
        "assigned_to": "ops-user-123",
        "created_at": created_at,
        "updated_at": created_at + timedelta(minutes=5),
        "resolution_code": None,
        "resolution_notes": None,
    }
    values.update(changes)
    return TradeException(**values)  # type: ignore[arg-type]


def test_domain_record_round_trip_preserves_every_field() -> None:
    item = make_exception(
        status=Status.RESOLVED,
        resolution_code="REFERENCE_DATA_CORRECTED",
        resolution_notes="Mapping corrected",
    )

    record = to_record(item)

    assert to_domain(record) == item
    assert record.type == "SETTLEMENT_MISMATCH"
    assert record.severity == "HIGH"
    assert record.status == "RESOLVED"


def test_nullable_fields_round_trip_as_none() -> None:
    item = make_exception(
        status=Status.OPEN,
        assigned_to=None,
        resolution_code=None,
        resolution_notes=None,
    )

    assert to_domain(to_record(item)) == item


def test_mapping_normalizes_aware_timestamps_to_utc() -> None:
    india = timezone(timedelta(hours=5, minutes=30))
    item = make_exception(
        created_at=datetime(2026, 11, 6, 16, 0, tzinfo=india),
        updated_at=datetime(2026, 11, 6, 16, 5, tzinfo=india),
    )

    mapped = to_domain(to_record(item))

    assert mapped.created_at == datetime(2026, 11, 6, 10, 30, tzinfo=timezone.utc)
    assert mapped.updated_at == datetime(2026, 11, 6, 10, 35, tzinfo=timezone.utc)


@pytest.mark.parametrize("field", ["created_at", "updated_at"])
def test_mapping_rejects_naive_timestamps(field: str) -> None:
    item = make_exception(**{field: datetime(2026, 11, 6, 10, 30)})

    with pytest.raises(ValueError, match="timezone-aware"):
        to_record(item)
