# HR Compliance Dashboard

Internal web app for ShortHills Tech HR that ingests three monthly Excel exports (GreytHR leave, biometric attendance, team roster), runs a Bronze → Silver → Gold medallion pipeline to flag non-compliant employees against 9 configurable thresholds, and sends templated compliance emails via Microsoft Graph API. The complete spec is `docs/PRD.md` (do not summarize it — it is authoritative).

## Build and test

```bash
# First-run boot (zero-dependency — only Docker Desktop required, PRD §23)
docker compose up --build

# Backend tests
cd backend && pytest -q

# Frontend tests
cd frontend && npm test

# Format
cd backend && black .
cd frontend && npx prettier --write src/
```

App URLs once running:
- Frontend: `http://localhost:3000`
- Backend (via nginx proxy): `http://localhost:3000/api/v1/...`
- Backend direct (for debugging only): `http://localhost:8000`

## Coding standards

- **No Alembic.** Schema is managed by `Base.metadata.create_all(engine)` on startup (PRD NFR-002).
- **Pipeline writes are idempotent.** Re-running for the same period must not duplicate gold rows (PRD FR-008, FR-009).
- **PRD §27 quirks must be preserved verbatim** — Excel serial dates, U+00BD (½), the typo column `"Intime window onpen till"`, NS-shift permanent-WFH absences are not flagged.
- **Errors return `{"detail": "..."}` only.** No Python stack traces in API responses (PRD NFR-005). Missing Graph env vars → HTTP 503 with the exact body from FR-014, never HTTP 500.
- **`.env` is never committed.** `block-secret-writes` hook enforces this; `Read(./.env*)` is in `settings.json` deny.
- **Pages never call axios directly** — all API calls go through `frontend/src/api/`. Use the `/api/v1` relative path so nginx proxying works.

## Workflow

1. Start every task by reading the relevant story under `docs/stories/US-NNN-*.md` and the `src/<area>/CLAUDE.md` for the layer you're touching.
2. Foundation stories (US-001 … US-004) must be complete before any feature story starts.
3. Run tests after every change. Do not claim done with red tests.
4. Pre-merge: use the `review-pr` skill — it dispatches code-reviewer + security-reviewer in parallel.
5. New product scope goes through the `new-feature` skill (PRD amendment + new FR/story before code).

## Memory layout

| Where | What |
|---|---|
| `CLAUDE.md` (this file) | Project overview, build commands, top-level standards |
| `docs/PRD.md` | Authoritative spec — FRs, schema, parsers, email, Docker, env |
| `docs/IDEA-BRIEF.md` | Distilled summary of the PRD |
| `docs/data-model.md` | DB schema + ERD + migration strategy (mirrors PRD §15) |
| `docs/architecture.md` | Runtime topology, module map, sequence diagrams |
| `docs/EPICS.md` | Story groupings + recommended vertical slice |
| `docs/stories/US-NNN-*.md` | One user story per FR + foundation stories |
| `docs/decisions/ADR-NNN-*.md` | Architecture decision records (ADR-001: no Alembic, no local DB) |
| `.claude/rules/code-style.md` | Python + JS style, naming, comments |
| `.claude/rules/testing.md` | pytest / vitest conventions and required coverage |
| `.claude/rules/security.md` | Secrets, auth, error handling, CORS |
| `.claude/rules/api-design.md` | Routes, status codes, schemas, idempotency |
| `src/api/CLAUDE.md` | FastAPI routers, Pydantic schemas, DI |
| `src/persistence/CLAUDE.md` | SQLAlchemy models, engine, sessions, unique keys |
| `src/services/CLAUDE.md` | Parsers, pipeline, flag engine, email service |
| `src/ui/CLAUDE.md` | React pages, components, axios layer, AuthContext |
| `.claude/agents/*.md` | 11 specialist agents (PM, architect, eng, QA, reviewers, devops, error-log) |
| `.claude/skills/*/SKILL.md` | 7 skills (new-feature, implement-story, review-pr, refactor, release, post-mortem, data-migration) |
| `CLAUDE.local.md` | Personal notes — gitignored |
| `.claude/agent-memory-local/error-log/MEMORY.md` | Error log — gitignored, created on first failure |
