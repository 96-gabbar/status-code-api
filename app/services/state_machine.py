from __future__ import annotations

from app.models.exception import Status


class InvalidStateTransitionError(Exception):
    pass


class ExceptionStateMachine:
    _transitions = {
        (Status.OPEN, "assign"): Status.INVESTIGATING,
        (Status.INVESTIGATING, "resolve"): Status.RESOLVED,
        (Status.RESOLVED, "close"): Status.CLOSED,
    }

    def transition(self, current_status: Status, action: str) -> Status:
        try:
            return self._transitions[(current_status, action)]
        except KeyError as exc:
            raise InvalidStateTransitionError(
                f"Cannot {action} exception from {current_status}"
            ) from exc
