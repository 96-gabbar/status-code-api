# Week 3 Review: Portfolio Service and Reliable Service Integration

**Review date:** 12 November 2026
**Branch:** `feature/week3`
**Baseline:** `c4bbf2e` (completed Week 2 implementation)
**Week 3 commit:** `e99f600` (`Build Week 3 portfolio service integration`)
**Pull request:** [#2 — Build Week 3 portfolio service integration](https://github.com/96-gabbar/status-code-api/pull/2)
**Status:** Implementation and local verification complete; hosted GitHub Actions runs are queued

## 1. Week 3 outcome

Week 3 added a separately owned Portfolio Service and connected it to the
Exception Service through a typed, observable, failure-aware HTTP boundary.
The repository now runs two independently migrated and tested FastAPI services,
each with its own PostgreSQL database and persistence lifecycle.

The completed implementation preserves the Week 2 Exception API contract while
adding optional portfolio validation to exception creation. In the integrated
Compose environment this validation is enabled, so an exception is persisted
only after the referenced portfolio has been confirmed as active.

## 2. Work completed

| Plan item | Achievement | Evidence |
|---|---|---|
| W3-01 | Captured the verified Week 2 baseline and branch state | `evidence/week3/w3-01-baseline.md` |
| W3-02 | Authored and validated the five-operation Portfolio OpenAPI contract | `portfolio-openapi.yaml`; validator and contract tests |
| W3-03 | Built the framework-independent Portfolio domain and state rules | Portfolio service and domain tests |
| W3-04 | Added the repository protocol and in-memory implementation | Shared repository contract tests |
| W3-05 | Added SQLAlchemy records and domain/record mapping | Mapping and constraint tests |
| W3-06 | Added a separate reversible Portfolio Alembic history | Upgrade/downgrade/re-upgrade lifecycle |
| W3-07 | Implemented the PostgreSQL Portfolio repository | Live CRUD, filter, order, pagination, and constraint tests |
| W3-08 | Built the Portfolio API, transactions, health, and readiness | API integration and rollback tests |
| W3-09 | Added the typed Portfolio gateway and HTTP client | Client contract tests for success and dependency failures |
| W3-10 | Integrated validation into exception creation | No ID allocation or persistence on validation failure |
| W3-11 | Propagated request IDs and added safe dependency logging | Correlation and allowlisted structured-log tests |
| W3-12 | Expanded Compose to two isolated service stacks | Two databases, two migrations, and two healthy APIs |
| W3-13 | Added cross-service end-to-end coverage | Valid, invalid, unavailable, and persistence scenarios |
| W3-14 | Extended CI with both contracts, migrations, suites, and quality gates | Workflow committed; hosted runs currently queued |
| W3-15 | Updated operations, architecture, decisions, and README documentation | `docs/week3/`, `docs/decisions.md`, and `README.md` |
| W3-16 | Completed the local review and published the branch and PR | Commit `e99f600`; PR #2; hosted completion pending |

## 3. Portfolio Service delivered

The Portfolio Service owns its domain, API, persistence, migration history,
configuration, readiness checks, and container lifecycle under
`portfolio_app/` and `portfolio_alembic/`.

Its v1 API provides:

- `POST /api/v1/portfolios` to create a portfolio.
- `GET /api/v1/portfolios/{portfolio_id}` to retrieve one portfolio.
- `GET /api/v1/portfolios` to filter, order, and paginate portfolios.
- `PATCH /api/v1/portfolios/{portfolio_id}` to update name, owner, or status.
- `GET /health` for process liveness.
- Exact-migration-revision readiness for safe startup orchestration.

The service implements `ACTIVE` and `INACTIVE` lifecycle states, deterministic
list behavior, UTC timestamps, stable error envelopes, request-scoped database
transactions, and rollback on failed operations.

## 4. Exception-to-Portfolio integration

Exception creation now depends on a `PortfolioGateway` protocol. The production
implementation calls the Portfolio API over HTTP; the Exception Service does
not import Portfolio ORM records or access the Portfolio database.

When validation is enabled, the integration behaves as follows:

| Portfolio outcome | Exception API behavior | Persistence result |
|---|---|---|
| Active portfolio | Continue creating the exception | Exception persisted |
| Portfolio missing | `422 INVALID_PORTFOLIO` | Nothing persisted |
| Portfolio inactive | `422 PORTFOLIO_INACTIVE` | Nothing persisted |
| Timeout, connection failure, malformed response, or upstream 5xx | `503 DEPENDENCY_UNAVAILABLE` | Nothing persisted |

Validation runs before public exception ID allocation and persistence. The
client uses explicit connect/read timeouts and permits one bounded retry only
for the idempotent portfolio lookup on safe transient failures. It does not
retry 4xx responses or exception writes.

The feature setting defaults off for standalone compatibility and is enabled
in the integrated Compose environment.

## 5. Reliability and observability

- Incoming request IDs propagate from the Exception API to the Portfolio API.
- Dependency logs record safe fields such as outcome, duration, attempt count,
  and status without logging credentials or raw upstream bodies.
- Each service owns a separate PostgreSQL container, database URL, Alembic
  history, migration job, and named volume.
- Compose waits for database health and successful one-shot migrations before
  starting the APIs.
- API and full-stack restarts retain database-owned resources.
- The Exception API exposes a stable `503` response when enabled Portfolio
  validation cannot obtain a trustworthy dependency answer.

## 6. Contract and regression results

The existing Exception API retains all eight method/path operations. The only
approved contract addition is a documented `503` response for exception
creation when Portfolio validation is enabled and unavailable.

| Contract check | Result |
|---|---|
| Exception authored/generated OpenAPI | 8 operations; 0 differences |
| Portfolio authored/generated OpenAPI | 5 operations; 0 differences |

The validators compare operations, response codes, parameters, request media
and schemas, and response media and schemas within their documented limits.

## 7. Verification results

Verification environment:

- Python 3.9.6
- Docker 29.9.3
- Docker Compose 5.7.0
- PostgreSQL 16 Alpine containers

| Check | Actual result |
|---|---|
| Full service, unit, contract, and integration suite | 213 passed against two PostgreSQL databases |
| Running-stack end-to-end suite | 3 passed |
| Exception migration lifecycle | Passed; head `20261106_0001` |
| Portfolio migration lifecycle | Passed; head `20261112_0001` |
| Ruff lint | Passed |
| Ruff format check | Passed across 155 files |
| Targeted mypy | Passed across 57 production and script files |
| Six-role Compose startup | Both APIs and databases healthy; both migration jobs exited 0 |
| Dependency outage and recovery | Stable 503, no partial write, and healthy recovery |
| Full-stack restart | Exception and Portfolio resources persisted |

The exact local commands are recorded in `docs/week3/local-operations.md`.
Focused implementation evidence is stored under `evidence/week3/`.

## 8. Publication and hosted CI

Commit `e99f600` is pushed to `origin/feature/week3`, and the branch tracks its
remote counterpart. Pull request #2 is open, cleanly mergeable, and targets
`main`.

GitHub created two CI runs for the published commit:

- [Run #5 — push](https://github.com/96-gabbar/status-code-api/actions/runs/43096478720)
- [Run #6 — pull request](https://github.com/96-gabbar/status-code-api/actions/runs/43096620278)

At review time both runs remain queued and GitHub has not assigned their jobs
to a runner. The workflow contains the expected `quality-and-tests` and
`compose-e2e` jobs. This review does not claim hosted success while those runs
remain incomplete.

## 9. Deviations and deferred scope

- Timeout behavior is tested deterministically with an HTTP mock transport;
  the live Compose suite covers a fully unavailable Portfolio dependency.
- Hosted CI completion remains the only open mandatory evidence item.
- Authentication, remote deployment, distributed tracing backends, circuit
  breaker libraries, asynchronous messaging, production secret management,
  caching, and rate limiting remain deferred as planned.

## 10. Scorecard

| Category | Score | Evidence |
|---|---:|---|
| Contract quality and Week 2 regression preservation | 20/20 | Both contracts match generated OpenAPI; eight Exception operations preserved |
| Portfolio domain and persistence correctness | 20/20 | Domain, repository, migration, transaction, and restart checks pass |
| Service boundary and failure behavior | 25/25 | HTTP-only integration, deterministic errors, bounded retry, and no partial writes |
| End-to-end reproducibility | 15/15 | Six-role Compose stack and running-stack scenarios pass |
| Observability and operations | 10/10 | Correlation propagation, safe logs, readiness, and runbook complete |
| CI and documentation | 5/10 | Documentation and workflow complete; hosted jobs still queued |
| **Current total** | **95/100** | **Provisional until hosted CI completes** |

Week 3 meets the target score locally. W3-14 and W3-16 remain in progress only
because the mandatory hosted workflow evidence has not completed.
