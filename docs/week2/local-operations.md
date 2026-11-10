# Week 2 Local Operations

## Docker Compose path

Docker Compose is the canonical local PostgreSQL workflow:

```bash
docker compose up --build
```

Compose waits for PostgreSQL, runs `alembic upgrade head` as a one-shot service, and starts the API only after migration succeeds.
The API is available at `127.0.0.1:8000`; PostgreSQL is bound to `127.0.0.1:55432` for host-side integration tests.

Verify liveness and readiness:

```bash
curl http://127.0.0.1:8000/health
docker compose exec api python scripts/check_container_health.py
docker compose ps
```

Stop the services while retaining local data:

```bash
docker compose down
```

`docker compose down -v` also deletes the named PostgreSQL volume and all local service data. Use it only when an empty local database is intended.

## External PostgreSQL path

The API also accepts any PostgreSQL instance reachable through a Psycopg SQLAlchemy URL:

```bash
export STATUS_CODE_API_REPOSITORY_BACKEND=postgres
export DATABASE_URL='postgresql+psycopg://user:password@host:5432/database'
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload
```

The API does not run migrations automatically. Check dependency readiness separately:

```bash
.venv/bin/python scripts/check_readiness.py
```

## In-memory development path

With no configuration overrides, the application retains its Week 1 in-memory behavior:

```bash
.venv/bin/uvicorn app.main:app --reload
```

This mode is useful for API/domain work and resets on process restart.

## Migrations

```bash
.venv/bin/alembic current
.venv/bin/alembic upgrade head
.venv/bin/alembic downgrade base
```

Downgrade removes the Week 2 table and its data. Use it only against a disposable database or as an intentional migration test.

Generate reviewable PostgreSQL SQL without connecting:

```bash
.venv/bin/alembic upgrade head --sql
.venv/bin/alembic downgrade head:base --sql
```

## Tests and quality gates

Fast tests run without PostgreSQL; integration tests skip explicitly:

```bash
.venv/bin/python -m pytest -q
```

Run the live integration tests against a migrated, disposable database:

```bash
export TEST_DATABASE_URL='postgresql+psycopg://user:password@host:5432/test_database'
.venv/bin/alembic upgrade head
.venv/bin/python -m pytest tests/integration -q
```

With the canonical Compose stack running, use:

```bash
export TEST_DATABASE_URL='postgresql+psycopg://status_code_api:status_code_api@127.0.0.1:55432/status_code_api'
.venv/bin/python -m pytest tests/integration -q
```

Run the local CI-equivalent gates:

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy app scripts
.venv/bin/python scripts/validate_openapi.py
.venv/bin/python -m pytest -q
```

## Troubleshooting

- `not ready: PostgreSQL is unavailable or uninitialized`: verify the URL, server, database, and credentials, then run the migration.
- Revision mismatch: run `alembic current` and `alembic upgrade head` using the same `DATABASE_URL` as the API.
- API starts but PostgreSQL operations fail: confirm `STATUS_CODE_API_REPOSITORY_BACKEND=postgres`; the default is `memory`.
- Duplicate or stale local state: inspect `docker compose ps` and the named volume before deciding whether to remove it.
- Never paste production credentials into logs, evidence files, commands committed to the repository, or `.env.example`.
