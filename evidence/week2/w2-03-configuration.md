# W2-03 Configuration Evidence

**Completed:** 6 November 2026

## Environment contract

| Variable | Default | Allowed/behavior |
|---|---|---|
| `STATUS_CODE_API_ENVIRONMENT` | `development` | `development`, `test`, `production` |
| `STATUS_CODE_API_REPOSITORY_BACKEND` | `memory` | `memory`, `postgres` |
| `STATUS_CODE_API_DATABASE_URL` or `DATABASE_URL` | Local PostgreSQL URL | Stored as a masked `SecretStr`; prefixed value wins |
| `STATUS_CODE_API_LOG_LEVEL` | `INFO` | Standard levels; input normalized to uppercase |
| `STATUS_CODE_API_SQL_ECHO` | `false` | Strict boolean parsing |

The default repository remains in-memory so the existing unit and contract suites do not require infrastructure. Docker Compose and PostgreSQL integration tests will explicitly select `postgres`.

`.env` and local virtual environments are ignored. `.env.example` contains synthetic local-development values only.

## Verification

```text
.venv-verify/bin/python -m pytest tests/test_config.py -q
8 passed in 0.07s

.venv-verify/bin/python -m pytest -q
113 passed in 0.59s

.venv-verify/bin/python scripts/validate_openapi.py
Authored operations: 8
Generated operations: 8
Differences: 0
```
