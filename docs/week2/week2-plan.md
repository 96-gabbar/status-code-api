# Week 2 Plan: Persistence, Packaging, and Integration Foundations

**Service:** Trade Exception Management API v1
**Status:** Local milestone complete; GitHub CI run pending
**Plan created:** 6 November 2026
**Week 1 baseline:** 8 OpenAPI operations, 97 tests passing, authored/generated OpenAPI differences: 0

> Evolve the existing service from process-local memory to a reproducible PostgreSQL-backed application while preserving its external API contract and domain behavior.

## 1. Outcome

At the end of Week 2, the same API can run locally against PostgreSQL, create its schema through versioned migrations, survive application restarts, emit useful structured logs, and pass unit, contract, persistence, and end-to-end tests in CI.

The repository boundary remains the seam between business logic and storage. HTTP handlers and workflow rules must not depend directly on SQLAlchemy.

## 2. Definition of done

Week 2 is complete only when all mandatory checks pass:

- [x] All 97 Week 1 tests still pass, except for deliberate fixture changes documented in the decision log.
- [x] `scripts/validate_openapi.py` reports 8 authored operations, 8 generated operations, and 0 differences.
- [x] PostgreSQL stores every `TradeException` field without changing the public JSON representation.
- [x] Created and updated exceptions remain available after the API process restarts.
- [x] A fresh database reaches the current schema using `alembic upgrade head`.
- [x] The migration can be downgraded to the empty baseline and upgraded again in an isolated test database.
- [x] Repository integration tests exercise create, get, replace, filtering, ordering, pagination, and ID generation against PostgreSQL.
- [x] Concurrent exception creation cannot produce duplicate IDs.
- [x] Failed workflow operations do not partially modify stored data.
- [x] Local setup is reproducible with documented commands and no manually created tables.
- [x] Docker Compose starts the API and PostgreSQL, applies migrations through an explicit startup step, and passes a health/readiness smoke test.
- [x] Configuration is read from environment variables with safe development defaults and no committed secrets.
- [x] Logs are structured and include timestamp, level, event/message, method, path, status, duration, and a request/correlation identifier.
- [ ] CI runs lint/static checks selected for this week, unit tests, OpenAPI validation, migration checks, and PostgreSQL integration tests.
- [x] `docs/week2/week2-review.md` records commands, versions, test counts, evidence, deviations, and remaining gaps.

## 3. Scope

### Mandatory

1. Define a repository protocol/interface that supports the service without coupling it to one implementation.
2. Retain the in-memory repository for fast unit tests.
3. Add a SQLAlchemy PostgreSQL implementation.
4. Add Alembic configuration and an initial migration.
5. Introduce application configuration and dependency wiring.
6. Move filtering, ordering, counting, and pagination into the PostgreSQL repository while preserving behavior.
7. Add transaction boundaries and safe database-generated identity handling.
8. Add repository and API integration tests against real PostgreSQL.
9. Add Docker packaging and a local Compose workflow.
10. Add structured request/application logging.
11. Add CI and reproducible evidence.
12. Update README and architecture/decision documentation.

### Conditional, pending clarification

- Portfolio Service endpoints and Exception-to-Portfolio integration.
- Authentication or authorization.
- Deployment to a remote environment.
- Production observability backend or log collector.

### Deferred

Kubernetes, Kafka, queues, vector databases, LLM features, RAG, production secrets management, high availability, backups, and load testing are outside Week 2 unless the plan is explicitly revised.

## 4. Contract invariants

The following are protected regression requirements:

- The eight method/path operations and documented response codes stay unchanged.
- Request and response schemas, enum values, field ownership, error envelope, filtering, ordering, and pagination semantics stay unchanged.
- New exceptions still receive public IDs in `EXC-<digits>` form.
- `total` is calculated after filtering and before pagination.
- Workflow remains `OPEN → INVESTIGATING → RESOLVED → CLOSED`.
- Validation occurs before resource lookup, and resource lookup before workflow preconditions.
- All timestamps remain timezone-aware UTC values serialized as RFC 3339 strings.
- Storage failures return the safe public 500 envelope and log diagnostic context without leaking credentials or stack traces to clients.

