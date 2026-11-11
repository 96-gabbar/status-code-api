# Portfolio Service v1 Contract Decisions

## Resource ownership

The Portfolio Service owns portfolio identity, name, owner, status, timestamps, persistence, and lifecycle. The Exception Service stores `portfolio_id` as an external reference and never reads the Portfolio database.

Clients supply `portfolio_id` during creation because the learning system already uses stable external identifiers such as `PORT-201` and `P1`. The service rejects duplicate identifiers with `409 PORTFOLIO_ALREADY_EXISTS`.

## Operations

Portfolio v1 exposes create, get, list, patch, and health. It does not expose deletion. Historical exceptions may continue to reference an inactive portfolio, so lifecycle changes use `PATCH` with `status: INACTIVE`.

PATCH accepts one or more of `name`, `owner`, and `status`. An empty object, explicit null, unknown field, or invalid value returns `422 VALIDATION_ERROR`. `portfolio_id`, `created_at`, and `updated_at` are immutable.

## Validation and lookup precedence

1. Validate path, query, and body input.
2. Look up the portfolio.
3. Apply the requested change.
4. Commit the request transaction.

Malformed identifiers therefore return 422 before a resource lookup. A well-formed missing identifier returns `404 PORTFOLIO_NOT_FOUND`.

## Listing semantics

- Optional filters: exact `status` and exact normalized `owner`.
- Filter before pagination.
- `total` is the filtered count before pagination.
- Default `limit` is 20; maximum is 100.
- Default `offset` is 0.
- Order by `created_at` descending, then `portfolio_id` ascending for a deterministic tie-break.

## Exception integration

When portfolio validation is enabled, exception creation performs an HTTP portfolio lookup before allocating an exception ID or opening the write workflow.

- Active portfolio: continue.
- Missing portfolio: `422 INVALID_PORTFOLIO`.
- Inactive portfolio: `422 PORTFOLIO_INACTIVE`.
- Timeout, connection failure, malformed response, or upstream 5xx: `503 DEPENDENCY_UNAVAILABLE`.

The rollout flag is disabled for standalone compatibility and enabled in the integrated Compose and end-to-end environments.

## Compatibility limits

The v1 contract intentionally excludes delete, positions, balances, valuation, authentication, reverse calls into the Exception Service, and remote deployment concerns.
