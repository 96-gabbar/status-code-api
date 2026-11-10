"""Exit successfully when the configured application dependencies are ready."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402
from app.db.readiness import DatabaseNotReady, check_database_readiness  # noqa: E402
from app.db.session import create_db_engine  # noqa: E402


def main() -> int:
    settings = get_settings()
    if settings.repository_backend == "memory":
        print("ready: memory repository")
        return 0

    engine = create_db_engine(settings)
    try:
        check_database_readiness(engine)
    except DatabaseNotReady as error:
        print(f"not ready: {error}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()

    print("ready: PostgreSQL reachable and migrations current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
