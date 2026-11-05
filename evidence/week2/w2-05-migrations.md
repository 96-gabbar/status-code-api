# W2-05 Migration Evidence

**Implementation date:** 6 November 2026
**Status:** DONE — live PostgreSQL lifecycle passed

## Implemented

- Alembic reads the masked application database setting at runtime.
- The initial hand-reviewed migration creates the ID sequence, table, constraints, and indexes.
- Downgrade removes indexes, table, and sequence in dependency-safe order.
- Tests verify one linear migration head and the presence of both directions.
- Offline PostgreSQL SQL is generated for upgrade and downgrade without contacting a database.

## Live PostgreSQL result

A separate `status_code_api_migration_test` database completed `upgrade head → downgrade base → upgrade head`, with every Alembic command exiting 0 against PostgreSQL 16. The live run also exposed and fixed migration URL precedence: a programmatically supplied Alembic URL now wins, while the application setting remains the default for CLI use.

## Verification

```text
.venv-verify/bin/python -m pytest tests/db/test_migrations.py tests/db/test_mappers.py -q
7 passed in 0.57s

.venv-verify/bin/alembic upgrade head --sql
Generated PostgreSQL DDL for the version table, sequence, table, 10 named check
constraints, unique public ID, four indexes, and revision insert.

.venv-verify/bin/alembic downgrade head:base --sql
Generated PostgreSQL DDL that drops four indexes, the table, sequence, revision,
and version table in dependency-safe order.
```

Live execution and offline SQL generation now cover both migration directions.
