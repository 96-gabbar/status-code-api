# HTTP semantics notes

## Annotated request-response exchange

Request:

```http
POST /orders HTTP/1.1
Host: api.example.test
Content-Type: application/json

{"instrument":"SYNTH-1","quantity":10}
```

Response:

```http
HTTP/1.1 201 Created
Content-Type: application/json
Location: /orders/ORD-1

{"order_id":"ORD-1","instrument":"SYNTH-1","quantity":10}
```

### Annotation

- Method: `POST` indicates a request to create a subordinate order resource under the `/orders` collection.
- Resource: `/orders` is the collection endpoint; the server creates a new resource whose identifier is returned as `ORD-1`.
- Headers: `Content-Type: application/json` tells the client the request body is JSON. `Location: /orders/ORD-1` tells the client where the newly created resource lives.
- Body: the request body is the creation payload, and the response body is the stored representation of the created order.
- Status: `201 Created` is the correct result because the server created a resource and should communicate that fact explicitly.
- Why not `PUT`? `PUT` would imply replacing the target resource representation at a known identifier, not creating a subordinate resource under a collection. This is creation, not replacement.
- Why `POST` is not guaranteed to be idempotent: repeating the same create request could create a second order if the server accepts it each time. The intended effect is not "same final state after one call as after many calls"; it is to create a new order on each request.

## Method-selection worksheet

| Scenario | Proposed path | Method | Success | Safe? | Idempotent? | Reasoning |
|---|---|---|---:|---|---|---|
| Retrieve order | `/orders/{id}` | `GET` | `200 OK` | Yes | Yes | The client is asking to read a representation; the intended effect is observation only. Retrieving the same order repeatedly does not change the order itself. |
| Create order | `/orders` | `POST` | `201 Created` | No | No | The server is creating a new order resource. Each call creates a new order, so the intended effect differs on repeated requests. |
| Replace order | `/orders/{id}` | `PUT` | `200 OK` or `204 No Content` | No | Yes | `PUT` expresses replacement of the target resource representation. Repeating the same request should leave the resource in the same state as one request. |
| Change order quantity | `/orders/{id}` | `PATCH` | `200 OK` | No | Not guaranteed | `PATCH` means partial update, not full replacement. Whether repeated patching is idempotent depends on the patch semantics and business rules. |
| Cancel order | `/orders/{id}/cancel` | `POST` | `200 OK` or `202 Accepted` | No | Not guaranteed | Cancellation is a business workflow action, not a resource deletion. It changes lifecycle state while preserving the order record. |
| Retrieve portfolio | `/portfolios/{id}` | `GET` | `200 OK` | Yes | Yes | It is a read-only fetch of a portfolio representation. |
| Trigger reconciliation | `/reconciliations` | `POST` | `202 Accepted` or `200 OK` | No | Not guaranteed | This is a workflow action that starts processing, not a read. It can create or schedule work and is not inherently idempotent. |
| Retrieve reconciliation result | `/reconciliations/{id}/result` | `GET` | `200 OK` | Yes | Yes | The client is fetching a result; the operation is read-only. |

### Safety and idempotency

Safe methods communicate "I am asking to observe, not to change state." `GET` is the classic safe method. The server may still write logs, metrics, or cache metadata, but a correctly designed safe route is not a state-changing business operation.

Idempotency is about the intended effect of repeating the same request. `PUT` is idempotent because replacing the same resource with the same representation should leave the resource in the same state after one or many attempts. `DELETE` can also be idempotent in the HTTP sense if the resource is already absent and the server treats that as the same outcome, even though the response status may differ on repeated calls.

### PUT versus PATCH

- `PUT` expresses replacement of the target resource representation.
- `PATCH` expresses a partial modification.
- `PUT` is idempotent by HTTP semantics: sending the same representation multiple times does not keep changing the resource state.
- `PATCH` is not guaranteed to be idempotent; a patch can be idempotent or non-idempotent depending on what it does.

### Business cancellation versus resource deletion

`POST /orders/{id}/cancel` represents a business transition. The order still exists, and its lifecycle changes from active to canceled while preserving history and traceability. That is different from `DELETE /orders/{id}`, which means the resource itself should cease to exist or become inaccessible through that identifier. The API contract must match the real business requirement.