Any necessary contract change must be proposed in the clarification/decision log before implementation and reflected in `openapi.yaml`, tests, and documentation.

## 5. Target architecture

```text
HTTP routes
    → ExceptionService and state machine
        → ExceptionRepository protocol
            ├── InMemoryExceptionRepository (unit tests)
            └── SqlAlchemyExceptionRepository
                    → SQLAlchemy session / transaction
                        → PostgreSQL

Application configuration
    → engine/session factory
    → FastAPI dependency wiring

Alembic
    → versioned PostgreSQL schema
```

SQLAlchemy persistence models and API/domain models remain separate. Mapping functions translate between them so database concerns do not leak into the public contract or state machine.

## 6. Work breakdown and tracker

Status values: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `DONE`.

| ID | Work item | Status | Depends on | Acceptance evidence |
|---|---|---|---|---|
| W2-00 | Resolve plan clarifications and record decisions | DONE | User answers | Section 11 has no open blocking items |
| W2-01 | Capture clean baseline and test inventory | DONE | W2-00 | `evidence/week2/w2-01-baseline.md`; 103 tests pass; OpenAPI differences: 0 |
| W2-02 | Define repository protocol and adapt in-memory implementation | DONE | W2-01 | `evidence/week2/w2-02-repository-boundary.md`; 105 tests pass; no SQLAlchemy imports in service/routes |
| W2-03 | Define configuration model and environment contract | DONE | W2-00 | `evidence/week2/w2-03-configuration.md`; 8 settings tests; full suite 113 passed |
| W2-04 | Add SQLAlchemy persistence model and mapping | DONE | W2-02, W2-03 | `evidence/week2/w2-04-persistence-model.md`; 5 mapping tests; full suite 118 passed |
| W2-05 | Add Alembic and initial migration | DONE | W2-04 | Live fresh upgrade, downgrade, and re-upgrade pass; see `evidence/week2/w2-05-migrations.md` |
| W2-06 | Implement PostgreSQL repository | DONE | W2-04, W2-05 | Live repository and API integration suite passes; see `evidence/week2/w2-06-postgres-repository.md` |
| W2-07 | Make public ID generation concurrency-safe | DONE | W2-06 | 20 parallel creates produce 20 unique public IDs; see `evidence/week2/w2-07-concurrent-ids.md` |
| W2-08 | Wire DB sessions and transaction boundaries into FastAPI | DONE | W2-03, W2-06 | Live commit, rollback, workflow, and restart-persistence checks pass; see `evidence/week2/w2-08-transaction-wiring.md` |
| W2-09 | Define liveness and readiness behavior | DONE | W2-08 | Container liveness and exact-revision PostgreSQL readiness pass; see `evidence/week2/w2-09-health-readiness.md` |
| W2-10 | Add structured logging and request IDs | DONE | W2-08 | `evidence/week2/w2-10-structured-logging.md`; secret-safe JSON request logging; full suite 136 passed |
| W2-11 | Add Dockerfile and Compose workflow | DONE | W2-05, W2-08, W2-09 | Image build, ordered startup, health, API restart, and volume persistence pass; see `evidence/week2/w2-11-packaging.md` |
| W2-12 | Add CI pipeline | BLOCKED | W2-05–W2-11 | Workflow and local gates complete; fresh GitHub run pending; see `evidence/week2/w2-12-ci-quality.md` |
| W2-13 | Update documentation and decision records | DONE | Continuous | README, database design, operations, decisions, evidence, and review reflect current implementation |
| W2-14 | Run final regression and produce review evidence | BLOCKED | W2-01–W2-13 | All local and live gates pass; only the fresh GitHub-hosted CI run remains; see `docs/week2/week2-review.md` |
| W2-15 | Specify/build Portfolio Service | DEFERRED TO WEEK 3 | Decision C2 | Separate contract and acceptance criteria approved before code |

