# Week 1 FDE Transition Specification

**Flagship artifact:** Trade Exception Management API v1  
**Time budget:** 10 focused hours across seven days  
**Stack:** Python, FastAPI, Pydantic, pytest; in-memory storage  
**Program:** FDE Transition → FinOps AI Platform → Investment Operations Copilot  
**Prepared:** 14 September 2026

> Build evidence of capability: **concept → reading → exercise → artifact → measurable acceptance test → portfolio evidence.**

## 1. Source, scope, and implementation decisions

This specification consolidates the Week 1 plan from [Understanding Forward Deployment Roles](chatgpt-conversation://6aa30aba-d348-83e8-bc03-0fb83d270bc9). It preserves the original objective, seven core operations, enums, five mini-artifacts, daily time allocation, completion targets, and Week 2 direction.

The conversation left some implementation details open. This document supplies **implementation clarifications** for field limits, pagination defaults, assignment behavior, resolution storage, error normalization, and scoring. These are proposed contract decisions, not claims that the source specified them. The `close` operation belongs to the required pure-Python state-machine exercise; exposing it over HTTP is an optional extension. A DELETE endpoint was not specified for the flagship service.

The existing 36-week tracker remains the outcome baseline. This file is the tactical Week 1 specification; it does not update that workbook or claim any work has already passed.

### In scope

- [ ] Read and explain HTTP/API fundamentals.
- [ ] Complete five small learning artifacts.
- [ ] Implement a layered FastAPI service using synthetic trade exceptions.
- [ ] Publish explicit request, response, and error contracts in `openapi.yaml`.
- [ ] Test validation, retrieval, filtering, pagination, and business transitions.
- [ ] Deliver reproducible setup instructions and measured completion evidence.

### Deferred

Database persistence, Docker, authentication, Kubernetes, Kafka, LLMs, queues, and deployment are outside Week 1. Use one application process with an in-memory repository. Data resets when the process restarts. All domain data must be synthetic; the platform is a fictional learning system.

## 2. Week 1 objective

By the end of the week, independently implement a clean Python/FastAPI service from a written API contract, demonstrating:

**HTTP semantics → request/response schemas → validation → stable error handling → OpenAPI documentation → automated tests.**

Explain why assignment and resolution are business operations, why input and output schemas differ, and how the repository can later be replaced without rewriting the domain rules.

## 3. Reading materials and concepts

Read the focused sections needed for the next exercise. The links below identify the official/reference materials discussed in the source and focused companion pages; they are a reading list, not a claim of current version verification. Record the versions actually used in the repository.

| Topic | Reading | Concepts to understand | Evidence |
|---|---|---|---|
| HTTP fundamentals | [MDN HTTP overview](https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview) | Client/server, request/response, headers, resources, statelessness | Annotate one complete exchange |
| HTTP methods | [MDN request methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods) | GET, POST, PUT, PATCH, DELETE; safe vs. idempotent | Eight justified method choices |
| Status codes | [MDN response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status) | 200, 201, 204, 400, 404, 409, 422, 500 | Eight runnable examples |
| API contracts | [OpenAPI Specification](https://spec.openapis.org/oas/latest.html) | `paths`, operations, parameters, schemas, responses, examples | Complete `openapi.yaml` |
| FastAPI inputs | [Request body](https://fastapi.tiangolo.com/tutorial/body/), [path parameters](https://fastapi.tiangolo.com/tutorial/path-params/), [query parameters](https://fastapi.tiangolo.com/tutorial/query-params/) | Path/query/body separation, typed request models | Create and list operations |
| FastAPI outputs | [Response models](https://fastapi.tiangolo.com/tutorial/response-model/) | Serialization, output validation, controlled exposure of fields | Explicit response schemas |
| Validation | [Pydantic models](https://docs.pydantic.dev/latest/concepts/models/), [fields](https://docs.pydantic.dev/latest/concepts/fields/), [validators](https://docs.pydantic.dev/latest/concepts/validators/) | Types, enums, constraints, null vs. omitted, validators, extra fields | Validation mini-API and negative tests |
| Testing | [pytest getting started](https://docs.pytest.org/en/stable/getting-started.html), [fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html), [parametrization](https://docs.pytest.org/en/stable/how-to/parametrize.html) | Assertions, isolated fixtures, parameterized cases | Repeatable test suite |
| API testing | [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/) | Test client, response assertions, dependency replacement | Endpoint tests without a running server |

### Concept checklist

- [ ] Explain safe methods and idempotency in terms of effects, not identical response codes.
- [ ] Distinguish replacement with PUT from a partial update with PATCH.
- [ ] Explain why this API uses POST for workflow actions.
- [ ] Distinguish malformed/invalid input, missing resources, and state conflicts.
- [ ] Distinguish an omitted PATCH field from an explicit `null`.
- [ ] Explain why a typed response model is useful even after request validation.
- [ ] Keep HTTP routing, domain rules, and storage responsibilities separate.
- [ ] Explain why `total` is calculated after filtering but before pagination.
- [ ] Express workflow rules independently of FastAPI.
- [ ] Explain how fixtures and parameterization can later support AI evaluations.

## 4. Domain and data model

An investment-operations process discovers exceptions that an operations analyst investigates and resolves. Each exception belongs to a portfolio and transaction. Week 1 validates their identifiers as strings; it does not call another system to verify that those resources exist.

### Enums

| Enum | Allowed values |
|---|---|
| `ExceptionType` | `SETTLEMENT_MISMATCH`, `MISSING_REFERENCE_DATA`, `POSITION_MISMATCH`, `PRICE_VARIANCE`, `CASH_BREAK`, `OTHER` |
| `Severity` | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `Status` | `OPEN`, `INVESTIGATING`, `RESOLVED`, `CLOSED` |

Enum values are case-sensitive. Do not silently convert unknown values to `OTHER`.

### Resource fields

The constraints and optional resolution fields below clarify the source model for implementation.

| Field | Type / constraint | Ownership and behavior |
|---|---|---|
| `exception_id` | String, `EXC-` followed by digits | Server generated; unique during the process lifetime; immutable |
| `portfolio_id` | Trimmed string, 1–64 characters | Required on creation; immutable in v1 |
| `transaction_id` | Trimmed string, 1–64 characters | Required on creation; immutable in v1 |
| `type` | `ExceptionType` | Required on creation; immutable in v1 |
| `severity` | `Severity` | Required on creation; mutable through PATCH |
| `status` | `Status` | Server controlled; initial value `OPEN` |
| `description` | Trimmed string, 1–2,000 characters | Required on creation; mutable through PATCH |
| `assigned_to` | Nullable string, 1–100 characters when set | Initial value `null`; set through assignment |
| `created_at` | UTC RFC 3339 timestamp | Server generated; immutable |
| `updated_at` | UTC RFC 3339 timestamp | Initially equals `created_at`; refreshed on accepted mutation |
| `resolution_code` | Nullable string, 1–100 characters | Initially `null`; stored on resolution |
| `resolution_notes` | Nullable string, 1–2,000 characters | Initially `null`; stored on resolution |

`resolution_code` is a constrained string, not an additional enum: the conversation provided one example, not a complete controlled vocabulary. All response fields are present, including nullable fields. Trim request strings before enforcing length constraints. Reject unknown input fields instead of silently ignoring them. Use separate models:

```text
CreateExceptionRequest
UpdateExceptionRequest
AssignExceptionRequest
ResolveExceptionRequest
ExceptionResponse
ExceptionListResponse
ErrorResponse
HealthResponse
```

### Canonical resource example

```json
{
  "exception_id": "EXC-10001",
  "portfolio_id": "PORT-201",
  "transaction_id": "TXN-918273",
  "type": "SETTLEMENT_MISMATCH",
  "severity": "HIGH",
  "status": "OPEN",
  "description": "Expected settlement amount differs from received amount",
  "assigned_to": null,
  "created_at": "2026-09-13T10:30:00Z",
  "updated_at": "2026-09-13T10:30:00Z",
  "resolution_code": null,
  "resolution_notes": null
}
```

The identifiers and timestamps in examples are illustrative. Tests should assert their format and relationships, not hard-code the clock.

## 5. Shared HTTP and error contract

**Local origin:** `http://127.0.0.1:8000`  
**Resource base path:** `/api/v1/exceptions`  
**Encoding:** JSON request and response bodies use `application/json`.

| Operation | Success | Expected client errors |
|---|---:|---|
| `POST /api/v1/exceptions` | 201 | 422 |
| `GET /api/v1/exceptions/{exception_id}` | 200 | 404, 422 |
| `GET /api/v1/exceptions` | 200 | 422 |
| `PATCH /api/v1/exceptions/{exception_id}` | 200 | 404, 422 |
| `POST /api/v1/exceptions/{exception_id}/assign` | 200 | 404, 409, 422 |
| `POST /api/v1/exceptions/{exception_id}/resolve` | 200 | 404, 409, 422 |
| `GET /health` | 200 | None by design |

All seven operations also document a generic 500 error response. Count method-plus-path operations, not only distinct path strings. There are **seven required operations across six paths**.

### Stable error envelope

```json
{
  "error": {
    "code": "EXCEPTION_NOT_FOUND",
    "message": "Exception EXC-99999 does not exist"
  }
}
```

Clients should branch on `error.code`; `message` is explanatory text. Validation errors may include a `details` array:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "body.severity",
        "message": "Must be one of LOW, MEDIUM, HIGH, CRITICAL"
      }
    ]
  }
}
```

| HTTP status | Error code | Trigger |
|---|---|---|
| 422 | `VALIDATION_ERROR` | Missing/invalid values, extra fields, invalid path/query values, empty PATCH, or malformed JSON in this service |
| 404 | `EXCEPTION_NOT_FOUND` | Well-formed exception identifier is absent |
| 409 | `INVALID_STATE_TRANSITION` | Assignment or resolution is invalid in the current state |
| 500 | `INTERNAL_ERROR` | Unexpected server failure |

```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred"
  }
}
```

Normalize FastAPI request-validation errors and domain errors into this envelope; do not mix it with `{"detail":"not found"}`. Do not expose stack traces in public error bodies. Test a simulated unexpected failure without adding a deliberate crash route to the flagship service.

**Validation order:** Validate path/query/body first (422), then resource existence (404), then workflow preconditions (409). Failed requests must leave stored state unchanged. For path parameters, enforce `^EXC-[0-9]+$`.

## 6. API contracts

### 6.1 Create an exception

```http
POST /api/v1/exceptions
Content-Type: application/json

