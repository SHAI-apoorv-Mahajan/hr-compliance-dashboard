# US-004 — End-to-end smoke test

**Epic:** Foundation

## Story
- **As a** developer
- **I want** an automated smoke test that boots the backend, talks to the real DB, exercises one protected route, and proves the React shell loads
- **So that** any future regression in the foundation layer is caught before feature work proceeds.

## Acceptance criteria
- **Given** the backend container started, **when** the smoke test runs, **then** it can connect to Supabase, confirm at least one row exists in `app_flag_thresholds` (proving seed ran), and exits 0.
- **Given** the backend, **when** the smoke test posts valid credentials to `/api/v1/auth/login` and uses the returned token to call `/api/v1/auth/me`, **then** both responses are HTTP 200 with the expected JSON shape.
- **Given** the frontend, **when** I open `http://localhost:3000/login`, **then** the login form renders with email and password fields, the JWT-protected `/dashboard` redirects to `/login` if no token is in `localStorage`, and after a successful API login the app navigates to `/dashboard` (which may render a placeholder until US-013 lands).
- **Given** `pytest` runs in `backend/`, **when** the foundation tests run, **then** at least one test covers: model imports, `create_all` idempotency on a test DB (or transactional cleanup), and password verification round-trip.

## Dependencies
- US-001, US-002, US-003

## Estimate
**S** — Wiring + one happy-path test per layer, no new business logic.

## Linked FR-IDs
None directly — guard rail for FR-001 and FR-017.

## Linked entities
- `app_users`, `app_flag_thresholds`

## Infrastructure dependencies
- `pytest`, `httpx` (already in requirements via FastAPI's TestClient).
- A reachable Supabase instance or a configured test schema.
