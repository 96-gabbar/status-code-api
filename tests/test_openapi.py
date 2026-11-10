"""Contract regression plus mutation checks to prevent a vacuous comparator."""

from copy import deepcopy

import pytest
import yaml

from app.main import app
from scripts.validate_openapi import ROOT, compare, resolve, schema


def test_authored_openapi_matches_app():
    authored = yaml.safe_load((ROOT / "openapi.yaml").read_text())
    assert compare(authored, app.openapi()) == []


@pytest.mark.parametrize(
    "change",
    ["operation", "code", "parameter", "request_media", "response_media", "schema", "required"],
)
def test_detects_contract_drift(change):
    baseline = app.openapi()
    changed = deepcopy(baseline)
    collection = changed["paths"]["/api/v1/exceptions"]
    if change == "operation":
        del collection["get"]
    elif change == "code":
        del collection["post"]["responses"]["201"]
    elif change == "parameter":
        collection["get"]["parameters"][0]["required"] = True
    elif change == "request_media":
        collection["post"]["requestBody"]["content"]["text/plain"] = {"schema": {"type": "string"}}
    elif change == "response_media":
        collection["post"]["responses"]["201"]["content"].clear()
    elif change == "schema":
        changed["components"]["schemas"]["CreateExceptionRequest"]["properties"]["description"][
            "maxLength"
        ] = 42
    else:
        collection["post"]["requestBody"]["required"] = False
    assert compare(baseline, changed)
    assert compare(changed, baseline)


def test_path_parameters_are_inherited_and_operation_parameters_override():
    param = {"in": "path", "name": "id", "required": True, "schema": {"type": "string"}}
    inherited = {"paths": {"/{id}": {"parameters": [param], "get": {"responses": {}}}}}
    explicit = deepcopy(inherited)
    item = explicit["paths"]["/{id}"]
    item["get"]["parameters"] = item.pop("parameters")
    assert compare(inherited, explicit) == []
    item["parameters"] = [{**param, "schema": {"type": "integer"}}]
    assert compare(inherited, explicit) == []


def test_normalizes_references_annotations_and_nullable_primitives():
    doc = {"components": {"schemas": {"Value": {"title": "Value", "type": "string"}}}}
    assert schema(doc, {"$ref": "#/components/schemas/Value"}) == {"type": "string"}
    assert schema({}, {"anyOf": [{"type": "string"}, {"type": "null"}]}) == schema(
        {}, {"type": ["string", "null"]}
    )
    assert schema({}, {"properties": {"title": {"type": "string"}}}) == {
        "properties": {"title": {"type": "string"}}
    }


@pytest.mark.parametrize("ref", ["https://example.com/schema", "#/components/schemas/Loop"])
def test_unsupported_references_fail_explicitly(ref):
    doc = {"components": {"schemas": {"Loop": {"$ref": "#/components/schemas/Loop"}}}}
    with pytest.raises(ValueError):
        schema(doc, {"$ref": ref})


def test_json_pointer_escapes():
    assert resolve({"a/b": {"~": {"type": "string"}}}, {"$ref": "#/a~1b/~0"}) == {"type": "string"}
