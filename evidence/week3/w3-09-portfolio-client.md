# W3-09 Portfolio client evidence

Date: 12 November 2026

- `PortfolioGateway` keeps the Exception application boundary independent of HTTP and Portfolio persistence types.
- `HttpPortfolioClient` uses 500 ms connect and 1 second read timeouts.
- It retries once only for idempotent GET timeout, connection, or 5xx failures.
- It does not retry 4xx or malformed responses.
- Contract tests cover active, inactive, missing, malformed JSON/schema, mismatched ID, timeout, connection failure, 4xx, 5xx, and request-ID propagation.
- Focused client/config suite: 18 passed.
