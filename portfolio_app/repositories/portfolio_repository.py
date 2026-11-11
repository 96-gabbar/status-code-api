from __future__ import annotations

from typing import Protocol

from portfolio_app.models.portfolio import Portfolio, PortfolioStatus


class PortfolioRepository(Protocol):
    def create(self, portfolio: Portfolio) -> Portfolio: ...

    def get(self, portfolio_id: str) -> Portfolio | None: ...

    def replace(self, portfolio: Portfolio) -> Portfolio: ...

    def list(
        self,
        *,
        status: PortfolioStatus | None = None,
        owner: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Portfolio], int]: ...