{
  "portfolio_id": "PORT-201",
  "transaction_id": "TXN-918273",
  "type": "SETTLEMENT_MISMATCH",
  "severity": "HIGH",
  "description": "Expected settlement amount differs from received amount"
}
```

```http
HTTP/1.1 201 Created
Location: /api/v1/exceptions/EXC-10001
Content-Type: application/json

{
  "exception_id": "EXC-10001",
  "portfolio_id": "PORT-201",
  "transaction_id": "TXN-918273",
  "type": "SETTLEMENT_MISMATCH",
  "severity": "HIGH",
  "status": "OPEN",
  "description": "Expected settlement amount differs from received amount",
  "assigned_to": null,
  "created_at": "2026-09-13T10:30:00Z",
  "updated_at": "2026-09-13T10:30:00Z",
  "resolution_code": null,
  "resolution_notes": null
}
```

**Acceptance criteria**

- [ ] All five request fields are required; server-owned fields are rejected with 422.
- [ ] New resource starts `OPEN`, unassigned, and unresolved.
- [ ] Return the full `ExceptionResponse` and a `Location` header.
- [ ] Invalid `severity: "URGENT"` returns the 422 envelope above.
- [ ] Repeated valid POSTs create distinct IDs. Business-key deduplication and idempotency keys are deferred.

### 6.2 Retrieve an exception

```http
GET /api/v1/exceptions/EXC-10001
```

**200 response:** The complete canonical resource from Section 4, reflecting its current stored values.

```http
GET /api/v1/exceptions/EXC-99999
```

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "error": {
    "code": "EXCEPTION_NOT_FOUND",
    "message": "Exception EXC-99999 does not exist"
  }
}
```

