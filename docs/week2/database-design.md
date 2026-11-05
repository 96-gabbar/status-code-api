# Week 2 Database Design

The Exception Service stores its domain state in PostgreSQL through SQLAlchemy while keeping HTTP, domain, and persistence models separate.

## Boundary

```text
HTTP route
  → request-scoped ExceptionService
    → ExceptionRepository protocol
      → SqlAlchemyExceptionRepository
        → caller-owned SQLAlchemy Session
          → PostgreSQL
```

The repository flushes changes so database-generated results are available, but it never commits. The request dependency commits a successful request, rolls back a failed request, and always closes the session. In-memory storage implements the same protocol for infrastructure-free unit tests.

## Schema

`trade_exceptions` contains a numeric internal primary key and a unique public `exception_id`. Public IDs are allocated from `exception_id_seq`, starting at 10001, and formatted as `EXC-<digits>`.

| Column | PostgreSQL representation | Key behavior |
|---|---|---|
| `id` | `bigserial` | Internal primary key and deterministic tie-breaker |
| `exception_id` | `varchar(32)` | Unique, required, format check |
| `portfolio_id` | `varchar(64)` | Required, length check, indexed |
| `transaction_id` | `varchar(64)` | Required, length check |
| `type` | `varchar(40)` | Required, enum-value check |
| `severity` | `varchar(16)` | Required, enum-value check, indexed |
| `status` | `varchar(20)` | Required, enum-value check, indexed |
| `description` | `text` | Required, 1–2,000 character check |
| `assigned_to` | `varchar(100)` | Nullable, length check when present |
| `created_at` | `timestamptz` | Required, UTC-normalized, ordering index |
| `updated_at` | `timestamptz` | Required, UTC-normalized |
| `resolution_code` | `varchar(100)` | Nullable, length check when present |
| `resolution_notes` | `text` | Nullable, length check when present |

Varchar plus named check constraints was chosen over native PostgreSQL enums. This keeps values explicit while avoiding enum-type migration complexity. API validation remains responsible for client-facing error details; database constraints protect stored data from every caller.

## Query behavior

Filtering, total count, ordering, limit, and offset execute in the repository. `total` is calculated after filters and before pagination. Results order by `created_at`, then internal `id`, preserving the Week 1 deterministic behavior for records created through this service.

Indexes cover the current filters (`portfolio_id`, `severity`, `status`) and ordering (`created_at`, `id`). New indexes require query evidence rather than being added speculatively.

## Migrations

Alembic owns schema changes. API startup never creates or changes schema. Operators run the migration as a separate command or one-shot Compose service before starting the API.

The initial revision is `20261106_0001`. Operational readiness requires PostgreSQL connectivity and this exact revision in `alembic_version`.

## Known verification boundary

Offline PostgreSQL DDL, mapping tests, repository unit tests, and migration-graph tests pass locally. Live migration, query, constraint, transaction, restart, and concurrency checks require PostgreSQL. They are implemented under `tests/integration/` and run when `TEST_DATABASE_URL` is present.
