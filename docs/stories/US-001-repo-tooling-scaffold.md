# US-001 — Repo and tooling scaffold

**Epic:** Foundation

## Story
- **As a** developer on the HR Compliance Dashboard
- **I want** the repo bootstrapped with backend, frontend, Docker, and env configuration
- **So that** every later story can build and run against a consistent, reproducible local environment.

## Acceptance criteria
- **Given** a fresh clone, **when** I run `docker compose up --build` from the project root, **then** both `backend` (FastAPI on :8000) and `frontend` (Nginx on :3000) containers reach a healthy state without errors.
- **Given** the running stack, **when** I open `http://localhost:3000`, **then** the nginx reverse proxy forwards `/api/*` calls to the backend (verified via `/api/v1/health` or equivalent ping returning 200).
- **Given** the repo, **when** I inspect it, **then** `.env.example` exists with all variables from PRD §24 (placeholder values), `.env` is gitignored, and `requirements.txt` matches PRD §23 exactly.
- **Given** the backend container, **when** it starts, **then** it loads env vars via `python-dotenv` / pydantic-settings, fails fast with a clear error if `DATABASE_URL` is missing, and never logs the raw value.

## Dependencies
None (foundation root).

## Estimate
**M** — Standard scaffolding but covers two Dockerfiles, nginx config, env wiring, and verifying the proxy end to end.

## Linked FR-IDs
None directly — supports NFR-001 (zero-dependency startup), NFR-007 (cross-platform Docker), NFR-004 (`.env` not committed).

## Linked entities
None — no DB work yet.

## Infrastructure dependencies
- Docker Desktop ≥ recent.
- `.env` file with `DATABASE_URL` (Supabase connection string from PRD §13).
- Node 20 (image only — local Node not required).
- Python 3.11 (image only).
