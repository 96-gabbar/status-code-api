# W2-02 Repository Boundary Evidence

**Completed:** 6 November 2026

## Change

`ExceptionRepository` is now a structural `Protocol` containing only the five storage operations required by `ExceptionService`. The former dictionary-backed implementation moved to `InMemoryExceptionRepository`.

`ExceptionService` accepts the protocol and defaults to a new in-memory instance when no repository is injected. The explicit `is not None` selection avoids replacing valid repository objects based on their truthiness.

The routes and service contain no SQLAlchemy imports. No database dependency was added in W2-02.

## Boundary checks

- The parameterized repository contract suite now runs against the named in-memory implementation and is ready to accept PostgreSQL fixtures later.
- Service tests verify that an injected repository receives created records.
- Service tests verify that default service instances receive isolated in-memory repositories.
- The public HTTP and OpenAPI contracts are unchanged.

## Verification

```text
.venv-verify/bin/python -m pytest tests/repositories tests/services -q
8 passed in 0.08s

.venv-verify/bin/python -m pytest -q
105 passed in 0.62s

.venv-verify/bin/python scripts/validate_openapi.py
Authored operations: 8
Generated operations: 8
Differences: 0

rg -n 'sqlalchemy' app/services app/api
No matches
```
