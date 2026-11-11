from copy import deepcopy

import yaml

from scripts.validate_openapi import ROOT, operations
from scripts.validate_portfolio_openapi import EXPECTED_OPERATIONS, validate


def authored_contract():
    return yaml.safe_load((ROOT / "portfolio-openapi.yaml").read_text())


def test_portfolio_contract_has_expected_operations_codes_and_limits():
    document = authored_contract()
    assert validate(document) == []
    assert set(operations(document)) == set(EXPECTED_OPERATIONS)


def test_portfolio_contract_defines_patch_as_nonempty_and_strict():
    schema = authored_contract()["components"]["schemas"]["UpdatePortfolioRequest"]
    assert schema["minProperties"] == 1
    assert schema["additionalProperties"] is False
    assert set(schema["properties"]) == {"name", "owner", "status"}


def test_portfolio_contract_defines_deterministic_pagination():
    document = authored_contract()
    params = document["components"]["parameters"]
    assert params["Limit"]["schema"] == {
        "type": "integer",
        "minimum": 1,
        "maximum": 100,
        "default": 20,
    }
    assert params["Offset"]["schema"] == {
        "type": "integer",
        "minimum": 0,
        "default": 0,
    }
    description = document["paths"]["/api/v1/portfolios"]["get"]["description"]
    assert "created_at descending" in description
    assert "before pagination" in description


def test_portfolio_validator_detects_operation_and_response_drift():
    baseline = authored_contract()
    missing_operation = deepcopy(baseline)
    del missing_operation["paths"]["/api/v1/portfolios/{portfolio_id}"]["patch"]
    assert validate(missing_operation)

    missing_response = deepcopy(baseline)
    del missing_response["paths"]["/api/v1/portfolios"]["post"]["responses"]["409"]
    assert validate(missing_response)
