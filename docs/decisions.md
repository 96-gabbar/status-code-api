# Week 1 design decisions

- POST is used for assign, resolve, and close because each is a domain command,
  not a CRUD replacement or deletion.
- Input and output schemas are separate so server-owned fields cannot be
  supplied by clients and response exposure remains intentional.
- The repository is in memory for this learning milestone; process restart
  resets synthetic data.
- Stable machine-readable error codes are used for client branching while
  messages remain explanatory.
- Filtering happens before pagination, and `total` reports the filtered count.
- `close` is exposed over HTTP in addition to the pure-Python state machine.
- Persistence, authentication, deployment, external service calls, queues, and
  intentional failure routes are deferred beyond Week 1.

## Week 2

- The service depends on an `ExceptionRepository` protocol. In-memory and
  SQLAlchemy implementations stay behind that boundary.
- SQLAlchemy records are separate from domain dataclasses and API schemas.
- PostgreSQL enum values use varchar columns with named check constraints to
  keep migrations explicit and portable.
- A PostgreSQL sequence allocates concurrency-safe public ID suffixes.
- HTTP request dependencies own transactions: commit on success, roll back on
  failure, and always close the session. Repositories only flush.
- API startup never mutates schema. Alembic runs as an explicit command or
  one-shot Compose service.
- `/health` remains process liveness. Operational readiness is a separate
  command that verifies PostgreSQL and the exact migration revision.
- Request logs are structured JSON and exclude query strings, bodies, headers,
  credentials, exception text, and stack traces.
- Docker Compose is the canonical local PostgreSQL path; external PostgreSQL is
  supported through `DATABASE_URL`.
- Ruff checks the repository; mypy targets production application and
  operational script code.

## Week 3

- The Portfolio Service owns portfolio identity, metadata, lifecycle, ORM
  records, migrations, and its PostgreSQL database.
- The Exception Service stores only `portfolio_id` and validates through an
  HTTP `PortfolioGateway`; it never imports Portfolio persistence code or
  queries the Portfolio database.
- Portfolio validation defaults off for standalone compatibility and is
  enabled in the integrated Compose environment.
- An active portfolio permits exception creation. Missing and inactive
  portfolios map to stable 422 errors; transport, malformed-response, and
  upstream failures map to 503.
- Validation happens before exception ID allocation or persistence.
- Portfolio GET uses a 500 ms connect timeout, a 1 second read timeout, and one
  retry for connection, timeout, or 5xx failures. It does not retry 4xx or
  malformed responses.
- Request IDs propagate across the HTTP boundary. Dependency logs contain only
  allowlisted outcome and timing fields.
- Local Compose uses two PostgreSQL containers and volumes, two migration jobs,
  and two API processes to preserve service ownership.
