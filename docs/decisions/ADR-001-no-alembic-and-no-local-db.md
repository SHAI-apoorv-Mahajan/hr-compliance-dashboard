# ADR-001 — No Alembic, no local DB container

- **Status:** Accepted (codified by PRD §9, §13, NFR-001, NFR-002, NFR-007). This ADR records the rationale.
- **Date:** 2026-05-15
- **Deciders:** product + tech lead (single HR admin product; no DBA in v1)

## Context

The HR Compliance Dashboard is an internal tool for a single non-technical HR user. The primary success metric is "first-run `docker compose up --build` works 100% of the time on macOS, Linux, and Windows" (PRD NFR-001, success metric #4). Previous internal projects at ShortHills Tech with similar shapes have failed first-run for two recurring reasons:

1. A local Postgres container that never starts cleanly cross-platform (volume permissions on Windows, port collisions on macOS, version drift on Linux).
2. Alembic migrations that worked on the author's machine but failed elsewhere — out-of-order revision IDs, missing autogenerate diffs, or "table already exists" on re-runs.

Two technical options were considered for each problem.

### Schema management

**Option A — SQLAlchemy `Base.metadata.create_all(engine)` on startup.** Idempotent. No revision files. Schema changes ship by deploying a new image with updated models.

**Option B — Alembic with autogenerate.** Industry-standard. Supports versioned forward/backward migrations. Has tooling for diffing models against DB state.

### Database hosting

**Option C — Local Postgres container in compose.** Standard. Self-contained "works offline" dev setup.

**Option D — Remote Supabase managed Postgres.** Eliminates the container. Trade DB latency for setup simplicity.

## Decision

**Option A + Option D.** Schema via `create_all`. Database via remote Supabase.

`Base.metadata.create_all(engine)` runs on FastAPI startup (PRD §25). The operation is idempotent — tables are created if absent, untouched if present. Seed runs immediately after, guarded by `if table.count() == 0`.

Supabase is reachable from the developer's machine, the CI runner, and the production deploy with identical credentials. There is **no `db:` service** in `docker-compose.yml`.

## Consequences

**Positive**

- First-run success rate is structurally maximized: no container ordering, no `wait-for-it.sh`, no volume permission surprises (NFR-001).
- Cross-platform parity is trivial — there is no host-mounted Postgres data directory to misbehave on Windows (NFR-007).
- No migration files to maintain. No "the migration ran but the app code is from a different branch" class of bug.
- DB schema is authored in one place — the SQLAlchemy models — and is automatically consistent with the ORM.
- Restarting the backend never modifies existing data (NFR-002 idempotency).

**Negative**

- No automatic downgrade path. Removing a column or changing its type requires either a one-off migration script (use the `data-migration` skill) or accepting that the column stays until the next clean reset.
- No DB schema versioning. There is no `alembic_version` table to inspect.
- Dropping a table or renaming a column **does not happen automatically** — `create_all` only adds. This is recorded in [data-model.md](../data-model.md) under "Migration strategy."
- Supabase is a single point of failure for the whole stack. If Supabase is down, the dev loop is blocked. (Acceptable for an internal monthly-batch tool; would not be acceptable for a real-time customer-facing service.)
- All developers and CI runners need network access to Supabase. There is no offline mode.

**Neutral / accepted trade-offs**

- We will write occasional one-off backfill scripts (`backend/scripts/migrate_YYYYMMDD_*.py`) for non-trivial data shape changes. The `data-migration` skill (`.claude/skills/data-migration/SKILL.md`) governs how those are written, tested, and run.
- If the project ever needs versioned migrations (e.g., when more than one developer is editing the schema concurrently), the migration path is: add Alembic, generate an initial baseline from the current models, then opt-in to autogenerate. Until then, `create_all` is sufficient.
- Local-only experimentation against the schema is possible by pointing `DATABASE_URL` at a developer's own Supabase project — no code change needed.

## Reversal

This decision is reversible. The migration path back to Alembic is well-known. If the constraints that drove this decision change — e.g., we add a second persistent developer who needs versioned schema review — we revisit then. Adding a local DB container is similarly reversible.

This ADR exists so that decision is taken with eyes open, not because the original was forgotten.
