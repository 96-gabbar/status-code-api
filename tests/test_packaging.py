from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_compose_separates_database_migration_and_api_roles() -> None:
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text())
    services = compose["services"]

    assert set(services) == {
        "db",
        "migrate",
        "api",
        "portfolio-db",
        "portfolio-migrate",
        "portfolio-api",
    }
    assert services["migrate"]["command"] == ["alembic", "upgrade", "head"]
    assert services["migrate"]["depends_on"]["db"]["condition"] == "service_healthy"
    assert services["api"]["depends_on"]["migrate"]["condition"] == "service_completed_successfully"
    assert services["api"]["depends_on"]["portfolio-api"]["condition"] == "service_healthy"
    assert services["api"]["healthcheck"]["test"] == [
        "CMD",
        "python",
        "scripts/check_container_health.py",
    ]
    assert services["portfolio-migrate"]["command"] == [
        "alembic",
        "-c",
        "portfolio_alembic.ini",
        "upgrade",
        "head",
    ]
    assert (
        services["portfolio-migrate"]["depends_on"]["portfolio-db"]["condition"]
        == "service_healthy"
    )
    assert (
        services["portfolio-api"]["depends_on"]["portfolio-migrate"]["condition"]
        == "service_completed_successfully"
    )
    assert services["portfolio-api"]["healthcheck"]["test"] == [
        "CMD",
        "python",
        "scripts/check_portfolio_container_health.py",
    ]


def test_compose_selects_postgres_repository() -> None:
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text())
    environment = compose["services"]["api"]["environment"]

    assert environment["STATUS_CODE_API_REPOSITORY_BACKEND"] == "postgres"
    assert environment["DATABASE_URL"].startswith("postgresql+psycopg://")
    assert environment["STATUS_CODE_API_PORTFOLIO_VALIDATION_ENABLED"] == "true"


def test_compose_uses_separate_database_ownership_and_volumes() -> None:
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text())
    services = compose["services"]

    exception_url = services["api"]["environment"]["DATABASE_URL"]
    portfolio_url = services["portfolio-api"]["environment"]["PORTFOLIO_DATABASE_URL"]
    assert "@db:" in exception_url
    assert "@portfolio-db:" in portfolio_url
    assert services["db"]["volumes"] != services["portfolio-db"]["volumes"]
    assert set(compose["volumes"]) == {"postgres-data", "portfolio-postgres-data"}


def test_dockerfile_runs_as_non_root_and_uses_runtime_dependencies() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text()

    assert "COPY requirements-prod.txt" in dockerfile
    assert "USER app" in dockerfile
    assert 'CMD ["uvicorn", "app.main:app"' in dockerfile
    assert "COPY --chown=app:app portfolio_alembic" in dockerfile
    assert "COPY --chown=app:app portfolio_app" in dockerfile
