# Testing

## Backend (pytest)
- Tests live under `tests/` mirroring `backend/` structure.
- Use `httpx.AsyncClient` or `fastapi.testclient.TestClient`. Never start the production server during tests.
- One unit test file per parser, one per pipeline stage, one per router.
- Parser tests use small synthetic `.xlsx` fixtures stored under `tests/fixtures/`. Do not commit real GreytHR or biometric exports.
- The biometric parser must have explicit tests for: the `"Emp Code:"` marker row, the next-row header skip, the `"Total Duration="` end marker, the U+00BD half-present character, and trailing-space `status` values (PRD §27 quirks #2, #3, #4).
- Pipeline idempotency tests: run the pipeline twice on the same input and assert no duplicate rows in `silver_daily_attendance`, `gold_period_stats`, `gold_employee_flags`.

## Frontend (vitest + React Testing Library)
- One test file per page, one per shared component.
- Mock axios at the `src/api/` layer — never mock raw fetch.
- Cover: render, happy-path interaction, and the 401-on-protected-route redirect.

## What every PR must include
- A test that fails on the previous commit and passes on this one (TDD-style proof of change).
- For bug fixes: a regression test reproducing the original bug.

## What we do NOT test
- Third-party library internals (SQLAlchemy, Pydantic).
- Microsoft Graph API itself — only our request construction and response handling, with `httpx.MockTransport`.
