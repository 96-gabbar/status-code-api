# W3-05 SQLAlchemy mapping evidence

Date: 12 November 2026

- Portfolio ORM metadata is isolated under `PortfolioBase`.
- The `portfolios` table definition has stable external ID ownership, length/status constraints, timezone-aware timestamps, and owner/status/created-order indexes.
- Domain/record mapping preserves every field, normalizes aware timestamps to UTC, rejects naive timestamps, and rejects unknown persisted status values.
- Portfolio tests: 21 passed.
- Ruff check and format check: passed.
- Targeted mypy for `portfolio_app`: passed across 12 source files.
