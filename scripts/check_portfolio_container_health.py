"""Check Portfolio API liveness and exact database-revision readiness."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from portfolio_app.config import get_portfolio_settings  # noqa: E402
from portfolio_app.db.readiness import (  # noqa: E402
    PortfolioDatabaseNotReady,
    check_portfolio_database_readiness,
)
from portfolio_app.db.session import create_portfolio_db_engine  # noqa: E402


def main() -> int:
    try:
        with urlopen("http://127.0.0.1:8001/health", timeout=1) as response:
            body = json.load(response)
            if response.status != 200 or body.get("status") != "healthy":
                raise ValueError("Unexpected liveness response")
    except (URLError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"unhealthy: Portfolio API liveness failed: {error}", file=sys.stderr)
        return 1

    settings = get_portfolio_settings()
    if settings.repository_backend == "memory":
        return 0

    engine = create_portfolio_db_engine(settings)
    try:
        check_portfolio_database_readiness(engine)
    except PortfolioDatabaseNotReady as error:
        print(f"unhealthy: Portfolio dependency readiness failed: {error}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
