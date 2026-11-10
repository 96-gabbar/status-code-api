"""Check API liveness and dependency readiness inside the API container."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402
from app.db.readiness import DatabaseNotReady, check_database_readiness  # noqa: E402
from app.db.session import create_db_engine  # noqa: E402


def main() -> int:
    try:
        with urlopen("http://127.0.0.1:8000/health", timeout=1) as response:
            body = json.load(response)
            if response.status != 200 or body.get("status") != "healthy":
                raise ValueError("Unexpected liveness response")
    except (URLError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"unhealthy: API liveness failed: {error}", file=sys.stderr)
        return 1

    settings = get_settings()
    if settings.repository_backend == "memory":
        return 0

    engine = create_db_engine(settings)
    try:
        check_database_readiness(engine)
    except DatabaseNotReady as error:
        print(f"unhealthy: dependency readiness failed: {error}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
