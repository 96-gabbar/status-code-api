# Trade Exception Management API v1

This Week 1 learning service is a layered FastAPI application using synthetic
in-memory data. Data resets when the process restarts.

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

## Tests

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest --junitxml=evidence/test-results.xml
```

The status-code, validation, and pagination mini-APIs are independently
runnable under `exercises/`.
