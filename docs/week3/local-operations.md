# Week 3 local operations

## Start and inspect

```bash
docker compose up -d --build
docker compose ps --all
docker compose logs --no-color api portfolio-api
```

Expected state: both database and API services are healthy, while both
migration services have exited with code 0.

The Exception API listens on `http://127.0.0.1:8000`; the Portfolio API listens
on `http://127.0.0.1:8001`. PostgreSQL ports are 55432 for Exception and 55433
for Portfolio.

## Contracts and tests

```bash
.venv/bin/python scripts/validate_openapi.py
.venv/bin/python scripts/validate_portfolio_openapi.py

TEST_DATABASE_URL=postgresql+psycopg://status_code_api:status_code_api@127.0.0.1:55432/status_code_api \
TEST_PORTFOLIO_DATABASE_URL=postgresql+psycopg://portfolio_api:portfolio_api@127.0.0.1:55433/portfolio_service \
.venv/bin/python -m pytest tests tests_portfolio exercises test_main.py -q

RUN_E2E=1 .venv/bin/python -m pytest tests_e2e -q
```

## Migration lifecycle

```bash
DATABASE_URL=postgresql+psycopg://status_code_api:status_code_api@127.0.0.1:55432/status_code_api \
.venv/bin/alembic upgrade head

PORTFOLIO_DATABASE_URL=postgresql+psycopg://portfolio_api:portfolio_api@127.0.0.1:55433/portfolio_service \
.venv/bin/alembic -c portfolio_alembic.ini upgrade head
```

Application startup never creates or changes tables. Container health checks
require the exact Exception and Portfolio revisions.

## Restart and shutdown

```bash
docker compose restart portfolio-api api
docker compose down
docker compose up -d
```

Named volumes preserve both databases across `down` and subsequent startup.
Use `docker compose down --volumes` only for an intentional complete local data
reset.

## Dependency outage check

```bash
docker compose stop portfolio-api
docker compose start portfolio-api
```

While Portfolio is stopped, integrated exception creation returns
`503 DEPENDENCY_UNAVAILABLE`. It must not allocate or persist an exception.
