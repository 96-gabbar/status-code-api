from __future__ import annotations

from typing import Protocol

from app.models.exception import Severity, Status, TradeException


class ExceptionRepository(Protocol):
    """Storage behavior required by the exception service."""

    def create(self, item: TradeException) -> TradeException: ...

    def get(self, exception_id: str) -> TradeException | None: ...

    def list(
        self,
        *,
        status: Status | None,
        severity: Severity | None,
        portfolio_id: str | None,
        exception_type: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[TradeException], int]: ...

    def replace(self, item: TradeException) -> TradeException: ...

    def next_exception_id(self) -> str: ...
