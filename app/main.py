from __future__ import annotations

from fastapi import FastAPI
from fastapi import HTTPException

from app.api.exceptions import router
from app.errors.handlers import (
    conflict_handler,
    http_exception_handler,
    internal_handler,
    not_found_handler,
    validation_handler,
)
from app.schemas.exception import HealthResponse
from app.services.exception_service import ExceptionNotFoundError, ExceptionService
from app.services.state_machine import InvalidStateTransitionError
from fastapi.exceptions import RequestValidationError


def create_app() -> FastAPI:
    app = FastAPI(title="Trade Exception Management API", version="1.0.0")
    app.state.exception_service = ExceptionService()
    app.include_router(router)
    app.add_exception_handler(RequestValidationError, validation_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(ExceptionNotFoundError, not_found_handler)
    app.add_exception_handler(InvalidStateTransitionError, conflict_handler)
    app.add_exception_handler(Exception, internal_handler)

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status="healthy", service="trade-exception-service", version="1.0.0"
        )

    return app


app = create_app()
