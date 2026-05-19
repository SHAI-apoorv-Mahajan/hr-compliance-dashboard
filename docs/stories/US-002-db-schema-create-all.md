# US-002 — DB schema via create_all + seed data

**Epic:** Foundation

## Story
- **As a** developer
- **I want** all SQLAlchemy models defined and `Base.metadata.create_all(engine)` plus the seed routine to run on backend startup
- **So that** the database is ready (tables + defaults) the first time the app boots, with zero manual migration steps.

## Acceptance criteria
- **Given** an empty Supabase database, **when** the backend container starts, **then** all 13 tables from PRD §15.2 are created exactly once, with column types, NOT NULL constraints, UNIQUE constraints (`silver_employees.emp_code`, `silver_daily_attendance (emp_code, att_date, upload_id)`, `gold_period_stats (emp_code, period_start, period_end)`, `app_users.email`, `app_flag_thresholds.flag_type`) all present.
- **Given** an already-populated database, **when** the backend restarts, **then** `create_all` completes without raising and no existing data is modified or dropped.
- **Given** a freshly created DB, **when** seed runs, **then** `app_users` has the default HR user (bcrypt-hashed `HR@ShortHills2024`), `app_email_templates` has all 8 templates from PRD §18.3, and `app_flag_thresholds` has all 9 rows from PRD §17 (defaults exactly as listed).
- **Given** a DB where the seed tables are already populated, **when** the backend restarts, **then** seed is a no-op (guarded by `if table.count() == 0`) — no duplicates inserted.
- **Given** a transient seed failure (e.g., Supabase connection blip), **when** the backend continues startup, **then** the error is logged but startup is not aborted (FR-017, NFR-005).

## Dependencies
- US-001 (repo + DB connection string)

## Estimate
**L** — 13 tables, four model files (`bronze.py`, `silver.py`, `gold.py`, `app.py`), `database.py` with `pool_pre_ping=True` and `pool_recycle=300`, plus the idempotent seed.

## Linked FR-IDs
- FR-017 (seed defaults)
- Supports NFR-002 (migration-free schema), NFR-006 (data integrity).

## Linked entities
All 13: `bronze_uploads`, `bronze_greythr_raw`, `bronze_biometric_raw`, `bronze_roster_raw`, `silver_employees`, `silver_leave_transactions`, `silver_daily_attendance`, `gold_period_stats`, `gold_employee_flags`, `app_users`, `app_email_templates`, `app_flag_thresholds`, `app_email_log`.

## Infrastructure dependencies
- `DATABASE_URL` env var.
- Supabase reachable.
- `passlib[bcrypt]` for the seed password hash.