## 7. Execution sequence

The days are sequencing units rather than calendar promises. Progress is measured by acceptance evidence.

### Day 1 — Baseline, boundaries, and configuration

- Resolve Section 11.
- Record the exact baseline, including the existing uncommitted Week 1 validation work.
- Define repository behavior with a protocol/interface and focused contract tests.
- Rename the concrete in-memory implementation if needed for clarity.
- Define configuration fields, environment naming, validation, and testing overrides.

Exit check: the service still runs fully in memory, all regression tests pass, and storage can be selected without changing route code.

### Day 2 — Relational model and migrations

- Design the `trade_exceptions` table, constraints, indexes, enum representation, and UTC timestamp behavior.
- Add explicit domain/persistence mapping.
- Configure Alembic and create the initial hand-reviewed migration.
- Test upgrade/downgrade/re-upgrade on an isolated database.

Exit check: an empty PostgreSQL instance can be brought to the expected schema solely through migrations.

### Day 3 — PostgreSQL repository

- Implement create, get, replace, list, filtering, counting, ordering, and pagination.
- Design concurrency-safe public ID generation.
- Add repository contract tests that run against both implementations where behavior should be identical.
- Add PostgreSQL-specific integration tests for transactions and constraints.

Exit check: both repository implementations satisfy the same behavioral contract, and concurrent creates generate unique public IDs.

### Day 4 — Application integration and failure behavior

- Wire session lifecycle and repository selection through FastAPI dependencies/app startup.
- Define transaction ownership and rollback behavior.
- Map expected database failures without exposing internals.
- Define liveness versus readiness behavior.
- Run the API integration suite against PostgreSQL, including restart persistence.

Exit check: the API behaves identically against PostgreSQL and retains data after process restart.

### Day 5 — Packaging and operations

- Add a production-oriented Dockerfile with a non-root runtime user.
- Add Compose services, health checks, persistent local volume, and explicit migration execution.
- Add structured logging and request/correlation IDs.
- Document local development, migration, reset, and troubleshooting workflows.

Exit check: a clean machine with Docker can start the stack and execute the documented smoke workflow.

### Day 6 — CI and quality gates

- Add the selected formatter/linter/type checker.
- Configure CI with a PostgreSQL service and migration step.
- Run unit, contract, integration, OpenAPI, migration, and packaging checks.
- Store concise machine-readable test evidence where useful; avoid committing transient environment data.

Exit check: the full pipeline passes from a fresh checkout without local state.

### Day 7 — Review and next-service decision

- Run all final checks and capture actual results.
- Review schema, transaction, logging, and deployment decisions.
- Complete `docs/week2/week2-review.md`.
- If C2 selects Portfolio Service for Week 2 and the core milestone is complete, write its contract before implementation; otherwise move it into the next plan.

Exit check: every mandatory definition-of-done item has evidence or is recorded as an explicit gap.

## 8. Proposed database design

This is a starting proposal to validate during W2-04, not an applied migration.

| Column | Proposed PostgreSQL representation | Constraint/index intent |
|---|---|---|
| `id` | `bigint GENERATED ... AS IDENTITY` | Primary key; source for public numeric suffix |
| `exception_id` | `varchar` | Unique, not null, check matching `^EXC-[0-9]+$` |
| `portfolio_id` | `varchar(64)` | Not null; filter index candidate |
| `transaction_id` | `varchar(64)` | Not null |
| `type` | varchar or native enum | Not null; choice recorded under C4 |
| `severity` | varchar or native enum | Not null; filter index candidate |
| `status` | varchar or native enum | Not null; filter index candidate |
| `description` | `varchar(2000)` or text with check | Not null |
| `assigned_to` | `varchar(100)` | Nullable |
| `created_at` | `timestamptz` | Not null; supports deterministic list ordering |
| `updated_at` | `timestamptz` | Not null |
| `resolution_code` | `varchar(100)` | Nullable |
| `resolution_notes` | `varchar(2000)` or text with check | Nullable |

