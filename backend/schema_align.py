"""Idempotent column-width widener for existing Supabase databases.

`create_all` does not ALTER existing columns. Real-world Excel data has values
longer than the conservative VARCHAR sizes originally chosen, so we widen the
relevant text columns to TEXT here on startup.

Safe to re-run: every ALTER is wrapped in try/except per statement; PostgreSQL
silently no-ops a TYPE change when source and target are already equivalent.
Only runs against PostgreSQL.
"""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.engine import Engine

log = logging.getLogger(__name__)


# (table, column) → target type. PRD-defined sizes that real data exceeds.
WIDENINGS: list[tuple[str, str, str]] = [
    ("bronze_uploads", "original_filename", "TEXT"),
    ("bronze_greythr_raw", "employee_no", "VARCHAR(40)"),
    ("bronze_greythr_raw", "name", "TEXT"),
    ("bronze_greythr_raw", "manager_no", "VARCHAR(40)"),
    ("bronze_greythr_raw", "manager_name", "TEXT"),
    ("bronze_greythr_raw", "leave_type", "TEXT"),
    ("bronze_greythr_raw", "transaction_type", "TEXT"),
    ("bronze_greythr_raw", "days", "NUMERIC(6,2)"),
    ("bronze_biometric_raw", "emp_code", "VARCHAR(40)"),
    ("bronze_biometric_raw", "employee_name", "TEXT"),
    ("bronze_biometric_raw", "in_time", "VARCHAR(20)"),
    ("bronze_biometric_raw", "out_time", "VARCHAR(20)"),
    ("bronze_biometric_raw", "shift", "TEXT"),
    ("bronze_biometric_raw", "scheduled_in_time", "VARCHAR(20)"),
    ("bronze_biometric_raw", "scheduled_out_time", "VARCHAR(20)"),
    ("bronze_biometric_raw", "status", "TEXT"),
    ("bronze_roster_raw", "name", "TEXT"),
    ("bronze_roster_raw", "project", "TEXT"),
    ("bronze_roster_raw", "client", "TEXT"),
    ("bronze_roster_raw", "in_team_role", "TEXT"),
    ("bronze_roster_raw", "billing_status", "TEXT"),
    ("bronze_roster_raw", "working_model", "TEXT"),
    ("bronze_roster_raw", "monday", "VARCHAR(20)"),
    ("bronze_roster_raw", "tuesday", "VARCHAR(20)"),
    ("bronze_roster_raw", "wednesday", "VARCHAR(20)"),
    ("bronze_roster_raw", "thursday", "VARCHAR(20)"),
    ("bronze_roster_raw", "friday", "VARCHAR(20)"),
    ("bronze_roster_raw", "saturday", "VARCHAR(20)"),
    ("bronze_roster_raw", "sunday", "VARCHAR(20)"),
    ("bronze_roster_raw", "intime_window", "TEXT"),
    ("bronze_roster_raw", "shift_time_day", "TEXT"),
    ("bronze_roster_raw", "shift_time_night", "TEXT"),
    ("silver_employees", "emp_code", "VARCHAR(40)"),
    ("silver_employees", "name", "TEXT"),
    ("silver_employees", "email", "VARCHAR(255)"),
    ("silver_employees", "project", "TEXT"),
    ("silver_employees", "client", "TEXT"),
    ("silver_employees", "in_team_role", "TEXT"),
    ("silver_employees", "billing_status", "TEXT"),
    ("silver_employees", "working_model", "TEXT"),
    ("silver_employees", "shift_time_day", "TEXT"),
    ("silver_employees", "shift_time_night", "TEXT"),
    ("silver_employees", "schedule_monday", "VARCHAR(20)"),
    ("silver_employees", "schedule_tuesday", "VARCHAR(20)"),
    ("silver_employees", "schedule_wednesday", "VARCHAR(20)"),
    ("silver_employees", "schedule_thursday", "VARCHAR(20)"),
    ("silver_employees", "schedule_friday", "VARCHAR(20)"),
    ("silver_employees", "schedule_saturday", "VARCHAR(20)"),
    ("silver_employees", "schedule_sunday", "VARCHAR(20)"),
    ("silver_leave_transactions", "emp_code", "VARCHAR(40)"),
    ("silver_leave_transactions", "employee_name", "TEXT"),
    ("silver_leave_transactions", "manager_no", "VARCHAR(40)"),
    ("silver_leave_transactions", "manager_name", "TEXT"),
    ("silver_leave_transactions", "leave_type", "TEXT"),
    ("silver_leave_transactions", "transaction_type", "TEXT"),
    ("silver_leave_transactions", "days", "NUMERIC(6,2)"),
    ("silver_daily_attendance", "emp_code", "VARCHAR(40)"),
    ("silver_daily_attendance", "employee_name", "TEXT"),
    ("silver_daily_attendance", "shift", "TEXT"),
    ("silver_daily_attendance", "status", "TEXT"),
    ("silver_daily_attendance", "approved_leave_type", "TEXT"),
]


def widen_columns(engine: Engine) -> None:
    if engine.dialect.name != "postgresql":
        return
    log.info("schema_align: widening %d columns if needed", len(WIDENINGS))
    # Each ALTER in its own transaction so one failure doesn't poison the rest.
    for table, column, target in WIDENINGS:
        stmt = f"ALTER TABLE {table} ALTER COLUMN {column} TYPE {target} USING {column}::{target}"
        try:
            with engine.begin() as conn:
                conn.execute(text(stmt))
        except Exception as e:
            log.warning("schema_align skip: %s.%s -> %s : %s", table, column, target, e)
    log.info("schema_align: done")