**Acceptance criteria**

- [ ] Existing ID returns 200 with all resource fields.
- [ ] Missing ID returns 404; malformed ID returns 422 `VALIDATION_ERROR` with field `path.exception_id`.
- [ ] GET does not change state or timestamps.

### 6.3 List, filter, and paginate

```http
GET /api/v1/exceptions?status=OPEN&severity=HIGH&limit=20&offset=0
```

| Query parameter | Type | Default / rule |
|---|---|---|
| `status` | `Status` | Optional exact match |
| `severity` | `Severity` | Optional exact match |
| `portfolio_id` | String, 1–64 characters | Optional exact match |
| `type` | `ExceptionType` | Optional exact match |
| `limit` | Integer, 1–100 inclusive | 20 |
| `offset` | Integer, ≥0 | 0 |

Combine supplied filters with AND. Sort by `created_at` ascending, then numeric exception-ID suffix ascending to break ties. Calculate `total` after filtering and before slicing. Keep ordering stable across unchanged data; consistency across concurrent mutations is deferred. Reject unsupported query parameter names with 422.

```json
{
  "items": [
    {
      "exception_id": "EXC-10001",
      "portfolio_id": "PORT-201",
      "transaction_id": "TXN-918273",
      "type": "SETTLEMENT_MISMATCH",
      "severity": "HIGH",
      "status": "OPEN",
      "description": "Expected settlement amount differs from received amount",
      "assigned_to": null,
      "created_at": "2026-09-13T10:30:00Z",
      "updated_at": "2026-09-13T10:30:00Z",
      "resolution_code": null,
      "resolution_notes": null
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

No matches is a successful 200:

```json
{"items": [], "total": 0, "limit": 20, "offset": 0}
```

An offset beyond the result count returns an empty list with the actual filtered `total`. It is not a 404.

```http
GET /api/v1/exceptions?limit=0
```

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [{"field": "query.limit", "message": "Must be between 1 and 100"}]
  }
}
```

**Acceptance criteria**

- [ ] Test every filter individually and at least one combined filter.
- [ ] Test defaults, consecutive pages, zero matches, and offset beyond the end.
- [ ] Reject limits 0, -1, and 10000; reject offset -10 and invalid enum values with 422.
- [ ] Every item uses the same `ExceptionResponse` schema as retrieval.

### 6.4 Partially update an exception

