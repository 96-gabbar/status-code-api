from __future__ import annotations

from portfolio_app.models.portfolio import Portfolio, PortfolioStatus


class InMemoryPortfolioRepository:
    def __init__(self) -> None:
        self._items: dict[str, Portfolio] = {}

    def create(self, portfolio: Portfolio) -> Portfolio:
        self._items[portfolio.portfolio_id] = portfolio
        return portfolio

    def get(self, portfolio_id: str) -> Portfolio | None:
        return self._items.get(portfolio_id)

    def replace(self, portfolio: Portfolio) -> Portfolio:
        self._items[portfolio.portfolio_id] = portfolio
        return portfolio

    def list(
        self,
        *,
        status: PortfolioStatus | None = None,
        owner: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Portfolio], int]:
        items = [
            item
            for item in self._items.values()
            if (status is None or item.status is status) and (owner is None or item.owner == owner)
        ]
        items.sort(key=lambda item: item.portfolio_id)
        items.sort(key=lambda item: item.created_at, reverse=True)
        total = len(items)
        return items[offset : offset + limit], total
