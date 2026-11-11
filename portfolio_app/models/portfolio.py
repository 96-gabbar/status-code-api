from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class PortfolioStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


@dataclass(frozen=True)
class Portfolio:
    portfolio_id: str
    name: str
    owner: str
    status: PortfolioStatus
    created_at: datetime
    updated_at: datetime
