from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session, sessionmaker

from app.api.exceptions import INTERNAL_RESPONSE, router
from app.clients.portfolio import HttpPortfolioClient
from app.config import Settings, get_settings
from app.db.session import create_db_engine, create_session_factory
from app.errors.handlers import (
    conflict_handler,
    dependency_unavailable_handler,
    http_exception_handler,
    inactive_portfolio_handler,
    internal_handler,
    invalid_portfolio_handler,
    not_found_handler,
    validation_handler,
)
from app.logging import configure_logging
from app.middleware import log_request
from app.schemas.exception import HealthResponse
from app.services.exception_service import ExceptionNotFoundError, ExceptionService
from app.services.portfolio_gateway import (
    PortfolioDependencyUnavailableError,
    PortfolioGateway,
    PortfolioInactiveError,
    PortfolioMissingError,
)
from app.services.state_machine import InvalidStateTransitionError


def create_app(
    settings: Settings | None = None,
    session_factory: sessionmaker[Session] | None = None,
    portfolio_gateway: PortfolioGateway | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(title="Trade Exception Management API", version="1.0.0")
    app.middleware("http")(log_request)
    app.state.settings = settings
    if portfolio_gateway is None and settings.portfolio_validation_enabled:
        portfolio_client = HttpPortfolioClient(
            settings.portfolio_service_url,
            connect_timeout_seconds=settings.portfolio_connect_timeout_seconds,
            read_timeout_seconds=settings.portfolio_read_timeout_seconds,
            retry_count=settings.portfolio_retry_count,
        )
        portfolio_gateway = portfolio_client
        app.add_event_handler("shutdown", portfolio_client.close)
    app.state.portfolio_gateway = portfolio_gateway
    if settings.repository_backend == "memory":
        app.state.exception_service = ExceptionService(
            portfolio_gateway=portfolio_gateway,
            portfolio_validation_enabled=settings.portfolio_validation_enabled,
        )
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
    app.add_exception_handler(PortfolioMissingError, invalid_portfolio_handler)  # type: ignore[arg-type]
    app.add_exception_handler(PortfolioInactiveError, inactive_portfolio_handler)  # type: ignore[arg-type]
    app.add_exception_handler(
        PortfolioDependencyUnavailableError,
        dependency_unavailable_handler,  # type: ignore[arg-type]
    )
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