The database should enforce stable invariants that protect data regardless of caller. Pydantic remains responsible for client-facing validation and error detail. Indexes should follow measured query paths rather than being added indiscriminately.

## 9. Test strategy

| Layer | Primary purpose | Storage |
|---|---|---|
| Domain/state-machine unit tests | Workflow correctness and failure invariants | None |
| Service unit tests | Business orchestration and repository interaction | In-memory/fake |
| Repository contract tests | Identical observable repository behavior | In-memory and PostgreSQL |
| Migration tests | Schema lifecycle and data compatibility | PostgreSQL |
| API integration tests | HTTP → service → transaction → database → response | PostgreSQL |
| OpenAPI comparison | Authored/generated contract stability | None |
| Compose smoke test | Packaging, migrations, readiness, and persistence | Containerized PostgreSQL |

Tests must use isolated databases or schemas and deterministic cleanup. Production or personal databases must never be test targets. CI failures should report which layer failed without requiring a developer to reproduce the entire stack first.

## 10. Evidence and documentation outputs

Planned artifacts:

```text
docs/week2/week2-plan.md
docs/week2/week2-review.md
docs/week2/database-design.md
docs/week2/local-operations.md
docs/decisions.md                    # append accepted Week 2 decisions
alembic.ini
alembic/
app/config.py
app/db/
tests/integration/
Dockerfile
compose.yaml
.github/workflows/ci.yml             # if GitHub Actions is selected
evidence/week2/                      # concise final results, not local databases/log dumps
```

Each completed tracker item must link to code/tests or record the exact verification command and result in the Week 2 review.

## 11. Clarifications required from the user

Items marked **blocking** must be answered before their dependent implementation begins. Recommended defaults are designed to keep the learning sequence coherent.

| ID | Clarification | Why it matters | Recommended default | Status |
|---|---|---|---|---|
| C1 | What time budget should Week 2 use? | Determines whether the plan targets a compact learning week or a production-style expansion. | 12–14 focused hours across seven sequencing units | ACCEPTED, 6 Nov 2026 |
| C2 | Is the Portfolio Service part of Week 2, or should Week 2 finish the Exception Service foundation first? | The second service adds a new contract, data model, deployment unit, and failure modes. | Finish the Exception Service foundation; specify Portfolio Service in Week 3 | ACCEPTED, 6 Nov 2026 |
| C3 | May Docker be the required local PostgreSQL path, or must the plan also support a natively installed PostgreSQL server? | Changes setup, test instructions, and support burden. | Docker Compose is the canonical path; allow an external `DATABASE_URL` for advanced/local use | ACCEPTED, 6 Nov 2026 |
| C4 | Should database enums use PostgreSQL native enum types or portable varchar columns with check constraints? | Affects migration complexity and portability. | Varchar plus check constraints for simpler, explicit migrations | ACCEPTED, 6 Nov 2026 |
| C5 | Which CI service should the repository target? | Determines pipeline syntax and secret/service configuration. | GitHub Actions | ACCEPTED, 6 Nov 2026 |
| C6 | Keep Python 3.9 compatibility or upgrade the project baseline? | Affects dependency versions, typing syntax, Docker image, and CI matrix. | Keep Python 3.9 for Week 2; schedule an intentional upgrade separately | ACCEPTED, 6 Nov 2026 |
| C7 | Is remote deployment expected in Week 2? If yes, which platform? | Adds credentials, managed PostgreSQL, networking, and release verification. | No remote deployment in Week 2; produce a deployment-ready container locally | ACCEPTED, 6 Nov 2026 |
| C8 | Should Week 2 include authentication/authorization? | Auth changes every endpoint, tests, and API contract and deserves its own threat model. | Defer authentication; keep the synthetic local learning boundary | ACCEPTED, 6 Nov 2026 |
| C9 | Do you want strict quality tools now, and do you have preferences? | Determines CI gates and potential cleanup scope. | Ruff across the repository; mypy targeting `app/` and `scripts/` | ACCEPTED, 6 Nov 2026 |
| C10 | Should migration startup be an explicit one-shot command/service or happen automatically inside API startup? | Impacts concurrency safety and operational clarity. | Explicit migration command/Compose service; API startup never mutates schema | ACCEPTED, 6 Nov 2026 |
| C11 | How should the combined uncommitted Week 1 and Week 2 work be published for CI? | The repository is on `main` at `origin/main`; triggering GitHub Actions requires committing and pushing the preserved working tree. | Create `week2-persistence`, commit all current Week 1/Week 2 changes together, push it, and monitor CI | ACCEPTED, 6 Nov 2026 |

