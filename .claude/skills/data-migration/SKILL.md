---
name: data-migration
description: Use when a schema change has been merged in docs/data-model.md and you need to migrate existing Supabase data. NEVER auto-invoked. This project does not use Alembic; schema additions are idempotent via create_all, but data backfills sometimes need a one-off script.
disable-model-invocation: true
---

# data-migration

## When to use
- A new column has been added to a silver or gold table and existing rows need a backfill value.
- A new flag type has been added — existing periods may need re-evaluation.
- A column has been renamed in a model and the underlying Supabase column still has the old name.

## Steps
1. **Read the delta.** Diff `docs/data-model.md` since the last release. Identify the precise schema change.
2. **Write a one-off script** under `backend/scripts/migrate_YYYYMMDD_<slug>.py`. The script must:
   - Be **idempotent** — running twice produces the same result.
   - Use a single transaction per logical step.
   - Log row counts before and after.
   - Have a `--dry-run` flag that does everything except `commit()`.
3. **Test on a Supabase branch** (or local schema copy) before touching production.
4. **Run with `--dry-run` first** in production, capture the planned changes, then run for real.
5. **Update CHANGELOG.md** with a "Migration:" entry naming the script.

## Hard rules
- Never use `DROP TABLE` or `DROP COLUMN` without an explicit user "yes, drop it". Schema additions only by default.
- Never modify `bronze_*` tables in a migration — bronze is append-only audit data.
- Never run a migration that takes a lock for > 10 seconds during business hours without coordination.
- Never bypass `pool_pre_ping` — use the same engine configuration the app uses.
