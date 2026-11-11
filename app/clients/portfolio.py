from __future__ import annotations

import logging
from time import perf_counter
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from app.logging import LOGGER_NAME
from app.services.portfolio_gateway import (
    PortfolioDependencyUnavailableError,
    PortfolioMissingError,
    PortfolioSnapshot,
    PortfolioState,
)


class _PortfolioResponse(BaseModel):
    portfolio_id: str
    status: PortfolioState


class HttpPortfolioClient:
    """Typed Portfolio lookup client with one bounded retry for safe GET failures."""

    def __init__(
        self,
        base_url: str,
        *,
        connect_timeout_seconds: float = 0.5,
        read_timeout_seconds: float = 1.0,
        retry_count: int = 1,
        client: httpx.Client | None = None,
    ) -> None:
        if retry_count < 0:
            raise ValueError("retry_count must be non-negative")
        self.retry_count = retry_count
        self._owns_client = client is None
        self.client = client or httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(
                connect=connect_timeout_seconds,
                read=read_timeout_seconds,
                write=read_timeout_seconds,
                pool=connect_timeout_seconds,
            ),
        )

    def get_portfolio(
        self,
        portfolio_id: str,
        *,
        request_id: str | None = None,
    ) -> PortfolioSnapshot:
        headers = {"X-Request-ID": request_id} if request_id else None
        attempts = self.retry_count + 1
        started = perf_counter()
        for attempt in range(attempts):
            try:
                response = self.client.get(
                    f"/api/v1/portfolios/{portfolio_id}",
                    headers=headers,
                )
            except (httpx.TimeoutException, httpx.NetworkError) as error:
                if attempt + 1 < attempts:
                    continue
                outcome = (
                    "timeout" if isinstance(error, httpx.TimeoutException) else "connection_error"
                )
                self._log(outcome, started, request_id, None, attempt + 1)
                raise PortfolioDependencyUnavailableError(
                    "Portfolio Service is unavailable"
                ) from error

            if response.status_code == 404:
                self._log("not_found", started, request_id, 404, attempt + 1)
                raise PortfolioMissingError(portfolio_id)
            if response.status_code >= 500:
                if attempt + 1 < attempts:
                    continue
                self._log("server_error", started, request_id, response.status_code, attempt + 1)
                raise PortfolioDependencyUnavailableError("Portfolio Service is unavailable")
            if response.status_code != 200:
                self._log(
                    "unexpected_status",
                    started,
                    request_id,
                    response.status_code,
                    attempt + 1,
                )
                raise PortfolioDependencyUnavailableError(
                    f"Unexpected Portfolio Service status {response.status_code}"
                )
            try:
                snapshot = self._parse_response(response, portfolio_id)
            except PortfolioDependencyUnavailableError:
                self._log("invalid_response", started, request_id, 200, attempt + 1)
                raise
            self._log("success", started, request_id, 200, attempt + 1)
            return snapshot

        raise AssertionError("unreachable")

    @staticmethod
    def _parse_response(response: httpx.Response, portfolio_id: str) -> PortfolioSnapshot:
        try:
            body: Any = response.json()
            parsed = _PortfolioResponse.model_validate(body)
        except (ValueError, ValidationError) as error:
            raise PortfolioDependencyUnavailableError(
                "Portfolio Service returned an invalid response"
            ) from error
        if parsed.portfolio_id != portfolio_id:
            raise PortfolioDependencyUnavailableError(
                "Portfolio Service returned a mismatched portfolio"
            )
        return PortfolioSnapshot(portfolio_id=parsed.portfolio_id, status=parsed.status)

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    @staticmethod
    def _log(
        outcome: str,
        started: float,
        request_id: str | None,
        status: int | None,
        attempts: int,
    ) -> None:
        logging.getLogger(LOGGER_NAME).info(
            "dependency.completed",
            extra={
                "request_id": request_id,
                "dependency": "portfolio-service",
                "operation": "get_portfolio",
                "outcome": outcome,
                "status": status,
                "attempts": attempts,
                "duration_ms": round((perf_counter() - started) * 1000, 3),
            },
        )
