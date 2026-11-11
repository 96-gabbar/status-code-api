from __future__ import annotations

import json
import logging
from collections.abc import Callable
from io import StringIO

import httpx
import pytest

from app.clients.portfolio import HttpPortfolioClient
from app.logging import LOGGER_NAME, JsonFormatter
from app.services.portfolio_gateway import (
    PortfolioDependencyUnavailableError,
    PortfolioMissingError,
    PortfolioState,
)


def client_for(handler: Callable[[httpx.Request], httpx.Response]) -> HttpPortfolioClient:
    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url="http://portfolio.test")
    return HttpPortfolioClient("http://portfolio.test", client=http_client)


@pytest.mark.parametrize("status", ["ACTIVE", "INACTIVE"])
def test_success_returns_typed_snapshot_and_propagates_request_id(status: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Request-ID"] == "request-123"
        return httpx.Response(200, json={"portfolio_id": "PORT-201", "status": status})

    snapshot = client_for(handler).get_portfolio("PORT-201", request_id="request-123")

    assert snapshot.portfolio_id == "PORT-201"
    assert snapshot.status is PortfolioState(status)


def test_missing_portfolio_is_not_retried() -> None:
    requests = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        return httpx.Response(404)

    with pytest.raises(PortfolioMissingError):
        client_for(handler).get_portfolio("PORT-404")
    assert requests == 1


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, content=b"not-json"),
        httpx.Response(200, json={"portfolio_id": "PORT-201", "status": "ARCHIVED"}),
        httpx.Response(200, json={"portfolio_id": "PORT-OTHER", "status": "ACTIVE"}),
        httpx.Response(422),
    ],
)
def test_malformed_or_unexpected_response_maps_to_dependency_unavailable(
    response: httpx.Response,
) -> None:
    with pytest.raises(PortfolioDependencyUnavailableError):
        client_for(lambda _: response).get_portfolio("PORT-201")


def test_timeout_is_retried_once_then_succeeds() -> None:
    requests = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        if requests == 1:
            raise httpx.ReadTimeout("slow", request=request)
        return httpx.Response(200, json={"portfolio_id": "PORT-201", "status": "ACTIVE"})

    snapshot = client_for(handler).get_portfolio("PORT-201")

    assert snapshot.status is PortfolioState.ACTIVE
    assert requests == 2


def test_connection_failure_is_bounded_to_two_attempts() -> None:
    requests = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        raise httpx.ConnectError("offline", request=request)

    with pytest.raises(PortfolioDependencyUnavailableError):
        client_for(handler).get_portfolio("PORT-201")
    assert requests == 2


def test_5xx_is_retried_once_and_4xx_is_not_retried() -> None:
    status_codes = iter([503, 200])
    requests = 0

    def retry_handler(_: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        status = next(status_codes)
        body = {"portfolio_id": "PORT-201", "status": "ACTIVE"} if status == 200 else None
        return httpx.Response(status, json=body)

    assert client_for(retry_handler).get_portfolio("PORT-201").status is PortfolioState.ACTIVE
    assert requests == 2

    requests = 0

    def no_retry_handler(_: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        return httpx.Response(409)

    with pytest.raises(PortfolioDependencyUnavailableError):
        client_for(no_retry_handler).get_portfolio("PORT-201")
    assert requests == 1


def test_dependency_log_contains_only_safe_outcome_fields() -> None:
    output = StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger(LOGGER_NAME)
    logger.addHandler(handler)
    try:
        client_for(
            lambda _: httpx.Response(
                200,
                json={"portfolio_id": "PORT-201", "status": "ACTIVE"},
            )
        ).get_portfolio("PORT-201", request_id="request-123")
    finally:
        logger.removeHandler(handler)

    payload = json.loads(output.getvalue())
    assert payload["event"] == "dependency.completed"
    assert payload["request_id"] == "request-123"
    assert payload["dependency"] == "portfolio-service"
    assert payload["operation"] == "get_portfolio"
    assert payload["outcome"] == "success"
    assert payload["status"] == 200
    assert payload["attempts"] == 1
    assert "PORT-201" not in output.getvalue()
