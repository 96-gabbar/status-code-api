"""Contract tests for the Week 1 validation API."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent))
from main import app  # noqa: E402


client = TestClient(app)


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "Ada Lovelace", "email": "ada@example.com", "age": 36, "country": "GB"},
        {"name": "Grace Hopper", "email": "grace@example.org", "age": 85, "country": "US"},
        {"name": "Linus Torvalds", "email": "linus@example.net", "age": 54, "country": "FI"},
        {"name": "  Alan Turing  ", "email": "alan@example.com", "age": 41, "country": "GB"},
        {"name": "Katherine Johnson", "email": "kj@example.com", "age": 101, "country": "US"},
    ],
)
def test_valid_users_are_created(payload):
    response = client.post("/users", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["id"].startswith("USR-")
    assert len(body["id"]) == 16
    assert body["name"] == payload["name"].strip()
    assert body["email"] == payload["email"]
    assert body["age"] == payload["age"]
    assert body["country"] == payload["country"]


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "A", "email": "valid@example.com", "age": 20, "country": "US"},
        {"name": "A" * 101, "email": "valid@example.com", "age": 20, "country": "US"},
        {"name": "  ", "email": "valid@example.com", "age": 20, "country": "US"},
        {"name": "Valid Name", "email": "not-an-email", "age": 20, "country": "US"},
        {"name": "Valid Name", "email": "valid@example.com", "age": 17, "country": "US"},
        {"name": "Valid Name", "email": "valid@example.com", "age": True, "country": "US"},
        {"name": "Valid Name", "email": "valid@example.com", "age": 20.5, "country": "US"},
        {"name": "Valid Name", "email": "valid@example.com", "age": "20", "country": "US"},
        {"name": "Valid Name", "email": "valid@example.com", "age": 20, "country": "U"},
        {"name": "Valid Name", "email": "valid@example.com", "age": 20, "country": "USA"},
        {
            "name": "Valid Name",
            "email": "valid@example.com",
            "age": 20,
            "country": "US",
            "role": "admin",
        },
    ],
)
def test_invalid_users_share_validation_error_envelope(payload):
    response = client.post("/users", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["message"] == "Request validation failed"
    assert response.json()["error"]["details"]


def test_missing_required_field_uses_validation_error_envelope():
    response = client.post(
        "/users",
        json={"name": "Valid Name", "email": "valid@example.com", "age": 20},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_non_object_json_uses_validation_error_envelope():
    response = client.post("/users", json=["not", "an", "object"])

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
