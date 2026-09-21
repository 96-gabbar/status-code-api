# Week 1 design decisions

- POST is used for assign, resolve, and close because each is a domain command,
  not a CRUD replacement or deletion.
- Input and output schemas are separate so server-owned fields cannot be
  supplied by clients and response exposure remains intentional.
- The repository is in memory for this learning milestone; process restart
  resets synthetic data.
- Stable machine-readable error codes are used for client branching while
  messages remain explanatory.
- Filtering happens before pagination, and `total` reports the filtered count.
- `close` is exposed over HTTP in addition to the pure-Python state machine.
- Persistence, authentication, deployment, external service calls, queues, and
  intentional failure routes are deferred beyond Week 1.
