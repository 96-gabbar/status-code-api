from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session, sessionmaker

from app.api.exceptions import INTERNAL_RESPONSE, router
from app.config import Settings, get_settings
from app.db.session import create_db_engine, create_session_factory
from app.errors.handlers import (
    conflict_handler,
    http_exception_handler,
    internal_handler,
    not_found_handler,
    validation_handler,
)
from app.logging import configure_logging
from app.middleware import log_request
from app.schemas.exception import HealthResponse
from app.services.exception_service import ExceptionNotFoundError, ExceptionService
from app.services.state_machine import InvalidStateTransitionError


def create_app(
    settings: Settings | None = None,
    session_factory: sessionmaker[Session] | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(title="Trade Exception Management API", version="1.0.0")
    app.middleware("http")(log_request)
    app.state.settings = settings
    if settings.repository_backend == "memory":
        app.state.exception_service = ExceptionService()
    else:
        if session_factory is None:
            engine = create_db_engine(settings)
            session_factory = create_session_factory(engine)
            app.state.db_engine = engine
            app.add_event_handler("shutdown", engine.dispose)
        app.state.session_factory = session_factory
    app.include_router(router)
    app.add_exception_handler(RequestValidationError, validation_handler)  # type: ignore[arg-type]
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(ExceptionNotFoundError, not_found_handler)  # type: ignore[arg-type]
    app.add_exception_handler(InvalidStateTransitionError, conflict_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, internal_handler)

    @app.get(
        "/health",
        response_model=HealthResponse,
        responses={500: INTERNAL_RESPONSE},
    )
    def health() -> HealthResponse:
        return HealthResponse(status="healthy", service="trade-exception-service", version="1.0.0")

    return app


app = create_app()
