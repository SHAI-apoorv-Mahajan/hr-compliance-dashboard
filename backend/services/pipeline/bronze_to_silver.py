"""Bronze → Silver. FR-006, FR-007.

For a given period:
  - silver_leave_transactions: copy bronze_greythr_raw rows whose period overlaps.
  - silver_daily_attendance: type bronze biometric times, derive booleans,
    cross-reference Availed leave to set has_approved_leave / approved_leave_type.
  - Permanent WFH employees: cross-reference is skipped (their absent days stay
    has_approved_leave=False — but downstream flag engine never flags them anyway).
  - silver_employees: filled exclusively by the roster parser. We never invent
    employees from biometric data.

Idempotent: re-running for the same period rebuilds silver rows associated
with the period's upload_ids (delete-then-insert).
"""

from __future__ import annotations

import logging
from datetime import date, datetime, time
from typing import Iterable

from sqlalchemy import and_
from sqlalchemy.orm import Session

from models import (
    BronzeBiometricRaw,
    BronzeGreytHRRaw,
    BronzeUpload,
    SilverDailyAttendance,
    SilverEmployee,
    SilverLeaveTransaction,
)


log = logging.getLogger(__name__)


HALF_PRESENT_TOKEN = "½Present"


def run_bronze_to_silver(db: Session, period_start: date, period_end: date) -> dict[str, int]:
    counts: dict[str, int] = {"leave_transactions": 0, "daily_attendance": 0}
    log.info("silver: starting for %s..%s", period_start, period_end)

    counts["leave_transactions"] = _rebuild_leave_transactions(db, period_start, period_end)
    counts["daily_attendance"] = _rebuild_daily_attendance(db, period_start, period_end)

    log.info("silver: done %s", counts)
    return counts


# ---- leave_transactions ----------------------------------------------------

def _rebuild_leave_transactions(db: Session, period_start: date, period_end: date) -> int:
    """Replace all silver_leave_transactions rows where the bronze upload's period
    matches the requested period. Idempotent."""
    relevant_uploads = (
        db.query(BronzeUpload.id)
        .filter(
            BronzeUpload.file_type == "greythr",
            BronzeUpload.status == "processed",
            BronzeUpload.period_start == period_start,
            BronzeUpload.period_end == period_end,
        )
        .all()
    )
    upload_ids = [u[0] for u in relevant_uploads]
    if not upload_ids:
        # Wipe silver_leave_transactions for this period if no source upload exists.
        db.query(SilverLeaveTransaction).filter(
            and_(
                SilverLeaveTransaction.period_start == period_start,
                SilverLeaveTransaction.period_end == period_end,
            )
        ).delete()
        return 0

    db.query(SilverLeaveTransaction).filter(
        SilverLeaveTransaction.upload_id.in_(upload_ids)
    ).delete(synchronize_session=False)

    rows = 0
    for raw in db.query(BronzeGreytHRRaw).filter(BronzeGreytHRRaw.upload_id.in_(upload_ids)).all():
        db.add(
            SilverLeaveTransaction(
                upload_id=raw.upload_id,
                emp_code=raw.employee_no,
                employee_name=_clean_name(raw.name),
                manager_no=raw.manager_no,
                manager_name=raw.manager_name,
                leave_type=raw.leave_type,
                transaction_type=raw.transaction_type,
                posted_date=raw.posted_date,
                from_date=raw.from_date,
                to_date=raw.to_date,
                days=raw.days,
                expire_date=raw.expire_date,
                reason=raw.reason,
                remarks=raw.remarks,
                period_start=period_start,
                period_end=period_end,
            )
        )
        rows += 1
    db.flush()
    return rows


# ---- daily_attendance ------------------------------------------------------

def _backfill_emp_codes(db: Session, upload_ids: list) -> None:
    """Populate silver_employees.emp_code from biometric data via normalized name match.

    The roster file has no emp_code column, so silver_employees rows are created
    with emp_code=NULL. Biometric rows always carry emp_code. We close the gap by
    matching employee_name (normalized, lower-case) from both sources.
    Only writes to rows where emp_code is currently NULL to stay idempotent.
    """
    employees_without_code = (
        db.query(SilverEmployee)
        .filter(SilverEmployee.emp_code.is_(None))
        .all()
    )
    if not employees_without_code:
        return

    # Build name → emp_code map from biometric rows in current upload batch.
    bio_rows = (
        db.query(BronzeBiometricRaw.employee_name, BronzeBiometricRaw.emp_code)
        .filter(BronzeBiometricRaw.upload_id.in_(upload_ids))
        .filter(BronzeBiometricRaw.emp_code.isnot(None))
        .distinct()
        .all()
    )
    name_to_emp_code: dict[str, str] = {}
    for bio_name, emp_code in bio_rows:
        if bio_name and emp_code:
            key = " ".join(bio_name.strip().split()).lower()
            name_to_emp_code[key] = emp_code.strip()

    updated = 0
    for emp in employees_without_code:
        key = " ".join(emp.name.strip().split()).lower() if emp.name else ""
        if key and key in name_to_emp_code:
            emp.emp_code = name_to_emp_code[key]
            updated += 1

    if updated:
        db.flush()
        log.info("silver: backfilled emp_code for %d employees from biometric names", updated)


