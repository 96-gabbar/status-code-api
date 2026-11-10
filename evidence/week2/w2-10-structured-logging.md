# W2-10 Structured Logging Evidence

**Completed:** 6 November 2026

## Behavior

- Application request logs are compact JSON written to stdout.
- Every request event includes UTC timestamp, level, event, request ID, method, path, status, and duration in milliseconds.
- A valid incoming `X-Request-ID` is preserved and returned; missing or unsafe values are replaced with a UUID.
- Logs intentionally exclude query strings, request/response bodies, headers, database URLs, exception text, and stack traces.
- Log level is controlled by validated application settings.

## Verification

```text
.venv-verify/bin/python -m pytest tests/test_logging.py -q
3 passed

.venv-verify/bin/python -m pytest -q
136 passed in 1.41s

.venv-verify/bin/python scripts/validate_openapi.py
Authored operations: 8
Generated operations: 8
Differences: 0
```
