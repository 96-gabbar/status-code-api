from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.main import create_app


def postgres_app(engine: Engine):
    settings = Settings(
        _env_file=None,
        repository_backend="postgres",
        DATABASE_URL=str(engine.url),
    )
    factory = sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
    )
    return create_app(settings=settings, session_factory=factory)


def test_resource_survives_application_recreation(postgres_engine: Engine) -> None:
    first_client = TestClient(postgres_app(postgres_engine))
    response = first_client.post(
        "/api/v1/exceptions",
        json={
            "portfolio_id": "PORT-201",
            "transaction_id": "TXN-918273",
            "type": "SETTLEMENT_MISMATCH",
            "severity": "HIGH",
            "description": "Expected settlement amount differs",
        },
    )
    assert response.status_code == 201
    created = response.json()

    restarted_client = TestClient(postgres_app(postgres_engine))
    retrieved = restarted_client.get(f"/api/v1/exceptions/{created['exception_id']}")

    assert retrieved.status_code == 200
    assert retrieved.json() == created


def test_failed_workflow_request_preserves_persisted_state(
    postgres_engine: Engine,
) -> None:
    client = TestClient(postgres_app(postgres_engine))
    created = client.post(
        "/api/v1/exceptions",
        json={
            "portfolio_id": "PORT-201",
            "transaction_id": "TXN-918273",
            "type": "SETTLEMENT_MISMATCH",
            "severity": "HIGH",
            "description": "Expected settlement amount differs",
        },
    ).json()
    path = f"/api/v1/exceptions/{created['exception_id']}"
    assert client.post(path + "/assign", json={"assignee": "ops"}).status_code == 200

    rejected = client.post(path + "/assign", json={"assignee": "other"})

    assert rejected.status_code == 409
    persisted = client.get(path).json()
    assert persisted["status"] == "INVESTIGATING"
    assert persisted["assigned_to"] == "ops"