## 12. Decision log

Record answers here before updating dependent work items.

| Date | Decision | Rationale | Affected items |
|---|---|---|---|
| 6 Nov 2026 | Preserve the Week 1 API contract and regression suite | Week 2 tests whether infrastructure can evolve behind stable behavior | All |
| 6 Nov 2026 | Keep both in-memory and PostgreSQL repositories | Fast unit feedback plus real persistence evidence | W2-02, W2-06, W2-14 |
| 6 Nov 2026 | Accept recommended defaults C1–C8 and C10 | Keeps Week 2 focused on a reproducible PostgreSQL foundation; Portfolio Service moves to Week 3 | W2-01–W2-15 except quality-tool choice |
| 6 Nov 2026 | Use Ruff repository-wide and targeted mypy for `app/` and `scripts/` | Enforces consistent code and production type safety without expanding Week 2 into cleanup of learning exercises and tests | W2-12, W2-14 |
| 6 Nov 2026 | Publish the combined Week 1/Week 2 working tree on `week2-persistence` | Preserves the existing work as one reviewable milestone and triggers GitHub Actions without updating `main` directly | W2-12, W2-14 |

## 13. Risks and controls

| Risk | Control |
|---|---|
| ORM concerns leak into HTTP/domain layers | Repository protocol, separate persistence model, mapping tests, import-boundary review |
| Tests pass only because they use in-memory storage | PostgreSQL repository contract and API integration suites in CI |
| Duplicate IDs under concurrency | Database identity/sequence plus parallel create test |
| Migrations work only on an existing developer database | Fresh upgrade/downgrade/re-upgrade check in CI |
| API starts before schema is ready | Explicit migration step and readiness probe |
| Environment secrets appear in logs or commits | Secret settings types, sanitization tests, `.env.example`, ignore rules |
| Docker setup hides application defects | Run core tests outside Compose and a separate end-to-end Compose smoke test |
| Week 2 expands into multiple unfinished services | Complete W2-00–W2-14 before starting W2-15 |
| Existing uncommitted work is overwritten | Capture baseline status and make narrowly scoped changes; do not reset user changes |

## 14. Weekly review scorecard

| Category | Weight | Passing evidence |
|---|---:|---|
| Contract and regression preservation | 20 | Week 1 suite plus OpenAPI validator pass |
| Persistence correctness | 25 | Repository, transaction, concurrency, and restart tests pass |
| Migration quality | 15 | Fresh upgrade/downgrade/re-upgrade passes |
| Reproducible packaging | 15 | Docker Compose smoke workflow passes |
| Operational foundations | 10 | Configuration, readiness, structured logging, sanitization checks pass |
| CI and documentation | 15 | Fresh CI pass and accurate Week 2 docs/evidence |

Target: **90/100 or higher**, with every definition-of-done item marked mandatory passing. A high score cannot compensate for a failed mandatory item.

## 15. Immediate next action after clarification

Resolve C11, then publish the reviewed branch and record the first GitHub Actions result for W2-12 and W2-14.
