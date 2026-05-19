# src/persistence — SQLAlchemy models, engine, session

Maps to `backend/models/` and `backend/database.py` (PRD §22).

## Hard rules
- **No Alembic.** Schema is managed by `Base.metadata.create_all(engine)` on startup. No migration files. The operation is idempotent.
- **UUID PKs** default via Python `uuid.uuid4` — never DB-level `gen_random_uuid()`.
- **`pool_pre_ping=True`** and **`pool_recycle=300`** on the engine. Supabase's pooler drops idle connections; without these, we crash on the next query (PRD §13).
- **SQLAlchemy 2.x style only.** `Mapped[T]`, `mapped_column(...)`. No legacy `Column()`.
- **Unique constraints (do not drop):**
  - `silver_employees.emp_code`
  - `silver_daily_attendance (emp_code, att_date, upload_id)`
  - `gold_period_stats (emp_code, period_start, period_end)`
  - `app_users.email`
  - `app_flag_thresholds.flag_type`

## Files
- `backend/models/bronze.py` — `bronze_uploads`, `bronze_greythr_raw`, `bronze_biometric_raw`, `bronze_roster_raw`.
- `backend/models/silver.py` — `silver_employees`, `silver_leave_transactions`, `silver_daily_attendance`.
- `backend/models/gold.py` — `gold_period_stats`, `gold_employee_flags`.
- `backend/models/app.py` — `app_users`, `app_email_templates`, `app_flag_thresholds`, `app_email_log`.
- `backend/database.py` — engine, `SessionLocal`, `Base`, `get_db()` generator.
- `backend/seed.py` — idempotent seed (default user, 8 templates, 9 thresholds; guarded by `count == 0`).

## Sessions
- Routers get a session via `get_db()` (yield + finally close).
- Services receive the session as a parameter — they never build their own.
- One transaction per request. Commit at the end of the router handler, rollback on exception.

## What never goes here
- Business logic — that lives in `src/services/`.
- Pydantic schemas — those live in `src/api/`.
- Raw SQL — use SQLAlchemy ORM or `text()` with bound parameters. Never string-format SQL.
