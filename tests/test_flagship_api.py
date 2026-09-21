from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.exception import Status
from app.services.state_machine import ExceptionStateMachine, InvalidStateTransitionError


client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_service() -> None:
    from app.services.exception_service import ExceptionService

    app.state.exception_service = ExceptionService()


def payload(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "portfolio_id": "PORT-201",
        "transaction_id": "TXN-918273",
        "type": "SETTLEMENT_MISMATCH",
        "severity": "HIGH",
        "description": "Expected settlement amount differs",
    }
    value.update(overrides)
    return value


def create(**overrides: object) -> dict:
    response = client.post("/api/v1/exceptions", json=payload(**overrides))
    assert response.status_code == 201
    return response.json()


def test_health_contract() -> None:
    assert client.get("/health").json() == {
        "status": "healthy",
        "service": "trade-exception-service",
        "version": "1.0.0",
    }


def test_create_returns_full_resource_and_location() -> None:
    response = client.post("/api/v1/exceptions", json=payload())
    body = response.json()
    assert response.status_code == 201
    assert response.headers["location"].endswith(body["exception_id"])
    assert body["status"] == "OPEN"
    assert body["assigned_to"] is None
    assert body["resolution_code"] is None


def test_repeated_create_generates_distinct_ids() -> None:
    assert create()["exception_id"] != create()["exception_id"]


def test_create_rejects_invalid_enum() -> None:
    response = client.post("/api/v1/exceptions", json=payload(severity="URGENT"))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_rejects_server_owned_field() -> None:
    response = client.post("/api/v1/exceptions", json=payload(status="RESOLVED"))
    assert response.status_code == 422


def test_create_trims_strings() -> None:
    item = create(portfolio_id=" PORT-1 ", description=" description ")
    assert item["portfolio_id"] == "PORT-1"
    assert item["description"] == "description"


def test_get_existing_exception() -> None:
    item = create()
    response = client.get(f"/api/v1/exceptions/{item['exception_id']}")
    assert response.status_code == 200
    assert response.json() == item


def test_get_missing_exception() -> None:
    response = client.get("/api/v1/exceptions/EXC-99999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "EXCEPTION_NOT_FOUND"


def test_get_malformed_id() -> None:
    response = client.get("/api/v1/exceptions/not-an-id")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_list_defaults_and_total() -> None:
    create()
    create()
    response = client.get("/api/v1/exceptions")
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["limit"] == 20


def test_list_filters_by_status() -> None:
    create()
    item = create()
    client.post(f"/api/v1/exceptions/{item['exception_id']}/assign", json={"assignee": "ops"})
    response = client.get("/api/v1/exceptions", params={"status": "INVESTIGATING"})
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["status"] == "INVESTIGATING"


def test_list_filters_by_severity() -> None:
    create(severity="LOW")
    create(severity="HIGH")
    response = client.get("/api/v1/exceptions", params={"severity": "LOW"})
    assert response.json()["total"] == 1


def test_list_combines_filters() -> None:
    create(portfolio_id="P1", severity="HIGH")
    create(portfolio_id="P1", severity="LOW")
    create(portfolio_id="P2", severity="HIGH")
    response = client.get("/api/v1/exceptions", params={"portfolio_id": "P1", "severity": "HIGH"})
    assert response.json()["total"] == 1


def test_list_paginates_after_filtering() -> None:
    for index in range(3):
        create(portfolio_id=f"P{index}")
    response = client.get("/api/v1/exceptions", params={"limit": 2, "offset": 1})
    assert response.json()["total"] == 3
    assert len(response.json()["items"]) == 2


@pytest.mark.parametrize("query", [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"unknown": "x"}])
def test_list_rejects_invalid_query(query: dict[str, object]) -> None:
    response = client.get("/api/v1/exceptions", params=query)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_patch_updates_only_allowed_fields() -> None:
    item = create()
    response = client.patch(f"/api/v1/exceptions/{item['exception_id']}", json={"severity": "CRITICAL"})
    assert response.status_code == 200
    assert response.json()["severity"] == "CRITICAL"
    assert response.json()["description"] == item["description"]


def test_patch_rejects_null() -> None:
    item = create()
    response = client.patch(f"/api/v1/exceptions/{item['exception_id']}", json={"severity": None})
    assert response.status_code == 422


