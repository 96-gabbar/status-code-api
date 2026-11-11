from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class PortfolioGatewayError(RuntimeError):
    pass


class PortfolioMissingError(PortfolioGatewayError):
    pass


class PortfolioDependencyUnavailableError(PortfolioGatewayError):
    pass


class PortfolioInactiveError(PortfolioGatewayError):
    pass


class PortfolioState(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


@dataclass(frozen=True)
class PortfolioSnapshot:
    portfolio_id: str
    status: PortfolioState


class PortfolioGateway(Protocol):
    def get_portfolio(
        self,
        portfolio_id: str,
        *,
        request_id: str | None = None,
    ) -> PortfolioSnapshot: ...
