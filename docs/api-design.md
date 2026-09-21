# Trade Exception API design

The flagship service exposes exceptions as resources under
`/api/v1/exceptions`. Creation uses `POST`; assignment, resolution, and
closure are business actions because they apply workflow transitions while
preserving the exception resource and its history. PATCH is limited to
descriptive fields and never changes workflow state.

Public request schemas are separate from response schemas. Clients cannot set
server-owned identifiers, timestamps, status, assignment, or resolution
fields. Responses expose the complete canonical representation, including
nullable fields.

The repository is an in-memory boundary. The service layer owns workflow and
mutation rules, so storage can later be replaced without changing the HTTP
contract. List filters are combined with AND, sorted by creation time and
numeric ID, and counted before offset/limit slicing.

All request, path, and query validation failures use `422 VALIDATION_ERROR`.
Missing well-formed IDs use `404 EXCEPTION_NOT_FOUND`; invalid workflow
actions use `409 INVALID_STATE_TRANSITION`. Unexpected failures use a safe
`500 INTERNAL_ERROR` response without implementation details.

The HTTP close operation is included as an explicit extension of the required
state-machine exercise: only `RESOLVED -> CLOSED` is accepted.
