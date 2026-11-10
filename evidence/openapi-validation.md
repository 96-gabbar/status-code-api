# OpenAPI validation — 6 November 2026

Implemented `scripts/validate_openapi.py` and `tests/test_openapi.py` against the authored root `openapi.yaml` and fresh `app.main:app.openapi()` output. The script can be invoked from any working directory; `--spec` selects an alternative authored file. Exit codes: 0 match, 1 differences, 2 unsupported references or input errors.

## Actual results

Run from `/Users/ashutosh/projects/status-code-api` using the existing `.venv-verify` environment:

```text
.venv-verify/bin/python scripts/validate_openapi.py
Authored operations: 8
Generated operations: 8
Differences: 0

.venv-verify/bin/python -m pytest -q --junitxml=evidence/openapi-full-test-results.xml
97 passed in 0.56s
```

Full captured output is in `openapi-validator.txt` and `openapi-pytest.txt`; the full-suite JUnit report is `openapi-full-test-results.xml`. No dependency installation was necessary.

The first comparison found 87 structural difference entries (repeated use of shared schemas multiplies entries), despite all eight operations and their response-code sets already matching. Three causes were fixed:

- Authored optional status, severity, portfolio and type query schemas omitted the null alternatives present in generated OpenAPI. Added those alternatives to YAML.
- Authored error details described arbitrary non-null objects. Updated YAML to describe the generated nullable array of objects with required `field` and `message` strings.
- Generated path parameters lacked the authored exception ID pattern. Added `Annotated`/`Path` schema metadata on the five existing handlers. Existing manual ID validation and handler bodies remain intact; the added pattern is documentation metadata, not a new validation path.

Existing edits to `requirements.txt`, the existing `.venv-verify` directory and `evidence/generated-openapi.json` were preserved. The generated snapshot is not used as a test oracle.

## Checks and explicit limits

- Compares exact method/path sets and response-code sets; includes only the eight OpenAPI HTTP operation keys, ignoring path-item metadata.
- Compares effective path-level and operation-level parameters keyed by location/name, with operation overrides; checks requiredness, deprecation, style, explode, allowReserved, schema and media content.
- Compares request-body presence, requiredness, media-type sets and schemas; compares each response's media-type set and schemas.
- Resolves local JSON Pointer references, including pointer escaping, in parameters, bodies, responses and nested schemas. External and cyclic references fail explicitly rather than being silently skipped.
- Recursively compares schema structure, including types, properties, required fields, enums, constraints, defaults, arrays, additionalProperties and compositions. Ignores title, description, examples, example and $comment annotations; preserves identically named property fields. Sorts required/enum/type/composition arrays and normalizes primitive anyOf nullable unions to type lists. Treats `nullable: false` as redundant.
- This is a bounded structural comparison, not a complete OpenAPI validator or proof of JSON Schema semantic equivalence. More complex equivalent compositions can produce differences. Only schemas reachable through operation parameters, request bodies and response content are covered; unused components are not checked.
- Does not compare document info, operation IDs, summaries, tags, security, servers, response headers, links, callbacks, webhooks, encoding or examples. Does not prove runtime payload compliance, custom validators, string trimming, unknown-query rejection or actual response-code behavior. Existing API tests exercise runtime behavior separately.
- Mutation tests confirm drift detection for operations, codes, parameters, required bodies, request/response media types and nested schema constraints in both directions. Additional tests cover inherited parameter overrides, reference resolution, annotations, nullable primitive normalization, escaped pointers and rejected external/cyclic references.
