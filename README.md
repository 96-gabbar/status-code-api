# Trade Exception Management API v1

This Week 1 learning service is a layered FastAPI application using synthetic
in-memory data. Data resets when the process restarts.

The tested environment uses **Python 3.9**. The commands below use the
repository-local virtual environment, so they do not depend on a globally
activated Python installation.

## Setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## Run

```bash
.venv/bin/python -m uvicorn app.main:app --reload
```

```bash
curl http://127.0.0.1:8000/health
```

The API supports create, retrieve, filter/list, PATCH, assign, resolve, and
close operations under `/api/v1/exceptions`.

### Example workflow

Create an exception:

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

## Mini-APIs

Run each mini-API from its own directory and use a different port if the
flagship service is already running:

```bash
cd exercises/status-code-api
../../.venv/bin/python -m uvicorn main:app --reload --port 8001

cd ../validation-api
../../.venv/bin/python -m uvicorn main:app --reload --port 8002

cd ../pagination-api
../../.venv/bin/python -m uvicorn main:app --reload --port 8003
```

The mini-API endpoints are:

- `http://127.0.0.1:8001/examples/item`
- `http://127.0.0.1:8002/users`
- `http://127.0.0.1:8003/products?limit=10&offset=20`

Each server also exposes its own `/docs` Swagger UI.