def _rebuild_daily_attendance(db: Session, period_start: date, period_end: date) -> int:
    """Type-convert bronze biometric rows, derive booleans, cross-reference leave.
    Idempotent: replace by upload_id."""
    relevant_uploads = (
        db.query(BronzeUpload.id)
        .filter(
            BronzeUpload.file_type == "biometric",
            BronzeUpload.status == "processed",
            BronzeUpload.period_start == period_start,
            BronzeUpload.period_end == period_end,
        )
        .all()
    )
    upload_ids = [u[0] for u in relevant_uploads]
    if not upload_ids:
        db.query(SilverDailyAttendance).filter(
            and_(
                SilverDailyAttendance.period_start == period_start,
                SilverDailyAttendance.period_end == period_end,
            )
        ).delete()
        return 0

    db.query(SilverDailyAttendance).filter(
        SilverDailyAttendance.upload_id.in_(upload_ids)
    ).delete(synchronize_session=False)

    # Back-fill emp_codes into silver_employees from biometric data before lookups.
    _backfill_emp_codes(db, upload_ids)

    # Build leave lookup: emp_code → list of (from_date, to_date, leave_type) for Availed rows.
    leave_lookup: dict[str, list[tuple[date, date, str]]] = {}
    leave_rows = (
        db.query(SilverLeaveTransaction)
        .filter(
            SilverLeaveTransaction.period_start == period_start,
            SilverLeaveTransaction.period_end == period_end,
            SilverLeaveTransaction.transaction_type == "Availed",
        )
        .all()
    )
    for lr in leave_rows:
        if not lr.emp_code or not lr.from_date or not lr.to_date:
            continue
        leave_lookup.setdefault(lr.emp_code, []).append(
            (lr.from_date, lr.to_date, lr.leave_type or "")
        )

    # Employee → is_permanent_wfh lookup (by emp_code if set, else by name).
    emp_code_to_pwfh: dict[str, bool] = {}
    name_to_pwfh: dict[str, bool] = {}
    for emp in db.query(SilverEmployee).all():
        if emp.emp_code:
            emp_code_to_pwfh[emp.emp_code] = emp.is_permanent_wfh
        if emp.name:
            name_to_pwfh[emp.name.lower()] = emp.is_permanent_wfh

    rows = 0
    for raw in (
        db.query(BronzeBiometricRaw).filter(BronzeBiometricRaw.upload_id.in_(upload_ids)).all()
    ):
        status = (raw.status or "").strip()
        is_half_present = HALF_PRESENT_TOKEN in status
        is_no_out_punch = "No OutPunch" in status
        is_absent = status == "Absent"
        is_weekly_off = "WeeklyOff" in status

        is_pwfh = False
        if raw.emp_code and raw.emp_code in emp_code_to_pwfh:
            is_pwfh = emp_code_to_pwfh[raw.emp_code]
        elif raw.employee_name:
            is_pwfh = name_to_pwfh.get(raw.employee_name.strip().lower(), False)

        has_approved_leave = False
        approved_leave_type: str | None = None
        # FR-007: skip cross-reference for permanent WFH employees.
        if not is_pwfh and is_absent and raw.emp_code and raw.att_date:
            for f, t, lt in leave_lookup.get(raw.emp_code, []):
                if f <= raw.att_date <= t:
                    has_approved_leave = True
                    approved_leave_type = lt
                    break

        db.add(
            SilverDailyAttendance(
                upload_id=raw.upload_id,
                emp_code=raw.emp_code,
                employee_name=raw.employee_name,
                att_date=raw.att_date,
                in_time=_to_time(raw.in_time),
                out_time=_to_time(raw.out_time),
                shift=raw.shift,
                scheduled_in_time=_to_time(raw.scheduled_in_time),
                scheduled_out_time=_to_time(raw.scheduled_out_time),
                work_duration_minutes=raw.work_duration_minutes,
                ot_minutes=raw.ot_minutes,
                total_duration_minutes=raw.total_duration_minutes,
                late_by_minutes=raw.late_by_minutes,
                early_going_by_minutes=raw.early_going_by_minutes,
                status=status,
                is_half_present=is_half_present,
                is_no_out_punch=is_no_out_punch,
                is_absent=is_absent,
                is_weekly_off=is_weekly_off,
                has_approved_leave=has_approved_leave,
                approved_leave_type=approved_leave_type,
                period_start=period_start,
                period_end=period_end,
            )
        )
        rows += 1
    db.flush()
    return rows


def _to_time(value: str | None) -> time | None:
    if not value:
        return None
    s = str(value).strip()
    if not s or s == "00:00":
        return None
    try:
        h, m = s.split(":")
        return time(int(h) % 24, int(m) % 60)
    except (ValueError, TypeError):
        return None


def _clean_name(name: str | None) -> str | None:
    if not name:
        return None
    return " ".join(name.split())
