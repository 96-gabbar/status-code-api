# Trade Exception Management API v1

This repository contains two layered FastAPI services: Trade Exception
Management and Portfolio. Each service owns its API, domain, persistence,
migrations, database, and runtime lifecycle.

The tested environment uses **Python 3.9**. The commands below use the
repository-local virtual environment, so they do not depend on a globally
activated Python installation.

Week 2 adds an optional PostgreSQL repository, versioned Alembic migrations,
Docker packaging, structured request logs, readiness checks, and CI while
preserving the Week 1 HTTP contract. In-memory storage remains the default for
fast local development.

Week 3 adds the separately owned Portfolio Service and validates portfolio
status over HTTP before integrated exception creation. The compatibility flag
remains off for standalone Exception development and is enabled by Compose.

## Setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## Run

```bash
.venv/bin/python -m uvicorn app.main:app --reload
.venv/bin/python -m uvicorn portfolio_app.main:app --reload --port 8001
```

```bash
curl http://127.0.0.1:8000/health
```

The API supports create, retrieve, filter/list, PATCH, assign, resolve, and
close operations under `/api/v1/exceptions`.

### Run with PostgreSQL

The canonical PostgreSQL workflow uses Docker Compose:

```bash
docker compose up --build
```

The stack starts two PostgreSQL containers, runs each service's migrations in
one-shot jobs, starts the Portfolio API, and then starts the Exception API with
portfolio validation enabled. See `docs/week3/local-operations.md` for
migration, readiness, persistence, reset, and troubleshooting commands.

### Example workflow

Create the portfolio owned by the Portfolio Service:

```bash
curl -i -X POST http://127.0.0.1:8001/api/v1/portfolios \
  -H 'Content-Type: application/json' \
  -d '{
    "portfolio_id": "PORT-201",
    "name": "Asia Credit Opportunities",
    "owner": "CREDIT-OPS"
  }'
```

Then create an exception referencing that active portfolio:

```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/exceptions \
  -H 'Content-Type: application/json' \
  -d '{
    "portfolio_id": "PORT-201",
    "transaction_id": "TXN-918273",
    "type": "SETTLEMENT_MISMATCH",
    "severity": "HIGH",
    "description": "Expected settlement amount differs from received amount"
  }'
```

Use the returned `exception_id` in the remaining workflow calls:

```bash
curl http://127.0.0.1:8000/api/v1/exceptions/EXC-10001
curl 'http://127.0.0.1:8000/api/v1/exceptions?status=OPEN&limit=20&offset=0'

curl -i -X PATCH http://127.0.0.1:8000/api/v1/exceptions/EXC-10001 \
  -H 'Content-Type: application/json' \
  -d '{"severity":"CRITICAL","description":"Updated investigation information"}'

curl -i -X POST http://127.0.0.1:8000/api/v1/exceptions/EXC-10001/assign \
  -H 'Content-Type: application/json' \
  -d '{"assignee":"ops-user-123"}'

curl -i -X POST http://127.0.0.1:8000/api/v1/exceptions/EXC-10001/resolve \
  -H 'Content-Type: application/json' \
  -d '{"resolution_code":"REFERENCE_DATA_CORRECTED","resolution_notes":"Mapping corrected"}'

curl -i -X POST http://127.0.0.1:8000/api/v1/exceptions/EXC-10001/close
```

## Tests

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest --junitxml=evidence/test-results.xml
```

PostgreSQL integration tests run when `TEST_DATABASE_URL` and
`TEST_PORTFOLIO_DATABASE_URL` point to migrated disposable databases;
otherwise their respective suites are explicitly skipped.

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy app portfolio_app scripts
.venv/bin/python scripts/validate_openapi.py
.venv/bin/python scripts/validate_portfolio_openapi.py

RUN_E2E=1 .venv/bin/python -m pytest tests_e2e -q
```

## Mini-APIs

Run each mini-API from its own directory and use a different port if the
flagship service is already running:

```bash
cd /path/to/status-code-api
.venv/bin/python -m uvicorn main:app --reload --port 8002

cd exercises/validation-api
../../.venv/bin/python -m uvicorn main:app --reload --port 8003

cd ../pagination-api
../../.venv/bin/python -m uvicorn main:app --reload --port 8004
```

The mini-API endpoints are:

- `http://127.0.0.1:8002/examples/item`
- `http://127.0.0.1:8003/users`
- `http://127.0.0.1:8004/products?limit=10&offset=20`

Each server also exposes its own `/docs` Swagger UI.