```http
PATCH /api/v1/exceptions/EXC-10001
Content-Type: application/json

{
  "severity": "CRITICAL",
  "description": "Updated investigation information"
}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "exception_id": "EXC-10001",
  "portfolio_id": "PORT-201",
  "transaction_id": "TXN-918273",
  "type": "SETTLEMENT_MISMATCH",
  "severity": "CRITICAL",
  "status": "OPEN",
  "description": "Updated investigation information",
  "assigned_to": null,
  "created_at": "2026-09-13T10:30:00Z",
  "updated_at": "2026-09-13T10:40:00Z",
  "resolution_code": null,
  "resolution_notes": null
}
```

**Acceptance criteria**

- [ ] Only `severity` and `description` are accepted; at least one must be supplied.
- [ ] Omitted fields retain their values; explicit `null` is rejected.
- [ ] Reject `exception_id`, `created_at`, `status`, `assigned_to`, and all other extra fields with 422.
- [ ] Example forbidden body `{"status":"RESOLVED"}` returns `VALIDATION_ERROR`, with detail field `body.status`.
- [ ] Missing resource returns the shared 404 envelope.
- [ ] For this learning contract, descriptive edits are permitted in any state; PATCH never performs a workflow transition.

### 6.5 Assign an exception

```http
POST /api/v1/exceptions/EXC-10001/assign
Content-Type: application/json

{"assignee": "ops-user-123"}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "exception_id": "EXC-10001",
  "portfolio_id": "PORT-201",
  "transaction_id": "TXN-918273",
  "type": "SETTLEMENT_MISMATCH",
  "severity": "HIGH",
  "status": "INVESTIGATING",
  "description": "Expected settlement amount differs from received amount",
  "assigned_to": "ops-user-123",
  "created_at": "2026-09-13T10:30:00Z",
  "updated_at": "2026-09-13T10:45:00Z",
  "resolution_code": null,
  "resolution_notes": null
}
```

The example starts from the canonical resource; it is independent of the PATCH example.

**Rule:** Assignment moves `OPEN → INVESTIGATING`. To keep the first state machine explicit, assignment from any other state—including repeated assignment—returns 409. Reassignment is deferred. `assignee` is a trimmed, nonempty string of at most 100 characters; user lookup is deferred.

```json
{
  "error": {
    "code": "INVALID_STATE_TRANSITION",
    "message": "Exception must be OPEN before it can be assigned"
  }
}
```

**Acceptance criteria**

- [ ] Assignment sets `assigned_to`, transitions status, and updates `updated_at` together.
- [ ] Test all four starting states: one success and three conflicts.
- [ ] Missing ID returns 404; `{"assignee":""}` returns 422 `VALIDATION_ERROR` with field `body.assignee`.
- [ ] Rejected assignment preserves the previous state and assignee.

### 6.6 Resolve an exception

```http
POST /api/v1/exceptions/EXC-10001/resolve
Content-Type: application/json

{
  "resolution_code": "REFERENCE_DATA_CORRECTED",
  "resolution_notes": "Security identifier mapping corrected."
}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "exception_id": "EXC-10001",
  "portfolio_id": "PORT-201",
  "transaction_id": "TXN-918273",
  "type": "SETTLEMENT_MISMATCH",
  "severity": "HIGH",
  "status": "RESOLVED",
  "description": "Expected settlement amount differs from received amount",
  "assigned_to": "ops-user-123",
  "created_at": "2026-09-13T10:30:00Z",
  "updated_at": "2026-09-13T11:00:00Z",
  "resolution_code": "REFERENCE_DATA_CORRECTED",
  "resolution_notes": "Security identifier mapping corrected."
}
```

| Starting state | Result |
|---|---|
| `OPEN` | 409; unchanged |
| `INVESTIGATING` | 200; transition to `RESOLVED` |
| `RESOLVED` | 409; unchanged |
| `CLOSED` | 409; unchanged |

```json
{
  "error": {
    "code": "INVALID_STATE_TRANSITION",
    "message": "Exception must be INVESTIGATING before it can be resolved"
  }
}
```

**Acceptance criteria**

- [ ] Both resolution fields are required and follow Section 4 constraints.
- [ ] Store the resolution details, preserve the assignee, and update the timestamp.
- [ ] Test success and all three invalid starting states.
- [ ] Missing ID returns 404; omitted `resolution_notes` returns 422 `VALIDATION_ERROR` with field `body.resolution_notes`.
- [ ] Invalid transitions never overwrite prior resolution details.

### 6.7 Health endpoint

```http
GET /health
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "healthy",
  "service": "trade-exception-service",
  "version": "1.0.0"
}
```

**Acceptance criteria**

- [ ] Exactly the three documented fields are returned with the values above.
- [ ] No authentication or business data is needed.
- [ ] Document the shared 500 error schema for unexpected server failures; no intentional failure route is needed.
- [ ] Treat this as basic process health. Dependency readiness checks belong to the later persistence/deployment work.

## 7. Workflow and business invariants

```text
OPEN --assign--> INVESTIGATING --resolve--> RESOLVED --close--> CLOSED
```

