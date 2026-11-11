# W3-12 Compose evidence

Date: 12 November 2026

- Six roles started in dependency order: Exception DB, Exception migration, Exception API, Portfolio DB, Portfolio migration, and Portfolio API.
- Both database containers became healthy; both migration jobs exited 0; both APIs became healthy.
- Exception and Portfolio databases use distinct containers, credentials, URLs, migration histories, and named volumes.
- The integrated Exception API enables portfolio validation and calls `http://portfolio-api:8001`.
- A real Portfolio create followed by Exception create returned 201 from both services.
- The same `compose-smoke-1` request ID appeared in the incoming Exception log, dependency log, and Portfolio lookup log.
- Full `docker compose down` and `docker compose up -d` preserved both created resources through named volumes.
