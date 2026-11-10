# W2-06 PostgreSQL Repository Evidence

**Implementation date:** 6 November 2026
**Status:** DONE — live PostgreSQL integration passed

## Implemented

- `SqlAlchemyExceptionRepository` implements the repository protocol using a caller-owned SQLAlchemy session.
- Filtering, count-before-pagination, deterministic ordering, limit, and offset execute in PostgreSQL rather than in the service layer.
- `create` and `replace` flush but do not commit; W2-08 owns transaction boundaries.
- Public ID allocation uses the PostgreSQL sequence created by the initial migration.
- The in-memory implementation now provides the same list behavior, and the service delegates to the repository.
- Contract tests cover list filtering, total, pagination, and stable ordering.

## Live PostgreSQL result

The five-test integration suite passed against PostgreSQL 16. It covers create/get/replace, database-side filters, count-before-pagination, ordering, pagination, sequence IDs, rollback, application recreation, failed workflow integrity, and concurrent sessions.

## Verification

```text
.venv-verify/bin/python -m pytest tests/repositories tests/services -q
11 passed in 0.48s

.venv-verify/bin/python -m pytest -q
123 passed in 1.23s

.venv-verify/bin/python scripts/validate_openapi.py
Authored operations: 8
Generated operations: 8
Differences: 0

rg -n 'sqlalchemy' app/services app/api
No matches
```

```text
TEST_DATABASE_URL=postgresql+psycopg://...@127.0.0.1:55432/status_code_api pytest tests/integration -q
5 passed in 0.84s
```
