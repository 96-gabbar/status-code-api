# Day 1 Specification: HTTP Semantics and Status Codes

**Learning path:** FDE Transition, Week 1  
**Day:** 1 of 7  
**Planned session length:** 90 minutes; use as a pacing guide, not a time-tracking requirement  
**Source:** [`week-1-fde-transition-specification.md`](./week-1-fde-transition-specification.md)  
**Primary outcome:** Explain and demonstrate deliberate HTTP method and status-code choices.

> Day 1 is successful when the reasoning is explicit and the examples are runnable. The learner will manage time separately; completion is based on evidence rather than elapsed time.

## 1. Purpose

Day 1 builds the HTTP foundation required for the Trade Exception Management API. The work should make it possible to answer these questions without relying on framework defaults:

1. What resource or business operation does an endpoint represent?
2. Which HTTP method best expresses that operation?
3. Is the operation safe or idempotent, and what do those properties mean?
4. Which success or error status accurately describes the outcome?
5. What should the client receive in the response body and headers?
6. How should malformed input, missing resources, and workflow conflicts differ?

The emphasis is on observable API behavior. Framework implementation details are secondary today.

## 2. Scope

### In scope

- Read focused HTTP material covering requests, responses, methods, and status codes.
- Annotate one complete request-response exchange.
- Complete the eight-scenario HTTP semantics worksheet.
- Build an isolated FastAPI exercise demonstrating eight status codes.
- Write at least one automated assertion for every example.
- Explain the design choices in plain language.
- Record test results and unfinished work. The learner will calculate time separately.

### Out of scope

- The Trade Exception Management API itself.
- The Week 1 layered application structure.
- The validation mini-API planned for Day 2.
- OpenAPI authoring, planned for Day 4.
- Authentication, persistence, Docker, deployment, and external services.
- Production-grade logging or observability.
- Creating an intentional failure route in the future flagship service.

## 3. Deliverables

Day 1 produces the following artifacts:

```text
docs/
├── http-semantics.md
└── status-codes.md
exercises/
└── status-code-api/
    ├── main.py
    ├── requirements.txt
    └── test_main.py
```

This is intentionally smaller than the final Week 1 repository structure. The broader scaffold remains a Day 2 task.

### Deliverable A: `docs/http-semantics.md`

The document must contain:

- One annotated HTTP request-response exchange.
- An eight-row method-selection worksheet.
- A short explanation of safe methods.
- A short explanation of idempotency in terms of intended server effects.
- A comparison of PUT and PATCH.
- An explanation of business cancellation versus resource deletion.

### Deliverable B: `exercises/status-code-api/`

A small FastAPI application must expose eight runnable outcomes: 200, 201, 204, 400, 404, 409, 422, and 500.

The exercise may use a single source file. It is a learning artifact, not the architecture template for the flagship API.

### Deliverable C: `docs/status-codes.md`

The document must explain:

- What each demonstrated status means.
- Why each endpoint returns that status.
- What a client should do with the outcome.
- Why this exercise distinguishes 400 from 422.
- Why the flagship API will later normalize request parsing and validation failures to 422.

### Exercise file responsibilities

| File | Responsibility |
|---|---|
| `exercises/status-code-api/main.py` | FastAPI application, request models, fixture state, endpoint handlers, and public error handlers |
| `exercises/status-code-api/test_main.py` | Black-box HTTP assertions using FastAPI's `TestClient` |
| `exercises/status-code-api/requirements.txt` | Exact direct dependency versions used for the exercise |
| `docs/status-codes.md` | Explanation of each observed response and its client meaning |

### Local setup

