"""Validate the authored Portfolio v1 contract and generated FastAPI contract."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.validate_openapi import compare, operations  # noqa: E402

SPEC = ROOT / "portfolio-openapi.yaml"
EXPECTED_OPERATIONS = {
    "GET /health": {"200", "500"},
    "GET /api/v1/portfolios": {"200", "422", "500"},
    "POST /api/v1/portfolios": {"201", "409", "422", "500"},
    "GET /api/v1/portfolios/{portfolio_id}": {"200", "404", "422", "500"},
    "PATCH /api/v1/portfolios/{portfolio_id}": {"200", "404", "422", "500"},
}


def validate(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    actual = operations(document)
    if set(actual) != set(EXPECTED_OPERATIONS):
        errors.append(
            f"operation set mismatch: expected={sorted(EXPECTED_OPERATIONS)} actual={sorted(actual)}"
        )
    for name, expected_codes in EXPECTED_OPERATIONS.items():
        if name not in actual:
            continue
        actual_codes = set(actual[name]["responses"])
        if actual_codes != expected_codes:
            errors.append(
                f"{name} response codes: expected={sorted(expected_codes)} actual={sorted(actual_codes)}"
            )

    schemas = document.get("components", {}).get("schemas", {})
    for name in (
        "CreatePortfolioRequest",
        "UpdatePortfolioRequest",
        "PortfolioResponse",
        "PortfolioListResponse",
        "HealthResponse",
        "ErrorResponse",
    ):
        if name not in schemas:
            errors.append(f"missing schema: {name}")

    examples = document.get("components", {}).get("examples", {})
    if "Portfolio" not in examples:
        errors.append("missing Portfolio example")

    collection = actual.get("GET /api/v1/portfolios", {})
    expected_params = {"query:limit", "query:offset", "query:owner", "query:status"}
    actual_params = set(collection.get("parameters", {}))
    if actual_params != expected_params:
        errors.append(
            f"list parameters: expected={sorted(expected_params)} actual={sorted(actual_params)}"
        )
    return errors


def main() -> int:
    try:
        document = yaml.safe_load(SPEC.read_text())
        errors = validate(document)
        from portfolio_app.main import app

        generated = app.openapi()
        differences = compare(document, generated)
        print(f"Authored operations: {len(operations(document))}")
        print(f"Generated operations: {len(operations(generated))}")
        print(f"Contract errors: {len(errors)}")
        for error in errors:
            print(f"- {error}")
        print(f"Generated differences: {len(differences)}")
        for difference in differences:
            print(f"- {difference}")
        return 1 if errors or differences else 0
    except (ValueError, KeyError, TypeError, OSError, yaml.YAMLError) as error:
        print(f"Validation error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
