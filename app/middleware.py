from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from re import fullmatch
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response

from app.logging import LOGGER_NAME

REQUEST_ID_PATTERN = r"[A-Za-z0-9._-]{1,128}"


def safe_request_id(value: str | None) -> str:
    if value is not None and fullmatch(REQUEST_ID_PATTERN, value):
        return value
    return str(uuid4())


async def log_request(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = safe_request_id(request.headers.get("X-Request-ID"))
    request.state.request_id = request_id
    started = perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        duration_ms = round((perf_counter() - started) * 1000, 3)
        logging.getLogger(LOGGER_NAME).info(
            "request.completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": status,
                "duration_ms": duration_ms,
            },
        )