The agreed environment is a repository-local `.venv`; Git initialization is outside Day 1.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r exercises/status-code-api/requirements.txt
```

The exercise currently uses these direct dependencies:

```text
fastapi==0.128.8
httpx==0.28.1
pytest==8.4.2
```

FastAPI installs Pydantic and Starlette transitively. HTTPX is required by `TestClient`, and pytest runs the automated checks.

### Incremental implementation workflow

Use a small red–green cycle for each status code:

1. Add one test expressing the external HTTP contract.
2. Run the suite and confirm that the new test fails for the expected reason.
3. Implement only enough endpoint behavior to satisfy that contract.
4. Run the full exercise suite and confirm that existing behavior still passes.
5. Complete the corresponding explanation in `docs/status-codes.md`.

Implement the cases in this order:

1. 200 existing item
2. 201 item creation and `Location`
3. 204 deletion with a truly empty body
4. 404 missing item
5. 400 unsupported command
6. 409 invalid workflow state
7. 422 request validation and normalized error output
8. 500 unexpected failure with a safe public response

This order begins with straightforward success behavior, then adds in-memory state and client errors, and leaves global validation and exception handlers until their purpose is visible.

## 4. Working agreements and assumptions

The following defaults remove decisions that do not contribute much to Day 1 learning:

- Use Python, FastAPI, Pydantic, pytest, and FastAPI's `TestClient`.
- Use only synthetic, in-memory data.
- Keep the status-code exercise independent from the future flagship API.
- Invoke its tests from inside `exercises/status-code-api/` so the hyphenated deliverable directory does not need to be an importable Python package.
- Use JSON for request and non-empty response bodies.
- Use a consistent JSON error envelope where a response body is appropriate.
- Use exact, deterministic fixture IDs so the tests are easy to understand.
- Do not initialize Git as part of Day 1 unless explicitly chosen later.
- Complete the worksheet independently before reviewing an answer key or receiving corrections.
- Use the 90-minute schedule as a pacing guide only; do not require time tracking in the Day 1 artifacts.

## 5. Suggested 90-minute execution plan

The intervals below organize the work but are not a reporting requirement. The learner will calculate time separately, and unfinished acceptance criteria remain unfinished regardless of the suggested duration.

### Block 1 — HTTP reading and annotation (00:00–00:30)

#### 00:00–00:05 — Establish the mental model

Write a two- or three-sentence description of:

- A client sending a request to a server.
- A server returning a response.
- HTTP being stateless: each request must carry the context needed to understand it, unless application state is addressed separately through identifiers, credentials, or other mechanisms.

#### 00:05–00:15 — Study method semantics

Read the focused sections in:

- [MDN HTTP overview](https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview)
- [MDN HTTP request methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods)

Capture notes on:

- GET, POST, PUT, PATCH, and DELETE.
- The difference between reading a resource and requesting a business action.
- Safe methods: the client is not asking the server to change application state.
- Idempotent methods: repeating the same request has the same intended effect as making it once.

Do not define idempotency as “the response is identical.” A repeated DELETE may leave the resource deleted while returning a different status on the second request.

#### 00:15–00:23 — Study status-code families

Read the relevant entries in:

- [MDN HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)

Focus only on 200, 201, 204, 400, 404, 409, 422, and 500. For each, record:

- What happened.
- Whether a response body is expected for this exercise.
- Whether the client can reasonably change its next request.

#### 00:23–00:30 — Annotate one exchange

Add one full exchange to `docs/http-semantics.md`. Recommended example:

```http
POST /orders HTTP/1.1
Host: api.example.test
Content-Type: application/json

{"instrument":"SYNTH-1","quantity":10}
```

```http
HTTP/1.1 201 Created
Content-Type: application/json
Location: /orders/ORD-1