| Current state | `assign` | `resolve` | `close` |
|---|---|---|---|
| `OPEN` | `INVESTIGATING` | Reject | Reject |
| `INVESTIGATING` | Reject | `RESOLVED` | Reject |
| `RESOLVED` | Reject | Reject | `CLOSED` |
| `CLOSED` | Reject | Reject | Reject |

Implement the pure-Python `ExceptionStateMachine` independently of HTTP. Test all **12 state/action combinations: three allowed and nine rejected**, plus at least one unknown action. Domain rejection is translated to HTTP 409 by the API layer. A test fixture may construct `CLOSED` records for API rejection tests.

The flagship HTTP API requires assign and resolve only. The state-machine exercise also requires close. An optional `POST /api/v1/exceptions/{exception_id}/close` extension may accept no body, return the full resource with 200 only from `RESOLVED`, and use the same 404/409/422/500 envelopes. If implemented, include it in all documentation and coverage denominators.

## 8. Project structure and deliverable package

Keep one learning repository. Day 3's `exception-api-v0/` milestone can be a Git tag or commit named `exception-api-v0`; avoid maintaining a duplicate service tree.

```text
trade-exception-service/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── exceptions.py
│   ├── models/
│   │   └── exception.py
│   ├── schemas/
│   │   └── exception.py
│   ├── services/
│   │   ├── exception_service.py
│   │   └── state_machine.py
│   ├── repositories/
│   │   └── exception_repository.py
│   └── errors/
│       └── handlers.py
├── exercises/
│   ├── validation-api/
│   ├── status-code-api/
│   └── pagination-api/
├── tests/
│   ├── conftest.py
│   ├── test_create_exception.py
│   ├── test_get_exception.py
│   ├── test_list_exceptions.py
│   ├── test_update_exception.py
│   ├── test_exception_workflow.py
│   ├── test_state_machine.py
│   └── test_health.py
├── docs/
│   ├── http-semantics.md
│   ├── status-codes.md
│   ├── api-design.md
│   ├── decisions.md
│   └── week-1-review.md
├── evidence/
│   └── test-results.xml
├── openapi.yaml
├── requirements.txt
├── README.md
└── pyproject.toml
```

Add package initialization files as needed. Each exercise includes runnable source and its own tests. A one-file mini-API is sufficient for an exercise; the flagship uses the layered structure.

| Layer | Responsibility |
|---|---|
| API | HTTP parameters, request/response models, status codes |
| Schemas | Public input/output validation and serialization |
| Models | Internal domain representation |
| Service | Workflow rules and orchestration |
| Repository | In-memory storage and retrieval |
| Error handlers | Stable public error mapping |

## 9. Five mini-artifacts

Allocate roughly 20–45 minutes to each. They are focused rehearsals; reuse what you learn in the flagship without turning them into additional production services.

### A. HTTP semantics worksheet

**Deliverable:** `docs/http-semantics.md` with eight rows containing operation, path, method, expected success status, safe/idempotent classification, and reasoning.

| Scenario | Suggested contract to evaluate |
|---|---|
| Retrieve order | `GET /orders/{id}` |
| Create order | `POST /orders` |
| Replace order | `PUT /orders/{id}` |
| Change order quantity | `PATCH /orders/{id}` |
| Cancel order | `POST /orders/{id}/cancel` |
| Retrieve portfolio | `GET /portfolios/{id}` |
| Trigger reconciliation | `POST /reconciliations` |
| Retrieve reconciliation result | `GET /reconciliations/{id}/result` |

**Acceptance:** **8/8 decisions with written reasoning.** Explain why business cancellation is distinct from deleting a resource, and when DELETE would fit a different requirement. Discuss GET as safe/idempotent, PUT and DELETE as idempotent in intended effects, and POST/PATCH as not guaranteed idempotent. Do not assume repeating DELETE must return the same status.

### B. Request validation API

**Deliverable:** `exercises/validation-api/`, exposing `POST /users`.

| Field | Rule |
|---|---|
| `name` | Trimmed string, 2–100 characters |
| `email` | Valid email address using a validation library |
| `age` | Integer, ≥18; reject booleans and fractional values |
| `country` | String of exactly two characters; country-code membership is not required |

```http
POST /users
Content-Type: application/json

{"name":"Asha Rao","email":"asha@example.com","age":18,"country":"IN"}
```

Clarified success contract: 201 with a generated `user_id` and validated fields.

```json
{"user_id":"USR-1","name":"Asha Rao","email":"asha@example.com","age":18,"country":"IN"}
```

Invalid input returns 422 with the shared `VALIDATION_ERROR` envelope. Do not perform email delivery or external verification.

**Acceptance:** At least **five valid and ten invalid requests**, all tested. Include exact length boundaries, invalid email, underage user, non-integer age, country length, missing field, and unknown field. Record the actual 15+ cases and outcomes.

### C. Status-code exercise

**Deliverables:** `exercises/status-code-api/` and `docs/status-codes.md`.

