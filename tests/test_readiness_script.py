import pytest

from app.config import get_settings
from scripts.check_readiness import main


def test_readiness_script_accepts_memory_backend(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("STATUS_CODE_API_REPOSITORY_BACKEND", "memory")
    get_settings.cache_clear()

    try:
        assert main() == 0
        assert capsys.readouterr().out.strip() == "ready: memory repository"
    finally:
        get_settings.cache_clear()
