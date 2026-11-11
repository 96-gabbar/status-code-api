from __future__ import annotations

import os
from uuid import uuid4

import httpx
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_E2E") != "1",
    reason="RUN_E2E=1 is required for the running Compose stack",
)

EXCEPTION_URL = os.getenv("EXCEPTION_API_URL", "http://127.0.0.1:8000")
PORTFOLIO_URL = os.getenv("PORTFOLIO_API_URL", "http://127.0.0.1:8001")


def identifier(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12].upper()}"


def create_portfolio(portfolio_id: str, request_id: str) -> dict[str, object]:
    response = httpx.post(
        f"{PORTFOLIO_URL}/api/v1/portfolios",
        json={"portfolio_id": portfolio_id, "name": "E2E Portfolio", "owner": "E2E-OPS"},
        headers={"X-Request-ID": request_id},
        timeout=5,
    )
    assert response.status_code == 201
    assert response.headers["X-Request-ID"] == request_id
    return response.json()


def create_exception(portfolio_id: str, request_id: str) -> httpx.Response:
    return httpx.post(
        f"{EXCEPTION_URL}/api/v1/exceptions",
        json={
            "portfolio_id": portfolio_id,
            "transaction_id": identifier("TXN"),
            "type": "SETTLEMENT_MISMATCH",
            "severity": "HIGH",
            "description": "Cross-service end-to-end validation",
        },
        headers={"X-Request-ID": request_id},
        timeout=5,
    )


def assert_no_exception_for(portfolio_id: str) -> None:
    response = httpx.get(
        f"{EXCEPTION_URL}/api/v1/exceptions",
        params={"portfolio_id": portfolio_id},
        timeout=5,
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_valid_portfolio_allows_exception_and_propagates_request_id() -> None:
    portfolio_id = identifier("PORT")
    request_id = identifier("REQ")
    create_portfolio(portfolio_id, request_id)

    response = create_exception(portfolio_id, request_id)

    assert response.status_code == 201
    assert response.headers["X-Request-ID"] == request_id
    assert response.json()["portfolio_id"] == portfolio_id


def test_unknown_portfolio_is_rejected_without_persistence() -> None:
    portfolio_id = identifier("MISSING")

    response = create_exception(portfolio_id, identifier("REQ"))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_PORTFOLIO"
    assert_no_exception_for(portfolio_id)


def test_inactive_portfolio_is_rejected_without_persistence() -> None:
    portfolio_id = identifier("INACTIVE")
    request_id = identifier("REQ")
    create_portfolio(portfolio_id, request_id)
    update = httpx.patch(
        f"{PORTFOLIO_URL}/api/v1/portfolios/{portfolio_id}",
        json={"status": "INACTIVE"},
        timeout=5,
    )
    assert update.status_code == 200

    response = create_exception(portfolio_id, request_id)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "PORTFOLIO_INACTIVE"
    assert_no_exception_for(portfolio_id)