| Status | Example scenario in the isolated exercise |
|---:|---|
| 200 | `GET /examples/item`: return an existing item |
| 201 | `POST /examples/items`: create an item and return its location |
| 204 | `DELETE /examples/items/1`: delete an existing fixture item; return no body |
| 400 | `POST /examples/commands` with `{"command":"UNSUPPORTED"}`: reject unsupported command syntax under the exercise contract |
| 404 | `GET /examples/items/999`: missing item |
| 409 | `POST /examples/closed-item/resolve`: conflicting workflow state |
| 422 | `POST /examples/users` with invalid age: schema validation failure |
| 500 | `GET /examples/internal-error`: controlled simulated server failure |

**Acceptance:** **8/8 runnable status examples**, one assertion per example, and a written explanation of each code. Verify the 204 response body is empty. Keep deliberate 500 generation confined to this exercise. Explain the chosen 400/422 distinction; the flagship normalizes invalid request parsing/validation to 422.

### D. Pagination API

**Deliverable:** `exercises/pagination-api/`, exposing `GET /products` over **100 synthetic products**.

Use deterministic product IDs 1–100, sorted ascending. Product schema: `product_id` (integer) and `name` (string). Default `limit=10`, `offset=0`; enforce limit 1–100 and offset ≥0.

```http
GET /products?limit=2&offset=20
```

```json
{
  "items": [
    {"product_id": 21, "name": "Product 21"},
    {"product_id": 22, "name": "Product 22"}
  ],
  "total": 100,
  "limit": 2,
  "offset": 20
}
```

**Acceptance:** Verify the source example `limit=10&offset=20` returns IDs 21–30. Test first page, last partial page, offset 100, and all four required invalid boundaries: `limit=0`, `limit=-1`, `limit=10000`, `offset=-10`. Invalid values return 422; beyond-end offsets return 200 with empty items and `total: 100`.

### E. Pure-Python state machine

**Deliverables:** `app/services/state_machine.py` and `tests/test_state_machine.py`.

```python
class ExceptionStateMachine:
    def transition(self, current_status: Status, action: str) -> Status:
        """Return the next status or raise a domain transition error."""
```

**Acceptance:** Cover all 12 cells in Section 7 and an unknown action. Keep HTTP objects and repository access out of this class. Use the same transition rules inside the flagship service.

## 10. Exact seven-day schedule

The original daily allocation totals **10 hours**. The subdivisions below fit all five exercises into that allocation. Day 3 is an exploratory implementation against this written spec; Day 4 freezes the complete OpenAPI contract before completing v1.

| Day | Time | Exact allocation | End-of-day artifact |
|---|---:|---|---|
| 1 | 1.5h | 30m HTTP reading; 30m worksheet A; 30m status exercise C | `docs/http-semantics.md`, status exercise and explanations |
| 2 | 1.5h | 30m Python/Pydantic reading; 45m validation exercise B; 15m scaffold | Validation mini-API with 5 valid + 10 invalid cases; repository structure |
| 3 | 1.5h | 20m FastAPI inputs/outputs; 25m pagination exercise D; 45m create/get/list/PATCH prototype | Pagination exercise; `exception-api-v0` milestone |
| 4 | 1.5h | 20m OpenAPI reading; 50m complete contracts; 20m compare prototype against contracts | `openapi.yaml`, `docs/api-design.md` |
| 5 | 1.5h | 20m pytest fixtures/parameterization; 55m endpoint and error tests; 15m fixes | API tests and initial measured results |
| 6 | 2h | 30m state-machine exercise E; 60m workflow integration and health; 30m tests and fixes | Trade Exception API v1; complete transition coverage |
| 7 | 0.5h | 10m design decisions; 10m clean setup smoke check; 10m score and review | README, `docs/decisions.md`, `docs/week-1-review.md`, evidence |
| **Total** | **10h** | | |

This is a timebox, not proof that all targets will fit. If work exceeds it, record actual hours and carry unfinished acceptance criteria forward; do not mark incomplete work Done. Full Week 1 completion is determined by evidence below.

## 11. Definition of Done and quantified evidence

### Original Week 1 targets

| Requirement | Target | How to measure |
|---|---:|---|
| API operations implemented | ≥7 | Count working method/path pairs from Section 5 |
| Automated tests | ≥25 | Collect at least 25 meaningful flagship test cases; exercise-only tests do not substitute |
| Tests passing | 100% | Zero failing, skipped, or expected-failure required cases |
| API paths documented in OpenAPI | 100% | All six core paths and seven operations present |
| Request schemas documented | 100% | All four request-body models plus every path/query parameter |
| Response schemas documented | 100% | Resource, list, health, and applicable error responses |
| Public API operations with error contracts | 100% | Every operation documents applicable errors, including generic 500 |
| Invalid workflow transitions tested | ≥5 | Required matrix is stronger: nine invalid pure-domain cases, plus API mapping cases |
| README setup and examples | Yes | Reproducible commands and sample workflow |
| Starts from clean clone | Yes | Fresh directory/environment; documented startup and smoke test succeed |

