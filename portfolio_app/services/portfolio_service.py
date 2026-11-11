from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timezone

from portfolio_app.models.portfolio import Portfolio, PortfolioStatus
from portfolio_app.repositories.in_memory_portfolio_repository import (
    InMemoryPortfolioRepository,
)
from portfolio_app.repositories.portfolio_repository import PortfolioRepository


class PortfolioNotFoundError(LookupError):
    pass


class PortfolioAlreadyExistsError(ValueError):
    pass


@dataclass(frozen=True)
class CreatePortfolio:
    portfolio_id: str
    name: str
    owner: str


@dataclass(frozen=True)
class UpdatePortfolio:
    name: str | None = None
    owner: str | None = None
    status: PortfolioStatus | None = None


class PortfolioService:
    def __init__(
        self,
        repository: PortfolioRepository | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.repository = repository or InMemoryPortfolioRepository()
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def create(self, command: CreatePortfolio) -> Portfolio:
        portfolio_id = self._text(command.portfolio_id, "portfolio_id", 64)
        name = self._text(command.name, "name", 200)
        owner = self._text(command.owner, "owner", 100)
        if self.repository.get(portfolio_id) is not None:
            raise PortfolioAlreadyExistsError(portfolio_id)
        now = self._utc_now()
        return self.repository.create(
            Portfolio(
                portfolio_id=portfolio_id,
                name=name,
                owner=owner,
                status=PortfolioStatus.ACTIVE,
                created_at=now,
                updated_at=now,
            )
        )

    def get(self, portfolio_id: str) -> Portfolio:
        portfolio = self.repository.get(portfolio_id)
        if portfolio is None:
            raise PortfolioNotFoundError(portfolio_id)
        return portfolio

    def update(self, portfolio_id: str, command: UpdatePortfolio) -> Portfolio:
        current = self.get(portfolio_id)
        if command.name is None and command.owner is None and command.status is None:
            raise ValueError("At least one portfolio field must be supplied")
        updated = replace(
            current,
            name=(current.name if command.name is None else self._text(command.name, "name", 200)),
            owner=(
                current.owner if command.owner is None else self._text(command.owner, "owner", 100)
            ),
            status=current.status if command.status is None else command.status,
            updated_at=self._utc_now(),
        )
        return self.repository.replace(updated)

    def list(
        self,
        *,
        status: PortfolioStatus | None = None,
        owner: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Portfolio], int]:
        return self.repository.list(
            status=status,
            owner=owner,
            limit=limit,
            offset=offset,
        )

    def _utc_now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Portfolio clock must return a timezone-aware datetime")
        return value.astimezone(timezone.utc)

    @staticmethod
    def _text(value: str, field: str, maximum: int) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{field} must not be blank")
        if len(normalized) > maximum:
            raise ValueError(f"{field} must be at most {maximum} characters")
        return normalized
