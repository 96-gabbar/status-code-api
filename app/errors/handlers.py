from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.services.exception_service import ExceptionNotFoundError
from app.services.portfolio_gateway import (
    PortfolioDependencyUnavailableError,
    PortfolioInactiveError,
    PortfolioMissingError,
)
from app.services.state_machine import InvalidStateTransitionError


def error_body(
    code: str, message: str, details: list[dict[str, str]] | None = None
) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if details:
        error["details"] = details
    return {"error": error}


async def validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    details = []
    for error in exc.errors():
        location = error.get("loc", ())
        field = ".".join(str(value) for value in location)
        details.append({"field": field, "message": str(error.get("msg", "Invalid value"))})
    return JSONResponse(
        status_code=422,
        content=error_body("VALIDATION_ERROR", "Request validation failed", details),
    )


async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    if exc.status_code == 422:
        detail: Any = exc.detail
        if isinstance(detail, dict):
            field = str(detail.get("field", "request"))
            message = str(detail.get("message", "Invalid value"))
        else:
            field = "request"
            message = str(detail)
        return JSONResponse(
            status_code=422,
            content=error_body(
                "VALIDATION_ERROR",
                "Request validation failed",
                [{"field": field, "message": message}],
            ),
        )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body("HTTP_ERROR", str(exc.detail)),
    )


async def not_found_handler(_: Request, exc: ExceptionNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content=error_body("EXCEPTION_NOT_FOUND", f"Exception {exc.args[0]} does not exist"),
    )


async def conflict_handler(_: Request, exc: InvalidStateTransitionError) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content=error_body("INVALID_STATE_TRANSITION", str(exc)),
    )


async def invalid_portfolio_handler(_: Request, exc: PortfolioMissingError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_body("INVALID_PORTFOLIO", f"Portfolio {exc.args[0]} does not exist"),
    )


async def inactive_portfolio_handler(_: Request, exc: PortfolioInactiveError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_body("PORTFOLIO_INACTIVE", f"Portfolio {exc.args[0]} is inactive"),
    )


async def dependency_unavailable_handler(
    _: Request,
    __: PortfolioDependencyUnavailableError,
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content=error_body("DEPENDENCY_UNAVAILABLE", "Portfolio Service is unavailable"),
    )


async def internal_handler(_: Request, __: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=error_body("INTERNAL_ERROR", "An unexpected error occurred"),
    )