The five mini-artifacts must also satisfy their stated acceptance criteria. Use parameterized cases when each asserts a distinct behavior; do not inflate test counts with duplicate assertions. Run the flagship and all exercise suites.

### Five-test scoring rubric

The source specifies five 20-point acceptance tests per tracker week and a completion threshold of ≥90/100, but does not supply an exact grouping for the detailed Week 1 checklist. This proposed mapping preserves that scoring convention. Each group earns **20 only when every condition in it passes**, otherwise 0.

| Group | 20-point acceptance test | Required evidence |
|---|---|---|
| 1. Functional service | All seven operations work; valid create → get/list → PATCH → assign → resolve flow and health check pass | Endpoint tests and sample calls |
| 2. Contract completeness | 100% of implemented paths, requests, responses, and applicable errors documented; examples match implementation | `openapi.yaml`, API design notes, contract review checklist |
| 3. Automated correctness | ≥25 flagship cases; all required suites pass; ≥5 invalid transitions covered, with complete required matrix | Test report and counts by suite |
| 4. Learning artifacts | All five mini-artifacts meet their quantified criteria | Worksheet, three mini-APIs, state machine, associated tests |
| 5. Reproducibility and explanation | Clean setup/start succeeds; README has setup/examples; design decisions and review are complete | README, fresh setup record, decisions, weekly review |

```text
weekly_score = 20 × number_of_passed_groups
week_complete = weekly_score >= 90 AND all required checklist items are satisfied
```

With binary 20-point groups, possible scores are 0, 20, 40, 60, 80, and 100. Therefore **≥90 effectively requires 100/100**. This makes the arithmetic explicit instead of inventing partial credit.

### Suggested flagship test distribution

| Area | Minimum suggested cases |
|---|---:|
| Create: success, required field, invalid enum, forbidden field | 4 |
| Get: existing, missing, malformed ID | 3 |
| List: filters, combined filters, pages, boundaries | 10 |
| PATCH: partial update, null, immutable field, empty body, missing ID | 5 |
| Workflow HTTP behavior: successes, six invalid states, missing/invalid inputs | 10 |
| State machine: 12 combinations plus unknown action | 13 |
| Health and generic error envelope | 2 |
| **Suggested total** | **47** |

The ≥25 source target is a floor; passing the full behavioral contract may require more cases. Assert failed mutations preserve stored values and use a fresh repository fixture per test.

### Delivery checklist

- [ ] One repository contains the flagship and all five mini-artifacts.
- [ ] `openapi.yaml` is checked in and agrees with runtime behavior.
- [ ] README states the tested Python version and dependency installation commands.
- [ ] Dependencies include everything needed for testing and email validation.
- [ ] README includes start command, health call, create/list/update/assign/resolve examples, and test command.
- [ ] README states that storage is in memory and resets on restart.
- [ ] Tests run without external services or credentials.
- [ ] `docs/decisions.md` explains POST actions, separate schemas, error design, pagination, and deferred features.
- [ ] `docs/week-1-review.md` records actual hours, each target, actual result, evidence location, score, and remaining gaps.
- [ ] Evidence identifies the tested commit and test date; no unmeasured metric is marked passed.

Example commands to document and verify in the eventual repository:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

In a second terminal after activating the environment:

```bash
curl -i http://127.0.0.1:8000/health
python -m pytest --junitxml=evidence/test-results.xml
```

Ensure the evidence directory exists and document exercise test commands or configure test discovery to include them. These are instructions for the Week 1 implementation, not execution results accompanying this specification.

## 12. Other relevant API domains

These are options for subsequent practice, not additional Week 1 deliverables.

| API domain | Example operations | Concepts | FDE relevance |
|---|---|---|---|
| Trade Exception | Create, filter, assign, resolve | Workflow and business invariants | Very high |
| Portfolio | Create portfolio, add/list positions, summarize | Hierarchical resources and aggregation | Very high |
| Entitlements | Grant/revoke access, check permission | Authorization and resource scope | Very high |
| Workflow Approval | Submit, approve, reject, list history | State machines and audit history | Very high |
| Reconciliation | Start run, poll status, fetch breaks | Async jobs and result contracts | Very high |
| Document Registry | Register metadata, search, retrieve | Metadata and later RAG ingestion | Very high |
| Client/KYC Case | Open case, validate, request information | Case workflow and validation | High |
| Order | Create, retrieve, update, cancel | CRUD and HTTP fundamentals | Moderate |
| Incident | Report, assign, escalate, resolve | Severity, events, ownership | High |
| Job Execution | Submit, inspect, cancel | Async processing and lifecycle | Very high |
| Notification | Enqueue, inspect delivery, retry | Queues and retry behavior | High |
| Feature Flag | Create flag, update config, read version | Configuration and versioning | Moderate |
| API Key Management | Issue, list metadata, revoke | Security and credential lifecycle | High |
| Model Evaluation | Start evaluation, retrieve metrics | Evaluation datasets and AI infrastructure | Very high |

