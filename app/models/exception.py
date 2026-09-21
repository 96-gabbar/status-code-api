from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from enum import Enum


class ExceptionType(str, Enum):
    SETTLEMENT_MISMATCH = "SETTLEMENT_MISMATCH"
    MISSING_REFERENCE_DATA = "MISSING_REFERENCE_DATA"
    POSITION_MISMATCH = "POSITION_MISMATCH"
    PRICE_VARIANCE = "PRICE_VARIANCE"
    CASH_BREAK = "CASH_BREAK"
    OTHER = "OTHER"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Status(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


@dataclass
class TradeException:
    exception_id: str
    portfolio_id: str
    transaction_id: str
    type: ExceptionType
    severity: Severity
    status: Status
    description: str
    assigned_to: str | None
    created_at: datetime
    updated_at: datetime
    resolution_code: str | None
    resolution_notes: str | None
