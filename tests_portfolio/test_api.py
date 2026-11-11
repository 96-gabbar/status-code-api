from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from portfolio_app.config import PortfolioSettings
from portfolio_app.main import create_app
from portfolio_app.services.portfolio_service import PortfolioService

app = create_app(PortfolioSettings(_env_file=None, repository_backend="memory"))
client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_service() -> None:
    app.state.portfolio_service = PortfolioService()


def payload(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "portfolio_id": "PORT-201",
        "name": "Asia Credit Opportunities",
        "owner": "CREDIT-OPS",
    }
    value.update(overrides)
    return value


def create(**overrides: object) -> dict[str, object]:
    response = client.post("/api/v1/portfolios", json=payload(**overrides))
    assert response.status_code == 201
    return response.json()


def test_health_contract_and_request_id() -> None:
    response = client.get("/health", headers={"X-Request-ID": "portfolio-request-1"})

    assert response.json() == {
        "status": "healthy",
        "service": "portfolio-service",
        "version": "1.0.0",
    }
    assert response.headers["X-Request-ID"] == "portfolio-request-1"


def test_create_trims_fields_and_returns_location() -> None:
    response = client.post(
        "/api/v1/portfolios",
        json=payload(portfolio_id=" PORT-201 ", name=" Portfolio ", owner=" OPS "),
    )

    assert response.status_code == 201
    assert response.headers["Location"] == "/api/v1/portfolios/PORT-201"
    assert response.json()["portfolio_id"] == "PORT-201"
    assert response.json()["name"] == "Portfolio"
    assert response.json()["owner"] == "OPS"
    assert response.json()["status"] == "ACTIVE"


def test_duplicate_and_missing_have_stable_errors() -> None:
    create()

    duplicate = client.post("/api/v1/portfolios", json=payload())
    missing = client.get("/api/v1/portfolios/PORT-404")

    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "PORTFOLIO_ALREADY_EXISTS"
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "PORTFOLIO_NOT_FOUND"


def test_patch_updates_supplied_fields_and_rejects_empty_or_null() -> None:
    create()

    updated = client.patch(
        "/api/v1/portfolios/PORT-201",
        json={"name": "Renamed", "status": "INACTIVE"},
    )

    assert updated.status_code == 200
    assert updated.json()["name"] == "Renamed"
    assert updated.json()["status"] == "INACTIVE"
    assert client.patch("/api/v1/portfolios/PORT-201", json={}).status_code == 422
    assert client.patch("/api/v1/portfolios/PORT-201", json={"owner": None}).status_code == 422


def test_list_filters_before_pagination_and_rejects_unknown_query() -> None:
    create(portfolio_id="PORT-2", owner="RATES-OPS")
    create(portfolio_id="PORT-1", owner="CREDIT-OPS")
    client.patch("/api/v1/portfolios/PORT-2", json={"status": "INACTIVE"})

    response = client.get(
        "/api/v1/portfolios",
        params={"owner": "RATES-OPS", "status": "INACTIVE", "limit": 1},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["portfolio_id"] == "PORT-2"
    invalid = client.get("/api/v1/portfolios", params={"unknown": "value"})
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"
