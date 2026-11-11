# Week 3 architecture

## Runtime boundary

```text
Client
  -> Exception API :8000
       -> ExceptionService
            -> ExceptionRepository -> Exception PostgreSQL
            -> PortfolioGateway -> HTTP GET
                 -> Portfolio API :8001
                      -> PortfolioService
                           -> PortfolioRepository -> Portfolio PostgreSQL
```

The Exception Service never imports Portfolio ORM records, sessions, or
migrations. The Portfolio Service never reads Exception data. A failed
portfolio lookup cannot share or partially commit an Exception transaction.

## Source boundaries

- `app/`: Exception API, domain behavior, persistence, and typed Portfolio HTTP client.
- `portfolio_app/`: Portfolio API, domain behavior, and persistence.
- `alembic/` and `portfolio_alembic/`: independent migration histories.
- `openapi.yaml` and `portfolio-openapi.yaml`: independently authored contracts.
- `tests/`, `tests_portfolio/`, and `tests_e2e/`: service and cross-service evidence.

## Startup order

1. Each PostgreSQL container reaches database health.
2. Each one-shot migration job upgrades its owned database.
3. The Portfolio API starts and passes liveness plus exact-revision readiness.
4. The Exception API starts with Portfolio validation enabled and passes its own readiness.

Both APIs expose process liveness at `/health`. Container readiness additionally
checks database connectivity and the exact expected migration revision.

## Failure behavior

Exception creation validates a portfolio before allocating an exception ID.
Missing and inactive portfolios return stable 422 errors. Connection failure,
timeout, malformed response, unexpected upstream status, and exhausted 5xx
retry return `503 DEPENDENCY_UNAVAILABLE`. No rejected path persists an
exception.
