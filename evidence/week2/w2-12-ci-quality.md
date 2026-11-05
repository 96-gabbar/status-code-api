# W2-12 CI and Quality Gates

**Implementation date:** 6 November 2026
**Status:** CI execution pending GitHub run

## Gates

- Ruff lint across the repository.
- Ruff formatting check across the repository.
- Mypy checks production `app/` and operational `scripts/` code.
- OpenAPI authored/generated comparison.
- Alembic upgrade, downgrade, and re-upgrade against PostgreSQL.
- Full pytest suite, including PostgreSQL integration tests when `TEST_DATABASE_URL` is configured.

Local quality and regression results are recorded after implementation. GitHub-hosted CI status cannot be represented as passing until the workflow runs in GitHub.

## Local verification

```text
.venv-verify/bin/ruff check .
All checks passed!

.venv-verify/bin/ruff format --check .
87 files already formatted

.venv-verify/bin/mypy app scripts
Success: no issues found in 30 source files

.venv-verify/bin/python scripts/validate_openapi.py
Authored operations: 8
Generated operations: 8
Differences: 0

.venv-verify/bin/python -m pytest -q
144 passed in 1.75s
```

The local run used the Compose PostgreSQL instance, so all five integration tests executed. The remaining gate is the first GitHub-hosted workflow run from a committed branch.
