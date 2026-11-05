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