{"order_id":"ORD-1","instrument":"SYNTH-1","quantity":10}
```

Annotate the method, resource, headers, body, status, and `Location` header. Explain why this is creation rather than replacement and why POST is not guaranteed to be idempotent.

### Block 2 — HTTP semantics worksheet (00:30–01:00)

Create `docs/http-semantics.md` with this table shape:

| Scenario | Proposed path | Method | Success | Safe? | Idempotent? | Reasoning |
|---|---|---|---:|---|---|---|
| Retrieve order | `/orders/{id}` | | | | | |
| Create order | `/orders` | | | | | |
| Replace order | `/orders/{id}` | | | | | |
| Change order quantity | `/orders/{id}` | | | | | |
| Cancel order | `/orders/{id}/cancel` | | | | | |
| Retrieve portfolio | `/portfolios/{id}` | | | | | |
| Trigger reconciliation | `/reconciliations` | | | | | |
| Retrieve reconciliation result | `/reconciliations/{id}/result` | | | | | |

#### Design questions to answer for every row

1. Is the endpoint retrieving information, creating a resource, replacing a representation, partially updating it, or invoking a domain action?
2. What is the intended server-side effect?
3. Would repeating the request change that intended effect?
4. What is the most precise success status?
5. If the endpoint creates a resource, should it return a `Location` header?

#### Required discussion: PUT versus PATCH

The worksheet must state that:

- PUT expresses replacement of the target resource representation.
- PATCH expresses a partial modification.
- PUT is idempotent by HTTP semantics.
- PATCH is not guaranteed to be idempotent; whether a particular patch behaves idempotently depends on its semantics.

#### Required discussion: cancellation versus deletion

`POST /orders/{id}/cancel` represents a business transition. It preserves the order and its history while changing its lifecycle state. DELETE would fit a different requirement in which the resource itself should cease to exist or become inaccessible through that resource identifier.

#### Worksheet acceptance check

- Exactly eight scenarios are evaluated.
- Every method and success status is justified.
- Every row explicitly classifies safety and idempotency.
- Reasoning discusses effects rather than merely repeating method definitions.
- No claim is made that repeated idempotent requests must return identical bodies or statuses.

Complete the worksheet before consulting an answer key. After the first attempt, review every row against the design discussions in this specification and record corrections separately so the original reasoning remains visible.

### Block 3 — Runnable status-code exercise (01:00–01:30)

Build the smallest implementation that demonstrates the following contracts.

#### Shared response conventions

Success responses containing data use JSON. Error responses use:

```json
{
  "error": {
    "code": "STABLE_MACHINE_CODE",
    "message": "Human-readable explanation"
  }
}
```

The error codes in this exercise should remain stable even if explanatory messages are edited.

#### 200 OK — retrieve an existing item

```http
GET /examples/item
```

Expected response:

```json
{"item_id":1,"name":"Example item"}
```

Test: status is 200 and the complete JSON body matches.

#### 201 Created — create an item

```http
POST /examples/items
Content-Type: application/json

{"name":"New item"}
```

Expected behavior:

- Return 201.
- Return the created representation with a deterministic generated ID.
- Return `Location: /examples/items/{id}`.

Test the status, body, and `Location` header.

#### 204 No Content — delete an existing fixture item

```http
DELETE /examples/items/1
```

Expected behavior:

- Return 204.
- Return no response body.

Test `response.content == b""`; do not accept `{}`, `null`, or a success message.

Reset the in-memory fixture between tests so test order does not affect the result.

#### 400 Bad Request — unsupported command syntax

```http
POST /examples/commands
Content-Type: application/json

{"command":"UNSUPPORTED"}
```

Expected response code: `UNSUPPORTED_COMMAND`.

Design decision: the request is valid JSON and has the expected field shape, but the command language defined by this isolated endpoint does not recognize the supplied instruction. This exercise intentionally classifies that command-level problem as 400.

#### 404 Not Found — retrieve a missing item

```http
GET /examples/items/999
```

Expected response code: `ITEM_NOT_FOUND`.

The identifier is well formed; the corresponding resource is absent.

#### 409 Conflict — reject an invalid workflow action

```http
POST /examples/closed-item/resolve
```

Expected response code: `INVALID_STATE_TRANSITION`.

The request is understandable, but resolving an already closed item conflicts with its current state.

#### 422 Unprocessable Content — schema validation failure

```http
POST /examples/users
Content-Type: application/json

