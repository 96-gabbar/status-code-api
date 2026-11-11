from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session, sessionmaker

from app.logging import configure_logging
from app.middleware import log_request
from portfolio_app.api import INTERNAL_RESPONSE, router
from portfolio_app.config import PortfolioSettings, get_portfolio_settings
from portfolio_app.db.session import (
    create_portfolio_db_engine,
    create_portfolio_session_factory,
)
from portfolio_app.errors import (
    conflict_handler,
    http_exception_handler,
    internal_handler,
    not_found_handler,
    validation_handler,
)
from portfolio_app.schemas import HealthResponse
from portfolio_app.services.portfolio_service import (
    PortfolioAlreadyExistsError,
    PortfolioNotFoundError,
    PortfolioService,
)


def create_app(
    settings: PortfolioSettings | None = None,
    session_factory: sessionmaker[Session] | None = None,
) -> FastAPI:
    settings = settings or get_portfolio_settings()
    configure_logging(settings.log_level)
    app = FastAPI(title="Portfolio Service API", version="1.0.0")
    app.middleware("http")(log_request)
    app.state.settings = settings
    if settings.repository_backend == "memory":
        app.state.portfolio_service = PortfolioService()
    else:
        if session_factory is None:
            engine = create_portfolio_db_engine(settings)
            session_factory = create_portfolio_session_factory(engine)
            app.state.db_engine = engine
            app.add_event_handler("shutdown", engine.dispose)
        app.state.session_factory = session_factory

    app.include_router(router)
    app.add_exception_handler(RequestValidationError, validation_handler)  # type: ignore[arg-type]
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(PortfolioNotFoundError, not_found_handler)  # type: ignore[arg-type]
    app.add_exception_handler(PortfolioAlreadyExistsError, conflict_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, internal_handler)

    @app.get(
        "/health",
        response_model=HealthResponse,
        operation_id="getHealth",
        summary="Check process liveness",
        responses={500: INTERNAL_RESPONSE},
    )
    def health() -> HealthResponse:
        return HealthResponse(status="healthy", service="portfolio-service", version="1.0.0")

    return app


app = create_app()
