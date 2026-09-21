from __future__ import annotations

from app.models.exception import TradeException


class ExceptionRepository:
    def __init__(self) -> None:
        self._items: dict[str, TradeException] = {}
        self._next_id = 10001

    def create(self, item: TradeException) -> TradeException:
        self._items[item.exception_id] = item
        return item

    def get(self, exception_id: str) -> TradeException | None:
        return self._items.get(exception_id)

    def all(self) -> list[TradeException]:
        return list(self._items.values())

    def replace(self, item: TradeException) -> TradeException:
        self._items[item.exception_id] = item
        return item

    def next_exception_id(self) -> str:
        value = f"EXC-{self._next_id}"
        self._next_id += 1
        return value
