# Week 3 Plan: Portfolio Service and Reliable Service Integration

**Services:** Trade Exception Management API v1 and Portfolio Service v1
**Status:** IN PROGRESS — W3-01 through W3-13 complete; W3-14 underway
**Plan created:** 6 November 2026
**Week 2 baseline:** 8 Exception API operations, 144 tests passing, OpenAPI differences: 0, PostgreSQL/Compose/GitHub CI passing

> Add a separately owned Portfolio Service and connect it to exception creation through an explicit, observable, failure-aware HTTP boundary without weakening the completed Week 2 foundation.

## 1. Outcome

At the end of Week 3, the repository runs two independently testable FastAPI services:

1. The Portfolio Service owns portfolio data, its API contract, repository, migrations, database, readiness, and container lifecycle.
2. The Exception Service retains ownership of trade exceptions and stores only a portfolio identifier.
3. Exception creation can validate a portfolio through a typed HTTP client with explicit timeout, error mapping, request-ID propagation, and tests for success and dependency failures.

The services share engineering conventions, not database tables or ORM models. Each service must remain runnable and testable without reaching into the other service's persistence layer.

## 2. Definition of done

Week 3 is complete only when all mandatory checks pass:

- [x] Section 11 has no open blocking clarification.
- [x] The Week 2 regression suite and eight-operation Exception API contract still pass unchanged except for an explicitly approved integration behavior change.
- [x] A separately authored Portfolio OpenAPI document matches the generated Portfolio Service contract.
- [x] Portfolio request, response, error, filtering, ordering, and pagination behavior is specified before implementation.
- [x] Portfolio domain, service, repository protocol, in-memory repository, and PostgreSQL repository have focused tests.
- [x] Portfolio persistence has a reversible Alembic migration and owns a database separate from the Exception Service database.
- [x] The Portfolio Service survives process and container restarts without data loss.
- [x] Exception-to-Portfolio communication uses HTTP through a typed client abstraction; no cross-service database query or ORM import exists.
- [x] Correlation/request IDs propagate from the incoming Exception request to the Portfolio request and appear in safe structured logs.
- [x] Portfolio-not-found, timeout, connection failure, malformed response, and unexpected upstream response behavior is deterministic and documented.
- [x] Retry behavior is restricted to explicitly safe operations and has bounded attempts and time.
- [x] Compose starts both databases, both migration jobs, and both APIs in dependency-safe order.
- [x] End-to-end tests cover valid portfolio creation, exception creation for a valid portfolio, unknown portfolio, dependency unavailable, and restart persistence.
- [ ] CI runs both OpenAPI validators, both migration lifecycles, unit/contract/integration tests, lint, formatting, and targeted mypy checks.
- [ ] `docs/week3/week3-review.md` records commands, versions, test counts, CI evidence, deviations, and remaining gaps.

## 3. Scope

### Mandatory

1. Define and freeze the Portfolio Service v1 contract.
2. Implement the Portfolio domain and application service without framework or ORM coupling.
3. Add in-memory and SQLAlchemy repository implementations behind a protocol.
4. Add independent Portfolio database configuration and reversible migrations.
5. Add Portfolio routes, validation, error envelopes, health, readiness, structured logs, and request IDs.
6. Add a typed Portfolio client boundary to the Exception Service.
7. Add explicit dependency failure mapping and bounded timeout/retry behavior.
8. Propagate correlation IDs across the service call.
9. Extend Docker Compose to run two APIs, two migration jobs, and independently owned databases.
10. Add unit, repository, API, integration, and end-to-end tests.
11. Extend GitHub Actions and record hosted evidence.
12. Update README, operations, architecture, and decision documentation.

### Conditional, pending clarification

- Whether portfolio validation is mandatory for every exception create or controlled by configuration during migration.
- Whether Portfolio v1 supports writes beyond create, such as rename/status changes.
- Whether inactive portfolios may receive new exceptions.
- Whether the Portfolio Service needs an exception summary endpoint that calls the Exception Service.

### Deferred

Authentication/authorization, user identity, production deployment, service mesh, distributed tracing backend, circuit breaker libraries, asynchronous messaging, Kafka, Kubernetes, caching, rate limiting, bulk import, portfolio valuation, positions, balances, and production secrets management are outside Week 3 unless the plan is explicitly revised.

## 4. Protected invariants

The following Week 2 behavior remains protected:

