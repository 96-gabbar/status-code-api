"""Automated checks for the Day 1 status-code exercise."""

import pytest
from fastapi.testclient import TestClient

from main import app, reset_example_state


client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def reset_state() -> None:
    reset_example_state()


def test_get_existing_item_returns_200() -> None:
    response = client.get("/examples/item")

    assert response.status_code == 200
    assert response.json() == {"item_id": 1, "name": "Example item"}


def test_create_item_returns_201_and_location() -> None:
    response = client.post("/examples/items", json={"name": "New item"})

    assert response.status_code == 201
    assert response.json() == {"item_id": 2, "name": "New item"}
    assert response.headers["Location"] == "/examples/items/2"


def test_delete_existing_item_returns_empty_204() -> None:
    response = client.delete("/examples/items/1")

    assert response.status_code == 204
    assert response.content == b""


def test_deleted_item_is_not_available_from_fixed_item_route() -> None:
    assert client.delete("/examples/items/1").status_code == 204

    response = client.get("/examples/item")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "ITEM_NOT_FOUND", "message": "Item not found"}
    }


def test_unsupported_command_returns_400() -> None:
    response = client.post("/examples/commands", json={"command": "UNSUPPORTED"})

    assert response.status_code == 400
    assert response.json() == {
        "error": {"code": "UNSUPPORTED_COMMAND", "message": "Unsupported command"}
    }


def test_missing_item_returns_404() -> None:
    response = client.get("/examples/items/999")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "ITEM_NOT_FOUND", "message": "Item not found"}
    }


def test_invalid_transition_returns_409() -> None:
    response = client.post("/examples/closed-item/resolve")

    assert response.status_code == 409
    assert response.json() == {
        "error": {"code": "INVALID_STATE_TRANSITION", "message": "Item is already closed"}
    }


def test_invalid_user_returns_422() -> None:
    response = client.post("/examples/users", json={"age": 17})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["message"] == "Validation error"


def test_unexpected_failure_returns_safe_500() -> None:
    response = client.get("/examples/internal-error")

    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}
    }
    assert "RuntimeError" not in response.text
    assert "stack trace details" not in response.text


def test_repeated_post_creates_distinct_resources() -> None:
    first = client.post("/examples/items", json={"name": "New item"})
    second = client.post("/examples/items", json={"name": "New item"})

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["item_id"] == 2
    assert second.json()["item_id"] == 3
    assert first.json()["item_id"] != second.json()["item_id"]


def test_repeated_delete_has_the_same_final_effect_with_different_statuses() -> None:
    first = client.delete("/examples/items/1")
    second = client.delete("/examples/items/1")
    retrieval = client.get("/examples/items/1")

    assert first.status_code == 204
    assert second.status_code == 404
    assert retrieval.status_code == 404


def test_repeated_put_replacement_has_the_same_final_effect() -> None:
    replacement = {"name": "Replacement item"}

    first = client.put("/examples/items/1", json=replacement)
    second = client.put("/examples/items/1", json=replacement)
    retrieval = client.get("/examples/items/1")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == {"item_id": 1, "name": "Replacement item"}
    assert second.json() == first.json()
    assert retrieval.json() == first.json()


def test_put_missing_item_returns_404() -> None:
    response = client.put("/examples/items/999", json={"name": "Replacement item"})

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "ITEM_NOT_FOUND", "message": "Item not found"}
    }
