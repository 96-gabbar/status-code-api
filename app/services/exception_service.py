from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from re import fullmatch

from app.models.exception import Severity, Status, TradeException
from app.repositories.exception_repository import ExceptionRepository
from app.repositories.in_memory_exception_repository import (
    InMemoryExceptionRepository,
)
from app.schemas.exception import (
    AssignExceptionRequest,
    CreateExceptionRequest,
    ResolveExceptionRequest,
    UpdateExceptionRequest,
)
from app.services.state_machine import ExceptionStateMachine, InvalidStateTransitionError


class ExceptionNotFoundError(Exception):
    pass


class ExceptionService:
    def __init__(self, repository: ExceptionRepository | None = None) -> None:
        self.repository: ExceptionRepository = (
            repository if repository is not None else InMemoryExceptionRepository()
        )
        self.state_machine = ExceptionStateMachine()

    def _get(self, exception_id: str) -> TradeException:
        item = self.repository.get(exception_id)
        if item is None:
            raise ExceptionNotFoundError(exception_id)
        return item

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def create(self, payload: CreateExceptionRequest) -> TradeException:
        now = self._now()
        return self.repository.create(
            TradeException(
                exception_id=self.repository.next_exception_id(),
                portfolio_id=payload.portfolio_id,
                transaction_id=payload.transaction_id,
                type=payload.type,
                severity=payload.severity,
                status=Status.OPEN,
                description=payload.description,
                assigned_to=None,
                created_at=now,
                updated_at=now,
                resolution_code=None,
                resolution_notes=None,
            )
        )

    def get(self, exception_id: str) -> TradeException:
        return self._get(exception_id)

    def list(
        self,
        *,
        status: Status | None,
        severity: Severity | None,
        portfolio_id: str | None,
        exception_type: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[TradeException], int]:
        return self.repository.list(
            status=status,
            severity=severity,
            portfolio_id=portfolio_id,
            exception_type=exception_type,
            limit=limit,
            offset=offset,
        )

    def update(self, exception_id: str, payload: UpdateExceptionRequest) -> TradeException:
        item = self._get(exception_id)
        severity = item.severity
        description = item.description
        if "severity" in payload.model_fields_set:
            if payload.severity is None:
                raise ValueError("PATCH severity cannot be null")
            severity = payload.severity
        if "description" in payload.model_fields_set:
            if payload.description is None:
                raise ValueError("PATCH description cannot be null")
            description = payload.description
        updated = replace(
            item,
            severity=severity,
            description=description,
            updated_at=self._now(),
        )
        return self.repository.replace(updated)

    def assign(self, exception_id: str, payload: AssignExceptionRequest) -> TradeException:
        item = self._get(exception_id)
        try:
            status = self.state_machine.transition(item.status, "assign")
        except InvalidStateTransitionError as exc:
            raise InvalidStateTransitionError(
                "Exception must be OPEN before it can be assigned"
            ) from exc
        return self.repository.replace(
            replace(item, assigned_to=payload.assignee, status=status, updated_at=self._now())
        )

    def resolve(self, exception_id: str, payload: ResolveExceptionRequest) -> TradeException:
        item = self._get(exception_id)
        try:
            status = self.state_machine.transition(item.status, "resolve")
        except InvalidStateTransitionError as exc:
            raise InvalidStateTransitionError(
                "Exception must be INVESTIGATING before it can be resolved"
            ) from exc
        return self.repository.replace(
            replace(
                item,
                status=status,
                resolution_code=payload.resolution_code,
                resolution_notes=payload.resolution_notes,
                updated_at=self._now(),
            )
        )

    def close(self, exception_id: str) -> TradeException:
        item = self._get(exception_id)
        try:
            status = self.state_machine.transition(item.status, "close")
        except InvalidStateTransitionError as exc:
            raise InvalidStateTransitionError(
                "Exception must be RESOLVED before it can be closed"
            ) from exc
        return self.repository.replace(replace(item, status=status, updated_at=self._now()))

    @staticmethod
    def valid_id(exception_id: str) -> bool:
        return fullmatch(r"EXC-[0-9]+", exception_id) is not None
