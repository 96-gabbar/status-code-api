# Week 3 Review: Portfolio Service and Reliable Integration

**Review date:** 12 November 2026  
**Branch:** `feature/week3`  
**Baseline:** `c4bbf2e`  
**Status:** Local implementation complete; hosted CI publication pending

## Delivered behavior

- A separately owned Portfolio API provides create, get, list/filter/paginate,
  patch, liveness, request transactions, and exact-revision readiness.
- Portfolio domain, in-memory repository, SQLAlchemy repository, mapping,
  migration, configuration, and PostgreSQL integration remain under
  `portfolio_app` and `portfolio_alembic`.
- Exception creation validates Portfolio state through a typed HTTP gateway
  before allocating a public exception ID or persisting data.
- Missing, inactive, and unavailable Portfolio outcomes map to stable
  `INVALID_PORTFOLIO`, `PORTFOLIO_INACTIVE`, and `DEPENDENCY_UNAVAILABLE`
  errors.
- Request IDs propagate across the service call and safe dependency logs record
  outcome, duration, attempts, and status.
- Compose runs two databases, two one-shot migration jobs, and two APIs with
  separate named volumes and dependency-safe startup.

## Local verification

Environment:

- Python 3.9.6
- Docker 29.9.3
- Docker Compose 5.7.0
- PostgreSQL 16 Alpine containers

Results:

| Check | Result |
|---|---|
| Exception authored/generated OpenAPI | 8 operations, 0 differences |
| Portfolio authored/generated OpenAPI | 5 operations, 0 differences |
| Exception migration downgrade/re-upgrade | Passed, head `20261106_0001` |
| Portfolio migration downgrade/re-upgrade | Passed, head `20261112_0001` |
| Full service/unit/integration suite | 213 passed |
| Running-stack end-to-end suite | 3 passed |
| Ruff | Passed; 155 files formatted |
| Targeted mypy | Passed; 57 production/script files |
| Six-role Compose startup | Both APIs/DBs healthy; both migrations exited 0 |
| Dependency outage | Stable 503; no exception persisted; recovery healthy |
| Full stack restart | Both database-owned resources persisted |

Commands used are documented in `docs/week3/local-operations.md`. Detailed
evidence for W3-01 through W3-13 is stored under `evidence/week3/`.

## Contract change

The existing eight Exception operations remain unchanged. The approved Week 3
change adds a documented `503` response to exception creation when Portfolio
validation is enabled and the dependency cannot provide a trustworthy answer.
The rollout setting defaults off for standalone compatibility and is enabled
in Compose.

## Deviations and limits

- Timeout behavior is verified deterministically with an HTTP mock transport;
  the live Compose end-to-end suite exercises a fully unavailable dependency.
- Authentication, remote deployment, distributed tracing backends, circuit
  breaker libraries, messaging, and production secret management remain
  deferred as planned.
- Hosted GitHub Actions evidence cannot be recorded until this branch is
  committed and pushed. W3-14 and W3-16 remain in progress until that run is
  green and linked here.

## Scorecard before hosted publication

| Category | Score |
|---|---:|
| Contract quality and Week 2 regression preservation | 20/20 |
| Portfolio domain and persistence correctness | 20/20 |
| Service boundary and failure behavior | 25/25 |
| End-to-end reproducibility | 15/15 |
| Observability and operations | 10/10 |
| CI and documentation | 5/10 |
| **Current total** | **95/100** |

The score is provisional because the mandatory hosted CI item is still open.
