# W3-03 Portfolio domain evidence

Date: 12 November 2026

- `Portfolio` and `PortfolioStatus` are framework-free domain types.
- `PortfolioService` covers create, get, partial update, ACTIVE/INACTIVE state, deterministic listing, duplicate IDs, missing IDs, and timezone-aware clocks.
- Neither FastAPI nor SQLAlchemy is imported by the domain model or service.
- The focused Portfolio service suite passes as part of the 21-test Portfolio suite.