def test_patch_rejects_immutable_field() -> None:
    item = create()
    response = client.patch(f"/api/v1/exceptions/{item['exception_id']}", json={"status": "RESOLVED"})
    assert response.status_code == 422


def test_patch_rejects_empty_body() -> None:
    item = create()
    response = client.patch(f"/api/v1/exceptions/{item['exception_id']}", json={})
    assert response.status_code == 422


def test_patch_missing_item_does_not_mutate() -> None:
    response = client.patch("/api/v1/exceptions/EXC-99999", json={"severity": "LOW"})
    assert response.status_code == 404


def test_assign_transitions_and_stores_assignee() -> None:
    item = create()
    response = client.post(f"/api/v1/exceptions/{item['exception_id']}/assign", json={"assignee": " ops "})
    assert response.status_code == 200
    assert response.json()["status"] == "INVESTIGATING"
    assert response.json()["assigned_to"] == "ops"


def test_assign_rejects_repeat_and_preserves_state() -> None:
    item = create()
    path = f"/api/v1/exceptions/{item['exception_id']}/assign"
    assert client.post(path, json={"assignee": "ops"}).status_code == 200
    response = client.post(path, json={"assignee": "other"})
    assert response.status_code == 409
    assert client.get(f"/api/v1/exceptions/{item['exception_id']}").json()["assigned_to"] == "ops"


def test_assign_rejects_empty_assignee() -> None:
    item = create()
    response = client.post(f"/api/v1/exceptions/{item['exception_id']}/assign", json={"assignee": " "})
    assert response.status_code == 422


def test_resolve_requires_investigating() -> None:
    item = create()
    response = client.post(
        f"/api/v1/exceptions/{item['exception_id']}/resolve",
        json={"resolution_code": "FIXED", "resolution_notes": "done"},
    )
    assert response.status_code == 409


def test_resolve_stores_details() -> None:
    item = create()
    client.post(f"/api/v1/exceptions/{item['exception_id']}/assign", json={"assignee": "ops"})
    response = client.post(
        f"/api/v1/exceptions/{item['exception_id']}/resolve",
        json={"resolution_code": "FIXED", "resolution_notes": "done"},
    )
    assert response.status_code == 200
    assert response.json()["resolution_code"] == "FIXED"


def test_resolve_requires_both_fields() -> None:
    item = create()
    response = client.post(f"/api/v1/exceptions/{item['exception_id']}/resolve", json={"resolution_code": "FIXED"})
    assert response.status_code == 422


def test_close_requires_resolved() -> None:
    item = create()
    response = client.post(f"/api/v1/exceptions/{item['exception_id']}/close")
    assert response.status_code == 409


def test_close_transitions_resolved_to_closed() -> None:
    item = create()
    path = f"/api/v1/exceptions/{item['exception_id']}"
    client.post(path + "/assign", json={"assignee": "ops"})
    client.post(path + "/resolve", json={"resolution_code": "FIXED", "resolution_notes": "done"})
    response = client.post(path + "/close")
    assert response.status_code == 200
    assert response.json()["status"] == "CLOSED"


@pytest.mark.parametrize(
    ("status", "action", "expected"),
    [
        (Status.OPEN, "assign", Status.INVESTIGATING),
        (Status.INVESTIGATING, "resolve", Status.RESOLVED),
        (Status.RESOLVED, "close", Status.CLOSED),
    ],
)
def test_state_machine_all_allowed(status: Status, action: str, expected: Status) -> None:
    assert ExceptionStateMachine().transition(status, action) == expected


@pytest.mark.parametrize(
    ("status", "action"),
    [(status, action) for status in Status for action in ("assign", "resolve", "close")
     if (status, action) not in {
         (Status.OPEN, "assign"),
         (Status.INVESTIGATING, "resolve"),
         (Status.RESOLVED, "close"),
     }],
)
def test_state_machine_rejects_invalid_transitions(status: Status, action: str) -> None:
    with pytest.raises(InvalidStateTransitionError):
        ExceptionStateMachine().transition(status, action)


def test_state_machine_rejects_unknown_action() -> None:
    with pytest.raises(InvalidStateTransitionError):
        ExceptionStateMachine().transition(Status.OPEN, "unknown")
