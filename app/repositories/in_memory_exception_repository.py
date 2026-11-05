from __future__ import annotations

from app.models.exception import Severity, Status, TradeException


class InMemoryExceptionRepository:
    """Process-local repository used by the default app and unit tests."""

    def __init__(self) -> None:
        self._items: dict[str, TradeException] = {}
        self._next_id = 10001

    def create(self, item: TradeException) -> TradeException:
        self._items[item.exception_id] = item
        return item

    def get(self, exception_id: str) -> TradeException | None:
        return self._items.get(exception_id)

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
        items = list(self._items.values())
        if status is not None:
            items = [item for item in items if item.status == status]
        if severity is not None:
            items = [item for item in items if item.severity == severity]
        if portfolio_id is not None:
            items = [item for item in items if item.portfolio_id == portfolio_id]
        if exception_type is not None:
            items = [item for item in items if item.type.value == exception_type]
        items.sort(
            key=lambda item: (
                item.created_at,
                int(item.exception_id.removeprefix("EXC-")),
            )
        )
        total = len(items)
        return items[offset : offset + limit], total

    def replace(self, item: TradeException) -> TradeException:
        self._items[item.exception_id] = item
        return item

    def next_exception_id(self) -> str:
        value = f"EXC-{self._next_id}"
        self._next_id += 1
        return value