{"age":17}
```

Expected response code: `VALIDATION_ERROR`.

Define a request schema requiring an integer age of at least 18. Normalize FastAPI/Pydantic validation output into the exercise's error envelope. Assert both the 422 status and the stable `VALIDATION_ERROR` response code.

#### 500 Internal Server Error — controlled unexpected failure

```http
GET /examples/internal-error
```

Expected response:

```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred"
  }
}
```

Keep this route only in the isolated exercise. Add a generic exception handler that avoids exposing exception messages or stack traces in the response.

When testing with FastAPI's `TestClient`, construct the client with `raise_server_exceptions=False`; otherwise the controlled exception may be raised into the test instead of being returned as a 500 response.

## 6. Test design

At least eight distinct test cases are required—one per demonstrated status. Prefer descriptive test names:

```text
test_get_existing_item_returns_200
test_create_item_returns_201_and_location
test_delete_existing_item_returns_empty_204
test_unsupported_command_returns_400
test_missing_item_returns_404
test_invalid_transition_returns_409
test_invalid_user_returns_422
test_unexpected_failure_returns_safe_500
```

### Isolation rules

- Each test receives fresh application state or resets the in-memory fixture.
- Tests must pass in any order.
- No test makes a network call or requires a separately running server.
- Assertions should cover observable behavior, not private implementation details.
- The 500 test must assert that internal exception details are absent.

### Suggested command

Run from the exercise directory:

```bash
python -m pytest -q
```

Record the exact command and result in the Day 1 completion record.

## 7. Design discussions to capture

### 7.1 Safe does not mean cacheable or side-effect-free implementation

A safe method communicates that the client is requesting observation rather than a state change. Servers may still log requests or update operational metrics. Those incidental effects do not turn a correctly designed GET into a state-changing business operation.

### 7.2 Idempotency is about intended effect

If replacing an order twice with the same PUT representation leaves the order in the same state as replacing it once, the intended effect is idempotent. Response timestamps, audit records, or status codes may still differ.

### 7.3 POST can represent creation or an action

POST is suitable both for creating a subordinate resource and invoking a domain command such as cancel, assign, or resolve. The path and documentation must make the intended semantics clear.

### 7.4 400 versus 422

For this exercise:

- 400 demonstrates a deliberately defined command-syntax failure.
- 422 demonstrates structural or field validation failure.

This boundary is an API contract choice and must be applied consistently. The Week 1 flagship contract later simplifies client behavior by mapping malformed JSON and request-validation problems to 422.

### 7.5 404 versus 409

- Use 404 when a well-formed identifier does not select an existing resource.
- Use 409 when the target exists but its current state prevents the requested operation.

### 7.6 500 must not expose internals

A 500 response signals an unexpected server failure. Public output should remain stable and safe. Debugging details belong in server-side diagnostics, not the client response.

## 8. Definition of Done

Day 1 is complete only when all of the following are true:

### Reading and reasoning

- [ ] One complete HTTP exchange is annotated.
- [ ] The worksheet contains 8/8 method decisions with written reasoning.
- [ ] All eight rows classify safety and idempotency.
- [ ] PUT replacement and PATCH partial update are distinguished.
- [ ] Business cancellation and resource deletion are distinguished.
- [ ] Idempotency is explained in terms of intended effects.

### Runnable exercise

- [ ] All eight required status examples are implemented.
- [ ] Each example has at least one automated assertion.
- [ ] The 201 response includes a `Location` header.
- [ ] The 204 response body is exactly empty.
- [ ] The 400/422 distinction is documented.
- [ ] The 500 response hides internal exception details.
- [ ] Tests do not depend on execution order or external services.
- [ ] All required tests pass with no skips or expected failures.

### Evidence

- [ ] `docs/http-semantics.md` exists.
- [ ] `docs/status-codes.md` exists.
- [ ] `exercises/status-code-api/` is runnable.
- [ ] The test command and result are recorded.
- [ ] Any incomplete criterion is explicitly carried forward.

## 9. Completion record

Fill this in at the end of the session:

```text
Date:
Reading completed:
Worksheet decisions completed: __ / 8
Runnable status examples: __ / 8
Tests passed: __ / __
Tests failed: __
Tests skipped or xfailed: __
Commands run:
Artifacts created:
Open questions:
Work carried forward:
```

## 10. Confirmed working decisions

1. **Learning mode:** Complete the worksheet independently, then review the answers and reasoning. Corrections should be recorded without erasing the initial attempt.
2. **Time handling:** The learner will calculate time separately. The suggested 90-minute breakdown is a pacing guide and is not part of the required evidence.
3. **Environment setup:** Use a local `.venv` and a minimal dependency list.
4. **Version control:** Leave Git initialization outside Day 1.

## 11. Day 1 exit statement

At completion, be able to say:

> I can select HTTP methods and status codes based on resource semantics and workflow outcomes, explain safety and idempotency in terms of effects, and prove those decisions with eight runnable FastAPI examples and automated tests.
