from __future__ import annotations

from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.portfolio_gateway import (
    PortfolioDependencyUnavailableError,
    PortfolioGatewayError,
    PortfolioMissingError,
    PortfolioSnapshot,
    PortfolioState,
)


@dataclass
class StubGateway:
    result: PortfolioSnapshot | PortfolioGatewayError
    request_id: str | None = None

    def get_portfolio(
        self,
        portfolio_id: str,
        *,
        request_id: str | None = None,
    ) -> PortfolioSnapshot:
        self.request_id = request_id
        if isinstance(self.result, PortfolioGatewayError):
            raise self.result
        return self.result


def client_for(result: PortfolioSnapshot | PortfolioGatewayError) -> tuple[TestClient, StubGateway]:
    gateway = StubGateway(result)
    settings = Settings(
        _env_file=None,
        repository_backend="memory",
        portfolio_validation_enabled=True,
    )
    return TestClient(create_app(settings, portfolio_gateway=gateway)), gateway


def payload() -> dict[str, str]:
    return {
        "portfolio_id": "PORT-201",
        "transaction_id": "TXN-918273",
        "type": "SETTLEMENT_MISMATCH",
        "severity": "HIGH",
        "description": "Expected settlement amount differs",
    }


def test_active_portfolio_allows_create_and_propagates_request_id() -> None:
    client, gateway = client_for(PortfolioSnapshot("PORT-201", PortfolioState.ACTIVE))

    response = client.post(
        "/api/v1/exceptions",
        json=payload(),
        headers={"X-Request-ID": "request-123"},
    )

    assert response.status_code == 201
    assert gateway.request_id == "request-123"


@pytest.mark.parametrize(
    ("result", "status", "code"),
    [
        (PortfolioMissingError("PORT-201"), 422, "INVALID_PORTFOLIO"),
        (PortfolioSnapshot("PORT-201", PortfolioState.INACTIVE), 422, "PORTFOLIO_INACTIVE"),
        (
            PortfolioDependencyUnavailableError("offline"),
            503,
            "DEPENDENCY_UNAVAILABLE",
        ),
    ],
)
def test_portfolio_rejection_has_stable_error_and_does_not_persist(
    result: PortfolioSnapshot | PortfolioGatewayError,
    status: int,
    code: str,
) -> None:
    client, _ = client_for(result)

    response = client.post("/api/v1/exceptions", json=payload())

    assert response.status_code == status
    assert response.json()["error"]["code"] == code
    assert client.get("/api/v1/exceptions").json()["total"] == 0
