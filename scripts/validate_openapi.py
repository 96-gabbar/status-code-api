"""Bounded structural comparison; see evidence/openapi-validation.md for limits."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
ANNOTATIONS = {"title", "description", "examples", "example", "$comment"}
JSONDocument = dict[str, Any]


def resolve(
    document: JSONDocument,
    value: Any,
    trail: tuple[str, ...] = (),
) -> Any:
    """Resolve local JSON pointers; fail explicitly on external/cyclic references."""
    if not isinstance(value, dict) or "$ref" not in value:
        return value
    ref = value["$ref"]
    if not ref.startswith("#/") or ref in trail:
        raise ValueError(f"Unsupported external or cyclic reference: {ref}")
    target = document
    for token in ref[2:].split("/"):
        target = target[token.replace("~1", "/").replace("~0", "~")]
    return {
        **resolve(document, target, (*trail, ref)),
        **{k: v for k, v in value.items() if k != "$ref"},
    }


def schema(
    document: JSONDocument,
    value: Any,
    trail: tuple[str, ...] = (),
) -> Any:
    if isinstance(value, list):
        return [schema(document, item, trail) for item in value]
    if not isinstance(value, dict):
        return value
    if "$ref" in value:
        ref = value["$ref"]
        if ref in trail:
            raise ValueError(f"Unsupported cyclic schema reference: {ref}")
        return schema(document, resolve(document, value), (*trail, ref))
    result: dict[str, Any] = {}
    for key, item in value.items():
        if key in ANNOTATIONS or (key == "nullable" and item is False):
            continue
        if key in {"properties", "$defs", "patternProperties", "dependentSchemas"}:
            result[key] = {name: schema(document, child, trail) for name, child in item.items()}
        else:
            result[key] = schema(document, item, trail)
        if key in {"required", "enum", "type", "anyOf", "oneOf", "allOf"} and isinstance(
            result[key], list
        ):
            result[key] = sorted(result[key], key=lambda x: json.dumps(x, sort_keys=True))
    # Normalize only the common primitive nullable union representation.
    branches = result.get("anyOf")
    if branches and all(isinstance(b, dict) and set(b) == {"type"} for b in branches):
        result.pop("anyOf")
        result["type"] = sorted([b["type"] for b in branches])
    return result


def content(document: JSONDocument, value: dict[str, Any]) -> dict[str, Any]:
    return {
        media: schema(document, item.get("schema", {}))
        for media, item in value.get("content", {}).items()
    }


def operations(document: JSONDocument) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for path, raw in document.get("paths", {}).items():
        item = resolve(document, raw)
        for method in METHODS & item.keys():
            operation = resolve(document, item[method])
            parameters: dict[tuple[str, str], dict[str, Any]] = {}
            for param in item.get("parameters", []) + operation.get("parameters", []):
                param = resolve(document, param)
                parameters[(param["in"], param["name"])] = {
                    "required": param.get("required", False),
                    "deprecated": param.get("deprecated", False),
                    "style": param.get(
                        "style", "form" if param["in"] in {"query", "cookie"} else "simple"
                    ),
                    "explode": param.get("explode", param["in"] in {"query", "cookie"}),
                    "allowReserved": param.get("allowReserved", False),
                    "schema": schema(document, param.get("schema", {})),
                    "content": content(document, param),
                }
            body = resolve(document, operation.get("requestBody", {}))
            result[f"{method.upper()} {path}"] = {
                "parameters": {f"{k[0]}:{k[1]}": v for k, v in sorted(parameters.items())},
                "requestBody": {
                    "present": "requestBody" in operation,
                    "required": body.get("required", False),
                    "content": content(document, body),
                },
                "responses": {
                    str(code): content(document, resolve(document, response))
                    for code, response in operation.get("responses", {}).items()
                },
            }
    return result


def compare(authored: JSONDocument, generated: JSONDocument) -> list[str]:
    """Return actionable differences, with authored values first."""
    left, right = operations(authored), operations(generated)
    differences: list[str] = []

    def walk(a: Any, b: Any, location: str) -> None:
        if isinstance(a, dict) and isinstance(b, dict):
            for key in sorted(a.keys() | b.keys()):
                here = f"{location}/{key}"
                if key not in a:
                    differences.append(f"{here}: missing from authored (generated={b[key]!r})")
                elif key not in b:
                    differences.append(f"{here}: extra in authored (authored={a[key]!r})")
                else:
                    walk(a[key], b[key], here)
        elif a != b:
            differences.append(f"{location}: authored={a!r}; generated={b!r}")

    walk(left, right, "operations")
    return differences


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=ROOT / "openapi.yaml")
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    from app.main import app

    try:
        authored = yaml.safe_load(args.spec.read_text())
        generated = app.openapi()
        differences = compare(authored, generated)
        print(f"Authored operations: {len(operations(authored))}")
        print(f"Generated operations: {len(operations(generated))}")
        print(f"Differences: {len(differences)}")
        for difference in differences:
            print(f"- {difference}")
        return 1 if differences else 0
    except (ValueError, KeyError, TypeError, OSError, yaml.YAMLError) as error:
        print(f"Validation error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
