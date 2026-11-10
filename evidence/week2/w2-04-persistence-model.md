# W2-04 Persistence Model Evidence

**Completed:** 6 November 2026

## Design

- SQLAlchemy persistence records are separate from domain dataclasses and API schemas.
- Enums use varchar columns with named check constraints, following accepted decision C4.
- PostgreSQL `timestamptz` semantics are requested through timezone-aware SQLAlchemy columns.
- Mapping rejects naive datetimes and normalizes aware values to UTC.
- Nullable workflow fields remain nullable; all other domain fields are required.
- Indexes follow the current filter and deterministic ordering paths.
- A numeric database identity is separate from the unique public `EXC-<digits>` identifier. W2-07 will make their relationship concurrency-safe.

## Verification

```text
.venv-verify/bin/python -m pytest tests/db/test_mappers.py -q
5 passed in 2.19s

.venv-verify/bin/python -m pytest -q
118 passed in 0.99s

.venv-verify/bin/python scripts/validate_openapi.py
Authored operations: 8
Generated operations: 8
Differences: 0
```
