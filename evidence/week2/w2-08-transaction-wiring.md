# W2-08 Session and Transaction Wiring

**Implementation date:** 6 November 2026
**Status:** DONE — live PostgreSQL API integration passed

## Implemented

- Application settings select memory or PostgreSQL persistence at startup.
- PostgreSQL engines use pre-ping and create non-expiring, non-autoflush sessions.
- One session and repository are created per HTTP request.
- Successful requests commit; exceptions roll back; every session closes.
- Repositories flush but never commit, keeping transaction ownership at the request boundary.
- In-memory mode retains one isolated service per application and keeps the existing fast tests infrastructure-free.

## Live PostgreSQL result

The API integration tests verified commit-on-success, rollback after an uncommitted create, persistence across application recreation, and preservation of the existing assignment after a conflicting workflow request. A separately created record also remained available after restarting the API container.

## Verification

```text
.venv-verify/bin/python -m pytest tests/test_dependencies.py tests/test_app_factory.py tests/test_flagship_api.py -q
49 passed in 0.81s

.venv-verify/bin/python -m pytest -q
128 passed in 1.34s

.venv-verify/bin/python scripts/validate_openapi.py
Authored operations: 8
Generated operations: 8
Differences: 0

rg -n 'sqlalchemy' app/services app/api
No matches
```
