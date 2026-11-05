# W2-12 CI and Quality Gates

**Implementation date:** 6 November 2026
**Status:** DONE — GitHub Actions passed

## Gates

- Ruff lint across the repository.
- Ruff formatting check across the repository.
- Mypy checks production `app/` and operational `scripts/` code.
- OpenAPI authored/generated comparison.
- Alembic upgrade, downgrade, and re-upgrade against PostgreSQL.
- Full pytest suite, including PostgreSQL integration tests when `TEST_DATABASE_URL` is configured.

Local quality and regression results are recorded after implementation. GitHub Actions run [42120018392](https://github.com/96-gabbar/status-code-api/actions/runs/42120018392) completed successfully for commit `7635a57780a74e0dd7e573cbda5266741cd98687` on `week2-persistence`.

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

The local run used the Compose PostgreSQL instance, so all five integration tests executed. The hosted run independently passed installation, Ruff lint and formatting, mypy, OpenAPI validation, live migration upgrade/downgrade/re-upgrade, and the complete pytest suite using its PostgreSQL 16 service.