- The Exception API keeps its eight method/path operations and authored/generated OpenAPI parity.
- Exception workflow remains `OPEN → INVESTIGATING → RESOLVED → CLOSED`.
- Existing error envelopes, validation precedence, filters, ordering, pagination, timestamps, and public IDs remain stable.
- The Exception Service owns exception transactions and never joins a transaction with the Portfolio Service.
- The Portfolio Service never reads or writes the Exception database.
- Dependency failures never expose URLs, credentials, stack traces, raw upstream bodies, or client headers.
- API startup never mutates schemas; each service uses an explicit migration command or one-shot migration container.
- PostgreSQL remains the live integration target while in-memory implementations support fast unit tests.

Any necessary contract change must first be recorded in Section 12, authored in the relevant OpenAPI document, and covered by regression tests.

## 5. Proposed service architecture

```text
Client
  |
  v
Exception API
  -> ExceptionService
      -> PortfolioGateway protocol
          -> HttpPortfolioClient
              -> Portfolio API
                  -> PortfolioService
                      -> PortfolioRepository protocol
                          +-- InMemoryPortfolioRepository
                          `-- SqlAlchemyPortfolioRepository
                                  -> Portfolio PostgreSQL
      -> ExceptionRepository
          -> Exception PostgreSQL

Explicit migration service -> Exception PostgreSQL
Explicit portfolio migration service -> Portfolio PostgreSQL
```

The recommended repository layout keeps both services in the monorepo while preserving runtime boundaries:

```text
app/                              # existing Exception Service
portfolio_app/                    # new Portfolio Service
portfolio_alembic/                # separate migration history
openapi.yaml                      # existing Exception contract
portfolio-openapi.yaml            # authored Portfolio contract
tests/                            # Exception/shared tests
tests_portfolio/                  # Portfolio-focused tests
tests_e2e/                        # both running services
```

Shared code should be limited to small infrastructure-neutral utilities only when duplication is already causing a maintenance problem. Domain models, repositories, database records, and service configuration remain separate.

## 6. Proposed Portfolio v1 contract

This is a planning proposal, not an approved contract.

### Resource

| Field | Ownership | Proposed rule |
|---|---|---|
| `portfolio_id` | Client on create | Stable string, 1–64 characters; supports existing external identifiers such as `PORT-201` |
| `name` | Client | Required, trimmed, 1–200 characters |
| `owner` | Client | Required team/desk label, trimmed, 1–100 characters |
| `status` | Server/client command | `ACTIVE` or `INACTIVE`; defaults to `ACTIVE` |
| `created_at` | Server | Timezone-aware UTC RFC 3339 timestamp |
| `updated_at` | Server | Timezone-aware UTC RFC 3339 timestamp |

### Recommended operations

| Method | Path | Purpose | Primary success |
|---|---|---|---|
| `POST` | `/api/v1/portfolios` | Create a portfolio with a stable external ID | `201` |
| `GET` | `/api/v1/portfolios/{portfolio_id}` | Retrieve one portfolio | `200` |
| `GET` | `/api/v1/portfolios` | List/filter/paginate portfolios | `200` |
| `PATCH` | `/api/v1/portfolios/{portfolio_id}` | Rename, change owner, or change status | `200` |
| `GET` | `/health` | Process liveness | `200` |

List behavior should mirror the Exception API conventions: deterministic order, filtering before pagination, and `total` calculated before pagination. Proposed filters are `status` and `owner`.

### Recommended integration rule

On `POST /api/v1/exceptions`, the Exception Service checks the Portfolio Service before persisting:

- `ACTIVE` portfolio: continue with exception creation.
- Missing portfolio: reject with a stable client-facing `INVALID_PORTFOLIO` error.
- `INACTIVE` portfolio: reject with `PORTFOLIO_INACTIVE`.
- Timeout, connection failure, malformed response, or upstream 5xx: return `503 DEPENDENCY_UNAVAILABLE`.
- The failed validation must not allocate or persist an exception.

The exact HTTP status for missing/inactive portfolio is blocking clarification C4.

## 7. Work breakdown and tracker

Status values: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `DONE`.

| ID | Work item | Status | Depends on | Acceptance evidence |
|---|---|---|---|---|
| W3-00 | Resolve blocking clarifications and record decisions | DONE | User answers | C1–C12 accepted; Section 11 has no open blocking items |
| W3-01 | Capture Week 2 baseline and branch state | DONE | W3-00 | `evidence/week3/w3-01-baseline.md`; 144 tests pass; both Week 2 hosted runs recorded |
| W3-02 | Author Portfolio v1 OpenAPI and examples | DONE | W3-00, W3-01 | `portfolio-openapi.yaml`; contract validator reports 5 operations and 0 errors; 4 validator tests pass |
| W3-03 | Implement Portfolio domain and state rules | DONE | W3-02 | Framework-free model/service tests cover create, update, active/inactive behavior |
| W3-04 | Define Portfolio repository protocol and in-memory implementation | DONE | W3-03 | Shared repository contract tests pass without infrastructure |
| W3-05 | Add Portfolio SQLAlchemy model and mapping | DONE | W3-03 | Round-trip mapping and UTC/constraint tests pass |
| W3-06 | Add independent Portfolio Alembic migration | DONE | W3-05 | Fresh live upgrade/downgrade/re-upgrade passes against Portfolio DB |
| W3-07 | Implement PostgreSQL Portfolio repository | DONE | W3-04–W3-06 | Live CRUD/filter/order/pagination/constraint tests pass |
| W3-08 | Build Portfolio API, configuration, transactions, health, and readiness | DONE | W3-02, W3-07 | Generated OpenAPI parity; live API and rollback tests pass |
| W3-09 | Define PortfolioGateway and HTTP client | DONE | W3-02, W3-08 | Typed client contract tests cover success, missing, inactive, malformed, timeout, and 5xx |
| W3-10 | Integrate portfolio validation into exception creation | DONE | W3-09 | No exception persists on rejected/dependency-failed validation; existing behavior preserved as approved |
| W3-11 | Add correlation propagation and dependency logging | DONE | W3-09 | Request ID reaches Portfolio Service; logs contain safe dependency outcome/duration fields |
| W3-12 | Extend Compose to two service stacks | DONE | W3-06, W3-08, W3-10 | Six-role startup order, separate volumes/DBs, health, persistence, and shutdown pass |
| W3-13 | Add cross-service end-to-end tests | DONE | W3-10–W3-12 | Valid, unknown, inactive, unavailable, timeout, rollback, and restart scenarios pass |
| W3-14 | Extend CI and quality gates | IN PROGRESS | W3-06–W3-13 | GitHub Actions passes both migrations, contracts, and all tests |
| W3-15 | Update operations, decisions, and architecture docs | DONE | Continuous | README and Week 3 docs match actual commands and behavior |
| W3-16 | Run final review and publish evidence | IN PROGRESS | W3-01–W3-15 | Local review complete; hosted CI evidence and final publication pending |

## 8. Execution sequence

The days are sequencing units rather than calendar promises.

### Day 1 — Clarifications, baseline, and contract

- Resolve Section 11 and record decisions.
- Capture branch, test, OpenAPI, migration, Compose, and CI baseline.
- Author Portfolio schemas, operations, examples, and error precedence.
- Add authored/generated Portfolio OpenAPI validation before route implementation.

Exit check: the Portfolio contract is reviewable and approved before persistence or HTTP integration code begins.

### Day 2 — Portfolio domain and repository boundary

- Implement portfolio entities and update rules.
- Define `PortfolioRepository` behavior.
- Add an in-memory implementation and shared contract tests.
- Keep FastAPI, SQLAlchemy, and HTTP clients out of the domain/service layer.

Exit check: Portfolio behavior runs entirely in memory with deterministic tests.

### Day 3 — Portfolio persistence

- Design the Portfolio table, constraints, indexes, timestamps, and ownership boundaries.
- Add domain/record mappers.
- Add a separate Alembic environment and initial migration.
- Implement the SQLAlchemy repository and live PostgreSQL contract tests.

Exit check: a fresh Portfolio database completes upgrade/downgrade/re-upgrade and repository tests.

### Day 4 — Portfolio API and operations

- Implement routes and error mapping from the approved contract.
- Add request-scoped transaction ownership.
- Add structured logs, request IDs, liveness, and exact-revision readiness.
- Verify API persistence and rollback against PostgreSQL.

Exit check: the standalone Portfolio Service passes OpenAPI and live API integration tests.

### Day 5 — Service-to-service boundary

- Define a `PortfolioGateway` protocol used by the Exception Service.
- Implement a typed HTTP client with explicit base URL, connect/read timeout, and bounded retry policy.
- Propagate request IDs and log safe dependency outcome and duration.
- Map missing, inactive, timeout, unreachable, malformed, and 5xx responses.

Exit check: client contract tests prove deterministic behavior without a running network service.

### Day 6 — Integrated Compose and end-to-end behavior

- Add Portfolio database, migration, and API services to Compose.
- Keep database ownership isolated through separate PostgreSQL containers and volumes.
- Run valid and failure-path tests through real HTTP and both databases.
- Verify that rejected validation does not persist an exception.
- Restart APIs and the full stack while retaining volumes.

Exit check: the documented local workflow brings up both services and passes cross-service smoke tests.

### Day 7 — CI, review, and evidence

- Extend CI to both migration histories and both authored/generated contracts.
- Run the complete unit, contract, integration, and end-to-end suite.
- Update operations, architecture, decisions, and Week 3 evidence.
- Push the reviewed branch, monitor GitHub Actions, and record the final run.

Exit check: every mandatory definition-of-done item has passing local and hosted evidence.

## 9. Test strategy

| Layer | Primary purpose | Runtime dependencies |
|---|---|---|
| Portfolio domain/service unit tests | Field rules and active/inactive behavior | None |
| Portfolio repository contract | Observable storage semantics | In-memory and PostgreSQL variants |
| Portfolio migration tests | Reversible schema lifecycle | Portfolio PostgreSQL |
| Portfolio API integration | HTTP → transaction → repository behavior | Portfolio PostgreSQL |
| Portfolio client contract | Response parsing, timeouts, retries, error mapping | Mock HTTP transport |
| Exception integration | Validation ordering and no partial persistence | Exception PostgreSQL + fake gateway |
| Cross-service end-to-end | Real HTTP boundary and correlation propagation | Both APIs and both PostgreSQL databases |
| OpenAPI comparison | Authored/generated stability for each service | None |
| Compose smoke | Startup order, readiness, persistence, failure behavior | Full container stack |

Failure-path tests must assert public status/error code, persistence outcome, retry count, request-ID propagation, and absence of sensitive log data. Tests must not rely on sleep-based timing when a controlled mock transport or readiness probe can provide deterministic coordination.

## 10. Evidence and documentation outputs

Planned artifacts:

```text
docs/week3/week3-plan.md
docs/week3/week3-review.md
docs/week3/service-boundaries.md
docs/week3/local-operations.md
docs/decisions.md
portfolio-openapi.yaml
portfolio_app/
portfolio_alembic.ini
portfolio_alembic/
tests_portfolio/
tests_e2e/
evidence/week3/
compose.yaml
.github/workflows/ci.yml
```

Each completed tracker item must link to code/tests or record exact commands and results in the Week 3 review. Evidence files should remain concise and must not contain credentials, raw database dumps, or verbose service logs.

## 11. Clarifications required from the user

Items marked **OPEN — BLOCKING** must be resolved before their dependent work begins. Recommended defaults preserve the learning sequence and Week 2 behavior.

| ID | Clarification | Why it matters | Recommended default | Status |
|---|---|---|---|---|
| C1 | What time budget should Week 3 target? | Controls whether this is a focused second-service milestone or a broader platform build. | 14–16 focused hours across seven sequencing units | ACCEPTED, 10 Nov 2026 |
| C2 | Should Portfolio Service be a separate runtime in this monorepo? | Determines packaging, imports, CI, Compose, and service ownership. | Yes: `portfolio_app/` with its own app, config, repository, migrations, and container command | ACCEPTED, 10 Nov 2026 |
| C3 | Which Portfolio v1 operations should be mandatory? | Freezes the public contract and implementation size. | Create, get, list/filter/paginate, patch, and health; no delete in v1 | ACCEPTED, 10 Nov 2026 |
| C4 | How should exception creation treat missing or inactive portfolios? | Changes a flagship Exception endpoint and its documented response codes. | Validate before ID allocation/persistence; return `422 INVALID_PORTFOLIO` or `422 PORTFOLIO_INACTIVE` | ACCEPTED, 10 Nov 2026 |
| C5 | Should portfolio validation be immediately mandatory? | Determines compatibility for existing callers and tests using synthetic portfolio IDs. | Configuration flag defaulting off outside integrated/production mode; enable it in Compose and end-to-end tests | ACCEPTED, 10 Nov 2026 |
| C6 | How should each service own PostgreSQL locally? | Determines isolation and migration safety. | Separate PostgreSQL containers, databases, migration histories, and named volumes | ACCEPTED, 10 Nov 2026 |
| C7 | What timeout/retry policy should the Portfolio client use? | Prevents hanging requests and accidental retry storms. | 500 ms connect + 1 s read timeout; one retry only for idempotent GET on connection/timeout/5xx, no retry for 4xx | ACCEPTED, 10 Nov 2026 |
| C8 | Should Portfolio Service call back into Exception Service for summaries? | Adds reverse dependency and cycle risk. | No in Week 3; keep validation one-way from Exception to Portfolio | ACCEPTED, 10 Nov 2026 |
| C9 | Keep Python 3.9 and the current Ruff/mypy policy? | A baseline upgrade would expand scope and CI changes. | Keep Python 3.9; Ruff repository-wide; mypy for both production app packages and scripts | ACCEPTED, 10 Nov 2026 |
| C10 | Should authentication or remote deployment enter Week 3? | Either changes contracts, credentials, infrastructure, and test scope substantially. | Defer both; finish local/CI service integration first | ACCEPTED, 10 Nov 2026 |
| C11 | What branch should hold Week 3 work? | Avoids mixing implementation into the completed Week 2 branch. | Use the existing local `feature/week3` branch | ACCEPTED, 10 Nov 2026 |
| C12 | How should `feature/week3` acquire the completed Week 2 baseline? | The branch must contain the verified Week 2 implementation before new service work begins. | Use merged Week 2 PR commit `c4bbf2e`; its tree is identical to `week2-persistence` at `f469d42` | ACCEPTED, 12 Nov 2026 |

## 12. Initial decision log

| Date | Decision | Rationale | Affected items |
|---|---|---|---|
| 6 Nov 2026 | Treat the completed Week 2 branch as the Week 3 baseline | Preserves verified persistence, packaging, and CI behavior | All |
| 6 Nov 2026 | Plan Portfolio Service contract before implementation | Prevents storage and client code from defining the public API accidentally | W3-02–W3-10 |
| 6 Nov 2026 | Preserve database ownership across service boundaries | Avoids cross-service joins, shared ORM models, and coupled migrations | W3-05–W3-13 |
| 10 Nov 2026 | Accept recommended defaults C1–C10 | Keeps Week 3 focused on a separately owned Portfolio Service and reliable one-way HTTP integration | W3-01–W3-16 |
| 10 Nov 2026 | Use the existing local `feature/week3` branch | Matches the user's established Week 3 branch naming and checkout | W3-01–W3-16 |
| 12 Nov 2026 | Accept `c4bbf2e` as the Week 3 code baseline | The merged `main` tree and `week2-persistence` tree both resolve to `8d127da8`; no Week 2 file differs | W3-00, W3-01 |

## 13. Risks and controls

| Risk | Control |
|---|---|
| New validation breaks existing Exception callers | Explicit rollout setting, contract decision, regression tests, documented response codes |
| Services become coupled through Python imports | Gateway protocol and HTTP-only production integration |
| Services share tables or migration history | Separate database URLs, models, Alembic trees, containers, and readiness checks |
| Dependency latency exhausts API workers | Short explicit timeouts, bounded retries, measured dependency duration logs |
| Retry duplicates a write | Retry only the idempotent portfolio lookup; never retry exception creation automatically |
| Portfolio outage partially writes an exception | Validate before ID allocation and before opening the persistence workflow |
| Raw upstream data leaks into logs/errors | Stable public errors and allowlisted structured dependency fields |
| End-to-end tests become flaky | Readiness probes, deterministic fault injection, mock transport for timing, isolated databases |
| Compose complexity obscures service ownership | Clear service names, separate migration roles, volumes, and operations guide |
| Week 3 expands into a platform rewrite | Enforce mandatory/conditional/deferred scope and clarification gates |

## 14. Weekly review scorecard

| Category | Weight | Passing evidence |
|---|---:|---|
| Contract quality and Week 2 regression preservation | 20 | Both OpenAPI validators pass and existing Exception behavior remains approved |
| Portfolio domain and persistence correctness | 20 | Domain, repository, migration, transaction, and restart tests pass |
| Service boundary and failure behavior | 25 | HTTP-only integration, deterministic errors, timeout/retry, and no partial writes pass |
| End-to-end reproducibility | 15 | Full Compose stack, readiness, failure paths, and volume persistence pass |
| Observability and operations | 10 | Correlation propagation, safe logs, readiness, and runbook checks pass |
| CI and documentation | 10 | Fresh GitHub Actions run and accurate Week 3 evidence pass |

Target: **90/100 or higher**, with every mandatory definition-of-done item passing. A high score cannot compensate for an unresolved mandatory item.

## 15. Immediate next action after clarification

Execute W3-01 to capture the verified baseline, then begin W3-02 without starting persistence work before the Portfolio contract is approved.
