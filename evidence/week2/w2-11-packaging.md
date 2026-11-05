# W2-11 Packaging Evidence

**Implementation date:** 6 November 2026
**Status:** DONE — Docker and Compose execution passed

## Implemented

- A Python 3.9 slim image installs a minimal pinned runtime dependency set and runs as a non-root user.
- Compose defines PostgreSQL, a one-shot migration service, and the API as separate roles.
- PostgreSQL must become healthy before migration; migration must succeed before API startup.
- API container health combines HTTP liveness with database reachability and exact migration revision.
- PostgreSQL data uses a named local volume.
- Docker context excludes environments, tests, docs, evidence, caches, and local secrets.

## Live Compose result

- Docker 29.9.3 client / 29.5.2 server and Compose 5.7.0 ran through Colima 0.10.3.
- Both application roles built from the non-root image.
- PostgreSQL became healthy, the one-shot migration exited 0, and the API started afterward and became healthy.
- HTTP liveness and in-container database/schema readiness passed.
- A record survived an API container restart and a complete `docker compose down` / `up -d` cycle with the named volume retained.
- PostgreSQL is exposed only on `127.0.0.1:55432` for host integration tests.

## Verification

```text
.venv-verify/bin/python -m pytest tests/test_packaging.py -q
3 passed
```

The final rebuilt image passed the same ordered startup and health checks after the migration and logging fixes.
