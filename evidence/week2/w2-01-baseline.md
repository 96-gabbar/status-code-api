# W2-01 Baseline Evidence

**Captured:** 6 November 2026
**Branch:** `main`
**HEAD:** `e93330282c8a01bc8e0552e3da98595953c6d5c8`
**Python:** 3.9.6

## Installed baseline packages

```text
fastapi 0.128.8
pydantic 2.13.5
pytest 8.4.2
PyYAML 6.0.3
```

No Week 2 database dependencies were installed during W2-01.

## Pre-change verification

```text
.venv-verify/bin/python -m pytest -q
97 passed in 0.57s

.venv-verify/bin/python scripts/validate_openapi.py
Authored operations: 8
Generated operations: 8
Differences: 0
```

## Worktree state and preservation

The baseline was intentionally captured from a non-clean worktree. W2-01 did not reset, delete, or overwrite these pre-existing changes:

- Modified: `app/api/exceptions.py`, `openapi.yaml`, `requirements.txt`.
- Untracked Week 1 validation work: `scripts/validate_openapi.py`, `tests/test_openapi.py`, and related files under `evidence/`.
- Untracked local artifacts: `.venv-verify/` and `.DS_Store`.
- Untracked Week 2 planning work: `docs/week2/week2-plan.md`.

The Week 1 validation report identifies the intended API/OpenAPI changes. Local virtual environments and operating-system metadata are not treated as source or evidence for Week 2.

## Repository contract inventory

The initial contract tests capture behavior currently required by `ExceptionService`:

- A new repository is empty and returns `None` for an absent ID.
- Public IDs begin at `EXC-10001`, increase sequentially, and are local to each in-memory repository instance.
- Create round-trips every domain field.
- Multiple records remain retrievable.
- Replace persists a complete changed record without creating a duplicate.
- Mutating the list returned by `all()` cannot delete stored records.

The tests deliberately do not define behavior for creating duplicate IDs or replacing missing IDs because the Week 1 service never invokes those cases. Database constraints and explicit error behavior will be defined during W2-02/W2-06 rather than inferred accidentally.

The PostgreSQL implementation will be added to the same parameterized contract-test fixture. PostgreSQL-specific transaction, constraint, filtering, pagination, ordering, and concurrency behavior will remain in integration tests.

## Post-change verification

```text
.venv-verify/bin/python -m pytest tests/repositories/test_exception_repository_contract.py -q
6 passed in 0.02s

.venv-verify/bin/python -m pytest -q
103 passed in 0.56s

.venv-verify/bin/python scripts/validate_openapi.py
Authored operations: 8
Generated operations: 8
Differences: 0
```

W2-01 added six tests and changed no application or dependency code.
