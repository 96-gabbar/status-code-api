# Week 1 Review

- Tested commit: not applicable (Git initialization is outside this exercise)
- Test date: 2026-09-22
- Python version: 3.9.6
- Actual hours: not yet recorded
- Flagship test cases passed / collected: 44 / 44
- All discovered test cases passed / collected: 84 / 84
- Required operations implemented / 7: 8 including HTTP close
- OpenAPI operations documented / implemented: 8 / 8 method-path operations, plus health
- Request and response contracts documented / required: verified against generated runtime OpenAPI and checked-in `openapi.yaml`
- Operations with error contracts / implemented: 8 / 8 flagship operations include 422/500 and applicable 404/409
- Invalid state-machine cases passed / 9: 9 plus 3 allowed and unknown action
- Mini-artifacts accepted / 5: 5 / 5 implementation artifacts present
- Clean setup and startup: PASS (`uvicorn` + `/health` smoke check)
- Evidence locations: `evidence/test-results.xml`, per-suite JUnit files, this review, pytest output

| Scoring group | Pass / fail | Points | Evidence |
|---|---|---:|---|
| Functional service | PASS | 20/20 | `tests/test_flagship_api.py`, health smoke check |
| Contract completeness | PASS | 20/20 | `openapi.yaml`, generated runtime OpenAPI, `docs/api-design.md` |
| Automated correctness | PASS | 20/20 | 84 tests discovered and passed |
| Learning artifacts | PASS | 20/20 | `exercises/`, Day 1 docs |
| Reproducibility and explanation | PASS | 20/20 | `README.md`, `docs/decisions.md`, health smoke check |

- Total: 100/100
- All mandatory criteria satisfied: YES, except actual focused hours remain unrecorded
- Week complete: YES
- Remaining gaps: record actual focused hours if time accounting is required.
- Most useful design lesson: keep workflow rules independent from HTTP routing and storage.
- What carries into Week 2: replace the repository while preserving contracts and regression tests.
