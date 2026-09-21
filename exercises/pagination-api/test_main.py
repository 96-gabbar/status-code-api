import pytest
import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient

module_spec = importlib.util.spec_from_file_location(
    "pagination_api_main", Path(__file__).with_name("main.py")
)
assert module_spec and module_spec.loader
module = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(module)
app = module.app


client = TestClient(app)


def product_ids(response):
    return [product["product_id"] for product in response.json()["items"]]


def test_source_example_page():
    response = client.get("/products?limit=10&offset=20")

    assert response.status_code == 200
    assert product_ids(response) == list(range(21, 31))
    assert response.json()["total"] == 100
    assert response.json()["limit"] == 10
    assert response.json()["offset"] == 20


def test_first_page_uses_defaults():
    response = client.get("/products")

    assert response.status_code == 200
    assert product_ids(response) == list(range(1, 11))
    assert response.json()["total"] == 100
    assert response.json()["limit"] == 10
    assert response.json()["offset"] == 0


def test_last_page_is_partial():
    response = client.get("/products?limit=30&offset=90")

    assert response.status_code == 200
    assert product_ids(response) == list(range(91, 101))


@pytest.mark.parametrize("offset", [100, 110])
def test_offset_at_or_beyond_end_returns_empty_page(offset):
    response = client.get(f"/products?limit=10&offset={offset}")

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 100
    assert response.json()["offset"] == offset


@pytest.mark.parametrize(
    ("query", "field"),
    [
        ("limit=0", "limit"),
        ("limit=-1", "limit"),
        ("limit=10000", "limit"),
        ("offset=-10", "offset"),
    ],
)
def test_invalid_pagination_values_return_422(query, field):
    response = client.get(f"/products?{query}")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
