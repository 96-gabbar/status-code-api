# Status-code explanations

This exercise is intentionally small and explicit. Each route demonstrates one HTTP outcome so the meaning of the code and the client action are easy to see.

## 200 OK — retrieve an existing item

- Route: `GET /examples/item`
- Meaning: the item exists and the server returned its current representation.
- Client action: the client can trust the body as the latest known state and render or reuse it.
- Why this status: the request is read-only and the resource exists.

## 201 Created — create an item

- Route: `POST /examples/items`
- Meaning: the server created a new resource and the representation is included in the response body.
- Client action: the client should treat the response as the created resource and follow the `Location` header to find the resource URI.
- Why this status: creation is a successful state change that produced a new resource.

## 204 No Content — delete an existing item

- Route: `DELETE /examples/items/1`
- Meaning: the server successfully processed the deletion request and deliberately returns no body.
- Client action: the client should treat the delete as successful and not expect a JSON payload.
- Why this status: the resource is gone and the response intentionally communicates success without a document body.

## 400 Bad Request — unsupported command syntax

- Route: `POST /examples/commands`
- Meaning: the request was syntactically valid JSON with the expected shape, but the command language defined by this endpoint does not accept the supplied value.
- Client action: correct the command or choose a recognized action.
- Why this status: this route defines a command vocabulary, and the request violates that vocabulary even though it is well-formed JSON.

## 404 Not Found — missing item

- Route: `GET /examples/items/999`
- Meaning: the identifier is well formed, but there is no matching resource.
- Client action: check whether the resource exists, whether the identifier is correct, or whether the client needs to create it.
- Why this status: the request is valid, but the target resource does not exist.

## 409 Conflict — invalid workflow action

- Route: `POST /examples/closed-item/resolve`
- Meaning: the resource exists, but its current lifecycle state prevents the requested operation.
- Client action: inspect the resource state, retry only after the state changes, or present a user-friendly workflow message.
- Why this status: the request is understandable and the resource is present, but the state transition is invalid.

## 422 Unprocessable Content — schema validation failure

- Route: `POST /examples/users` with `{"age":17}`
- Meaning: the request body is structurally valid JSON, but it violates the required schema constraint (`age >= 18`).
- Client action: fix the invalid field before retrying.
- Why this status: the request is well-typed enough to reach validation, but the field value is not allowed.
- Why this differs from 400: in this exercise, 400 is reserved for a command vocabulary problem, while 422 is for validation of a recognized request shape. The boundary is an explicit API contract choice.
- Why the flagship API will later normalize to 422: a later production API should treat malformed request data and field-level validation issues consistently as 422, rather than mixing them into broader bad-request semantics.

## 500 Internal Server Error — unexpected failure

- Route: `GET /examples/internal-error`
- Meaning: an unhandled server error occurred and the public response must remain safe.
- Client action: treat it as a temporary server-side issue and do not rely on the internal details being exposed.
- Why this status: an internal failure is unexpected and not caused by malformed client input.
- Why the response hides internals: application exceptions, stack traces, and implementation details should stay in server logs, not in a public API response.

## Why the exercise distinguishes 400 and 422

This exercise intentionally separates two different classes of client error:

- `400 Bad Request` means the request is valid enough to parse, but the endpoint-defined command or operation is unsupported.
- `422 Unprocessable Content` means the request has a recognized schema, but a required constraint is violated.

That distinction helps the client make better decisions. A command mismatch is usually a business-action or API-contract issue. A schema violation is a data-quality issue.

## Why the flagship API will later normalize to 422

A future API should prefer a consistent validation model in which request parsing and field validation failures are surfaced as 422. That makes the client behavior more predictable and keeps the API contract easier to explain. Here, the learning app demonstrates the distinction in a small, isolated form before the wider production API adds richer validation rules.
