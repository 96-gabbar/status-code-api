from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_compose_separates_database_migration_and_api_roles() -> None:
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text())
    services = compose["services"]

    assert set(services) == {"db", "migrate", "api"}
    assert services["migrate"]["command"] == ["alembic", "upgrade", "head"]
    assert services["migrate"]["depends_on"]["db"]["condition"] == "service_healthy"
    assert services["api"]["depends_on"]["migrate"]["condition"] == "service_completed_successfully"
    assert services["api"]["healthcheck"]["test"] == [
        "CMD",
        "python",
        "scripts/check_container_health.py",
    ]


def test_compose_selects_postgres_repository() -> None:
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text())
    environment = compose["services"]["api"]["environment"]

    assert environment["STATUS_CODE_API_REPOSITORY_BACKEND"] == "postgres"
    assert environment["DATABASE_URL"].startswith("postgresql+psycopg://")


def test_dockerfile_runs_as_non_root_and_uses_runtime_dependencies() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text()

    assert "COPY requirements-prod.txt" in dockerfile
    assert "USER app" in dockerfile
    assert 'CMD ["uvicorn", "app.main:app"' in dockerfile
