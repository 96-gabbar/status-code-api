from unittest.mock import create_autospec

from sqlalchemy.orm import Session

from app.config import Settings
from app.main import create_app
from app.services.exception_service import ExceptionService


def test_memory_configuration_builds_in_memory_service() -> None:
    settings = Settings(_env_file=None, repository_backend="memory")

    app = create_app(settings=settings)

    assert app.state.settings is settings
    assert isinstance(app.state.exception_service, ExceptionService)


def test_postgres_configuration_uses_injected_session_factory() -> None:
    settings = Settings(_env_file=None, repository_backend="postgres")
    session = create_autospec(Session, instance=True)

    def session_factory() -> Session:
        return session

    app = create_app(settings=settings, session_factory=session_factory)  # type: ignore[arg-type]

    assert app.state.settings is settings
    assert app.state.session_factory is session_factory
    assert not hasattr(app.state, "exception_service")
