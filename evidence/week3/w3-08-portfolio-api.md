# W3-08 standalone Portfolio API evidence

Date: 12 November 2026

- FastAPI routes implement create, list, get, update, and liveness.
- Pydantic input validation trims values and rejects empty PATCH, explicit null, unknown fields, bad enum values, and unsupported query parameters.
- Request-scoped PostgreSQL dependencies commit successful requests and roll back failures.
- Exact-revision readiness checks `portfolio_alembic_version` for `20261112_0001`.
- Authored OpenAPI operations: 5.
- Generated OpenAPI operations: 5.
- Authored/generated differences: 0.
- Live Portfolio/API/contract tests: 46 passed.
- Ruff, formatting, and targeted mypy: passed.
