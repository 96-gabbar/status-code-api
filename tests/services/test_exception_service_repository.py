from app.repositories.in_memory_exception_repository import (
    InMemoryExceptionRepository,
)
from app.schemas.exception import CreateExceptionRequest
from app.services.exception_service import ExceptionService


def create_payload() -> CreateExceptionRequest:
    return CreateExceptionRequest(
        portfolio_id="PORT-201",
        transaction_id="TXN-918273",
        type="SETTLEMENT_MISMATCH",
        severity="HIGH",
        description="Expected settlement amount differs",
    )


def test_service_uses_injected_in_memory_repository() -> None:
    repository = InMemoryExceptionRepository()
    service = ExceptionService(repository=repository)

    created = service.create(create_payload())

    assert service.repository is repository
    assert repository.get(created.exception_id) == created


def test_default_service_uses_an_isolated_in_memory_repository() -> None:
    first_service = ExceptionService()
    second_service = ExceptionService()

    created = first_service.create(create_payload())

    assert isinstance(first_service.repository, InMemoryExceptionRepository)
    assert first_service.get(created.exception_id) == created
    assert second_service.repository.get(created.exception_id) is None
