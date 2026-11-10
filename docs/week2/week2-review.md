# Week 2 Review

**Review date:** 6 November 2026
**Baseline commit:** `e93330282c8a01bc8e0552e3da98595953c6d5c8` with preserved uncommitted Week 1 work
**Python:** 3.9.6
**Status:** COMPLETE — all mandatory local and hosted gates passed

## Delivered

- Environment-driven, secret-safe configuration.
- Repository protocol with in-memory and SQLAlchemy implementations.
- Separate SQLAlchemy persistence model and domain mapping.
- Initial reversible Alembic migration with named constraints, indexes, and public-ID sequence.
- Database-side filtering, counting, ordering, and pagination.
- Request-scoped sessions with commit, rollback, and close ownership.
- Operational readiness checking without changing the eight-operation OpenAPI contract.
- Structured JSON request logging and request IDs.
- Non-root Docker image, PostgreSQL/migration/API Compose topology, and container health check.
- PostgreSQL integration tests for repository behavior, concurrent IDs, rollback, restart persistence, and failed-workflow integrity.
- GitHub Actions pipeline for quality, migrations, OpenAPI, and all tests.
- Database design, local operations, decisions, and README updates.

## Local verification

```text
ruff check .
All checks passed!

ruff format --check .
87 files already formatted

mypy app scripts
Success: no issues found in 30 source files

python scripts/validate_openapi.py
Authored operations: 8
Generated operations: 8
Differences: 0

python -m pytest -q
144 passed in 1.75s

python -m pip check
No broken requirements found.
```

Alembic offline mode generated complete PostgreSQL upgrade and downgrade SQL for revision `20261106_0001`. A separate live PostgreSQL 16 database then passed `upgrade head → downgrade base → upgrade head`.

Docker 29.9.3, Docker Compose 5.7.0, and Colima 0.10.3 were installed for local verification. The non-root image built successfully. Compose started PostgreSQL, ran the migration as a one-shot service, and started the API only after migration success. HTTP liveness, exact-revision database readiness, API-container restart persistence, and named-volume persistence across `down`/`up` all passed.

The live run found and fixed two discrepancies:

1. `alembic/env.py` previously overwrote an explicit programmatic migration URL with the default application URL. The Alembic configuration now leaves the URL empty and applies application settings only when no explicit URL is supplied.
2. Alembic's logging setup disabled the application request logger during same-process test runs. It now preserves existing loggers.

GitHub Actions run [42120018392](https://github.com/96-gabbar/status-code-api/actions/runs/42120018392) passed on `week2-persistence` for commit `7635a57`. It independently completed dependency installation, Ruff lint/format, mypy, OpenAPI parity, PostgreSQL migration upgrade/downgrade/re-upgrade, and all tests.

## Tracker outcome

| Item | Result |
|---|---|
| W2-00 clarifications | DONE |
| W2-01 baseline | DONE |
| W2-02 repository boundary | DONE |
| W2-03 configuration | DONE |
| W2-04 model/mapping | DONE |
| W2-05 migration | DONE |
| W2-06 PostgreSQL repository | DONE |
| W2-07 concurrent IDs | DONE |
| W2-08 transaction wiring | DONE |
| W2-09 readiness | DONE |
| W2-10 logging | DONE |
| W2-11 packaging | DONE |
| W2-12 CI | DONE |
| W2-13 documentation | DONE |
| W2-14 final evidence | DONE |

## Scorecard

| Category | Weight | Current evidence | Current score |
|---|---:|---|---:|
| Contract and regression preservation | 20 | 144 tests pass; OpenAPI 0 differences | 20 |
| Persistence correctness | 25 | Live CRUD, filters, pagination, concurrency, rollback, and restart tests pass | 25 |
| Migration quality | 15 | Offline SQL and live upgrade/downgrade/re-upgrade pass | 15 |
| Reproducible packaging | 15 | Non-root image, ordered Compose startup, health, restart, and volume checks pass | 15 |
| Operational foundations | 10 | Configuration, readiness, logging, request IDs, and sanitization pass | 10 |
| CI and documentation | 15 | Local gates, documentation, and GitHub Actions run 42120018392 pass | 15 |
| **Total** | **100** | All mandatory evidence complete | **100** |

Week 2 meets every mandatory definition-of-done item.

## Next milestone

Week 3 begins with the Portfolio Service contract and acceptance criteria, following the accepted C2 scope decision.
