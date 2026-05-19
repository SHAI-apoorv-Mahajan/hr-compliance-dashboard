# HR Compliance Dashboard

Internal web app that ingests three monthly Excel exports (GreytHR leave, biometric attendance, team roster), runs a Bronze → Silver → Gold medallion pipeline to flag non-compliant employees, and sends templated compliance emails via Microsoft Graph API.

The complete specification is in [docs/PRD.md](docs/PRD.md).

## Quick start

```bash
cp .env.example .env   # then fill in DATABASE_URL, SECRET_KEY, GRAPH_* (optional for v1)
docker compose up --build
```

Open `http://localhost:3000` and log in as `hr@shorthills.ai` / `HR@ShortHills2024` (seeded on first run).

## Documentation map

- [docs/PRD.md](docs/PRD.md) — authoritative spec (FRs, schema, parsers, email, Docker)
- [docs/IDEA-BRIEF.md](docs/IDEA-BRIEF.md) — distilled summary
- [docs/data-model.md](docs/data-model.md) — DB schema and ERD
- [docs/EPICS.md](docs/EPICS.md) — story groupings and recommended vertical slice
- [docs/stories/](docs/stories/) — per-FR user stories with acceptance criteria
- [CLAUDE.md](CLAUDE.md) — entry point for AI-assisted contributors

## Tech stack

React 18 (Vite) · TailwindCSS · React Router v6 · Axios · Recharts
FastAPI · Python 3.11 · SQLAlchemy 2.x · Pydantic v2
PostgreSQL via Supabase (remote) · JWT (python-jose) · bcrypt (passlib)
pandas · openpyxl · httpx · Microsoft Graph API
Docker Compose (backend + frontend only — no local DB container)

## Working with Claude Code

The `.claude/` directory is configuration for [Claude Code](https://claude.com/claude-code). The committed source of truth for `.claude/settings.json` is **`.claude/settings.json.template`**.

During an active Claude Code session, the harness rewrites `.claude/settings.json` with per-session permission approvals — this is expected. To reconcile back to the template before committing:

```bash
make settings        # restores settings.json from the template
```

The pre-commit hook does this automatically. Edit `.claude/settings.json.template` to change project-wide Claude Code config; don't edit `.claude/settings.json` directly.

## Status

Foundation scaffolded. Implementation tracked under `docs/stories/`. See [docs/EPICS.md](docs/EPICS.md) for the recommended vertical slice.