## 13. Evolving FinOps AI Platform architecture

Here, “FinOps” means the fictional financial-operations platform from the conversation. The platform gradually supports an **Investment Operations Copilot** that investigates trade exceptions using structured APIs and retrieved procedures.

```text
                            FinOps AI Platform
                                  |
                             API Gateway
                     +------------+------------+
                     |            |            |
                 Portfolio    Exception     Document
                  Service      Service       Service
                     |            |            |
                 PostgreSQL   PostgreSQL   Vector Store

                       Reconciliation Service
                                  |
                                Queue
                                  |
                            Worker Service
                                  |
                          AI Investigator
                         /        |        \
                 Portfolio    Exception    Documents
                    API          API          RAG
```

This is a conceptual evolution, not a Week 1 deployment diagram. Week 1 implements only the Exception Service with in-memory storage. Later service boundaries and invocation paths should be justified by the workflow as it develops.

| Stage | Addition | How Week 1 contributes |
|---|---|---|
| Week 1 | Contracted Exception Service | Typed inputs/outputs, errors, workflow rules, tests |
| Week 2 | Persistence, packaging, integration foundations | Replace repository while preserving external behavior |
| Later early weeks | Documents, retrieval, tool calling, job handling | Reuse API contracts as dependable interfaces |
| Weeks 13–24 | Investment Operations Copilot | Investigate exceptions using portfolios, transactions, procedures, and tools |
| Later portfolio/interview work | Evaluation evidence, deployment story, case study | Explain decisions and demonstrate measured outcomes |

Future cross-cutting work includes permissions, auditability, observability, failure handling, evaluation, and human review. These are architectural destinations, not hidden additions to Week 1 scope.

## 14. Week 2 and later-week connections

### Week 2: evolve the same service

```text
In-memory repository
    → PostgreSQL
    → SQLAlchemy
    → Alembic migrations
    → Docker
    → Configuration
    → Structured logging
    → Integration tests
    → CI
```

Carry the Week 1 contract and regression tests forward. Add persistence-specific tests, document any deliberate contract change, and reuse the repository boundary to contain storage changes.

The conversation also proposes a second service:

```http
POST /portfolios
GET  /portfolios/{id}
GET  /portfolios
POST /portfolios/{id}/positions
GET  /portfolios/{id}/positions
GET  /portfolios/{id}/summary
```

These are a Week 2 direction, not complete contracts in this file. Define their schemas and errors before implementation. When Exception Service calls Portfolio Service, practice timeouts, retries, failure mapping, versioning, idempotency, and eventual consistency. Do not blindly retry mutations.

### Later weeks: use the APIs as AI tools

- **Retrieval foundation:** The source tracker describes Week 6's cited RAG assistant with ≥95% valid citations, Recall@5 ≥80%, correctness ≥80%, ≥30 evaluated questions, and ≥3 successful deployed health checks. Week 1 supplies the habits of explicit contracts and measurable tests.
- **Copilot build, Weeks 13–24:** Combine structured portfolio/exception data with procedures and documents to investigate operational breaks and route uncertain cases for human review.
- **Week 19 evaluation evidence:** The source names a package of ≥100 golden investigation cases. Isolated fixtures and parameterized testing learned now support that later work.
- **Week 24 portfolio evidence:** The source calls for a sanitized public repository, demo video, case study, and evaluation results. Preserve readable decisions and reproducible setup from the beginning.
- **Week 29 interview evidence:** The source targets five complete FDE case interviews with an average score ≥80. Practice explaining why your contract fits the user's workflow and how you measured correctness.

The full 36-week workbook was not attached to the referenced conversation retrieval. These later milestones are drawn from the conversation's descriptions, not independently checked spreadsheet contents.

## 15. Weekly review template

Copy this into `docs/week-1-review.md` when implementing the plan.

```markdown
# Week 1 Review

- Tested commit:
- Test date:
- Actual hours:
- Flagship test cases passed / collected:
- Exercise test cases passed / collected:
- Required operations implemented / 7:
- OpenAPI operations documented / implemented:
- Request and response contracts documented / required:
- Operations with error contracts / implemented:
- Invalid state-machine cases passed / 9:
- Mini-artifacts accepted / 5:
- Clean setup and startup: PASS / FAIL
- Evidence locations:

| Scoring group | Pass / fail | Points | Evidence |
|---|---|---:|---|
| Functional service | | /20 | |
| Contract completeness | | /20 | |
| Automated correctness | | /20 | |
| Learning artifacts | | /20 | |
| Reproducibility and explanation | | /20 | |

- Total: /100
- All mandatory criteria satisfied: YES / NO
- Week complete: YES / NO
- Remaining gaps:
- Most useful design lesson:
- What carries into Week 2:
```

**The delivered outcome is a working, specified, tested service and its learning evidence—not simply time spent reading FastAPI documentation.**
