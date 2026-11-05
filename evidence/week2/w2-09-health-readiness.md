# W2-09 Liveness and Readiness

**Implementation date:** 6 November 2026
**Status:** DONE — live PostgreSQL readiness passed

## Behavior

- `GET /health` remains the stable process-liveness contract and does not depend on PostgreSQL.
- `scripts/check_readiness.py` is the operational readiness check used by containers and orchestration.
- Memory mode is immediately ready.
- PostgreSQL mode requires a successful connection and the exact current Alembic revision.
- Connection, initialization, missing migration, and stale migration failures return a non-zero process status without changing the eight-operation OpenAPI contract.

Unit tests cover reachable/current, unreachable, uninitialized, stale, and memory-mode behavior. In Compose, PostgreSQL became healthy, migration revision `20261106_0001` was current, the API health check passed, and `python scripts/check_container_health.py` exited 0 inside the API container.

## Verification

```text
.venv-verify/bin/python -m pytest tests/db/test_readiness.py tests/test_readiness_script.py -q
5 passed

.venv-verify/bin/python scripts/check_readiness.py
ready: memory repository
```
