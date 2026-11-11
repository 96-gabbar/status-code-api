# W3-07 PostgreSQL repository evidence

Date: 12 November 2026

- `SqlAlchemyPortfolioRepository` implements create, get, replace, filtering, deterministic ordering, count-before-pagination, and pagination.
- Request transaction ownership remains outside the repository.
- Live tests cover CRUD, restart-visible persistence, rollback, invalid lengths/status constraints, and ordering/filter behavior.
- Dedicated Portfolio PostgreSQL suite passed as part of 46 live Portfolio tests.
