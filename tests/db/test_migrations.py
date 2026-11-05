from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

ROOT = Path(__file__).resolve().parents[2]


def test_migration_history_has_one_linear_head() -> None:
    config = Config(str(ROOT / "alembic.ini"))
    scripts = ScriptDirectory.from_config(config)

    assert scripts.get_heads() == ["20261106_0001"]
    assert scripts.get_base() == "20261106_0001"


def test_initial_migration_has_upgrade_and_downgrade() -> None:
    config = Config(str(ROOT / "alembic.ini"))
    migration = ScriptDirectory.from_config(config).get_revision("20261106_0001")

    assert migration is not None
    assert migration.module.upgrade is not None
    assert migration.module.downgrade is not None
