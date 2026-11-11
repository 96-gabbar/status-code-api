# W3-04 repository boundary evidence

Date: 12 November 2026

- `PortfolioRepository` defines create, get, replace, filter, order, count, and pagination behavior.
- `InMemoryPortfolioRepository` implements the protocol without infrastructure.
- Shared contract tests prove round-trip replacement, filtering before count/pagination, created-at-descending and ID-ascending tie ordering, and collection isolation.
- The same contract will be applied to the PostgreSQL implementation in W3-07.
