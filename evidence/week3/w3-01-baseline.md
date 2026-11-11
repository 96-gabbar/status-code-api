# W3-01 Baseline Evidence

**Captured:** 12 November 2026
**Branch:** `feature/week3`
**HEAD:** `c4bbf2e971fe4eb5f9d336f4eacc1ac43038aca1`
**Tree:** `8d127da8db0ab8b3df9f14b6652df7da2d1a29a4`

## Baseline identity

The checked-out branch points to the merged Week 2 pull request. Its tree is identical to local `week2-persistence` at `f469d42`, so the differing commit graph does not represent a code difference.

The Week 2 hosted evidence remains:

- GitHub Actions run `42120018392` passed for the implementation commit.
- GitHub Actions run `42120681482` passed for the final branch tip.

## Local verification

```text
.venv-verify/bin/python -m pytest -q
139 passed, 5 skipped in 1.69s

TEST_DATABASE_URL=postgresql+psycopg://...@127.0.0.1:55432/status_code_api \
  .venv-verify/bin/python -m pytest -q
144 passed in 2.03s

.venv-verify/bin/ruff check .
All checks passed!

.venv-verify/bin/ruff format --check .
88 files already formatted

.venv-verify/bin/mypy app scripts
Success: no issues found in 30 source files

.venv-verify/bin/python scripts/validate_openapi.py
Authored operations: 8
Generated operations: 8
Differences: 0
```

The first test run confirms the infrastructure-free path and intentional PostgreSQL skips. The second run uses the canonical Compose PostgreSQL service and executes all five integration tests.

## Environment

- Python 3.9.6
- Docker CLI 29.9.3
- Docker Compose 5.7.0
- PostgreSQL 16 Alpine through the existing Compose stack

W3-01 is complete. Week 3 begins from a clean, live-verified Week 2 code baseline plus the uncommitted Week 3 planning files.
