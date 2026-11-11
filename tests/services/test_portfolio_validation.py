from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.repositories.in_memory_exception_repository import InMemoryExceptionRepository
from app.schemas.exception import CreateExceptionRequest
from app.services.exception_service import ExceptionService
from app.services.portfolio_gateway import (
    PortfolioDependencyUnavailableError,
    PortfolioGatewayError,
    PortfolioInactiveError,
    PortfolioMissingError,
    PortfolioSnapshot,
    PortfolioState,
)


def payload() -> CreateExceptionRequest:
    return CreateExceptionRequest(
        portfolio_id="PORT-201",
        transaction_id="TXN-918273",
        type="SETTLEMENT_MISMATCH",
        severity="HIGH",
        description="Expected settlement amount differs",
    )


@dataclass
class StubGateway:
    result: PortfolioSnapshot | PortfolioGatewayError
    calls: int = 0
    request_id: str | None = None

    def get_portfolio(
        self,
        portfolio_id: str,
        *,
        request_id: str | None = None,
    ) -> PortfolioSnapshot:
        self.calls += 1
        self.request_id = request_id
        if isinstance(self.result, PortfolioGatewayError):
            raise self.result
        assert portfolio_id == self.result.portfolio_id
        return self.result


def test_validation_disabled_preserves_standalone_creation() -> None:
    gateway = StubGateway(PortfolioMissingError("PORT-201"))
    service = ExceptionService(portfolio_gateway=gateway, portfolio_validation_enabled=False)

    created = service.create(payload())

    assert created.portfolio_id == "PORT-201"
    assert gateway.calls == 0


def test_active_portfolio_is_checked_before_creation_and_receives_request_id() -> None:
    gateway = StubGateway(PortfolioSnapshot("PORT-201", PortfolioState.ACTIVE))
    service = ExceptionService(portfolio_gateway=gateway, portfolio_validation_enabled=True)

    created = service.create(payload(), request_id="request-123")

    assert created.exception_id == "EXC-10001"
    assert gateway.calls == 1
    assert gateway.request_id == "request-123"


@pytest.mark.parametrize(
    "failure",
    [
        PortfolioMissingError("PORT-201"),
        PortfolioDependencyUnavailableError("offline"),
    ],
)
def test_gateway_failure_does_not_allocate_or_persist_exception(
    failure: PortfolioGatewayError,
) -> None:
    repository = InMemoryExceptionRepository()
    service = ExceptionService(
        repository,
        portfolio_gateway=StubGateway(failure),
        portfolio_validation_enabled=True,
    )

    with pytest.raises(type(failure)):
        service.create(payload())

    assert repository.list(
        status=None,
        severity=None,
        portfolio_id=None,
        exception_type=None,
        limit=20,
        offset=0,
    ) == ([], 0)
    assert repository.next_exception_id() == "EXC-10001"


def test_inactive_portfolio_is_rejected_before_allocation() -> None:
    repository = InMemoryExceptionRepository()
    service = ExceptionService(
        repository,
        portfolio_gateway=StubGateway(PortfolioSnapshot("PORT-201", PortfolioState.INACTIVE)),
        portfolio_validation_enabled=True,
    )

    with pytest.raises(PortfolioInactiveError):
        service.create(payload())

    assert repository.next_exception_id() == "EXC-10001"
