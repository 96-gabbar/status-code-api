from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from portfolio_app.config import PortfolioSettings
from portfolio_app.main import create_app


def postgres_app(engine: Engine):
    settings = PortfolioSettings(
        _env_file=None,
        repository_backend="postgres",
        PORTFOLIO_DATABASE_URL=str(engine.url),
    )
    factory = sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
    )
    return create_app(settings=settings, session_factory=factory)


def test_resource_survives_application_recreation(portfolio_postgres_engine: Engine) -> None:
    first_client = TestClient(postgres_app(portfolio_postgres_engine))
    response = first_client.post(
        "/api/v1/portfolios",
        json={
            "portfolio_id": "PORT-201",
            "name": "Asia Credit Opportunities",
            "owner": "CREDIT-OPS",
        },
    )
    assert response.status_code == 201
    created = response.json()

    restarted_client = TestClient(postgres_app(portfolio_postgres_engine))
    retrieved = restarted_client.get("/api/v1/portfolios/PORT-201")

    assert retrieved.status_code == 200
    assert retrieved.json() == created


def test_rejected_request_does_not_mutate_persisted_state(
    portfolio_postgres_engine: Engine,
) -> None:
    client = TestClient(postgres_app(portfolio_postgres_engine))
    client.post(
        "/api/v1/portfolios",
        json={"portfolio_id": "PORT-201", "name": "Original", "owner": "CREDIT-OPS"},
    )

    rejected = client.patch("/api/v1/portfolios/PORT-201", json={"name": ""})

    assert rejected.status_code == 422
    assert client.get("/api/v1/portfolios/PORT-201").json()["name"] == "Original"
