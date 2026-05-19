"""Flag engine. FR-009 + PRD §17.

9 flag types evaluated per (emp_code, period). Each fires when its rule says
so vs the threshold from app_flag_thresholds. Writes to gold_employee_flags
keyed on (emp_code, flag_type, period_start). Idempotent.

Permanent WFH employees (silver_employees.is_permanent_wfh = True) never
produce LATE_ARRIVAL, ABSENT_WITHOUT_LEAVE, or WFO_VIOLATION flags
(FR-007 + PRD §27 #8).
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from models import (
    AppFlagThreshold,
    GoldEmployeeFlag,
    SilverDailyAttendance,
    SilverEmployee,
    SilverLeaveTransaction,
)
from services.pipeline._upsert import upsert


log = logging.getLogger(__name__)


FLAG_TYPES = [
    "LATE_ARRIVAL",
    "EARLY_DEPARTURE",
    "ABSENT_WITHOUT_LEAVE",
    "CONSECUTIVE_ABSENCE",
    "NO_OUT_PUNCH",
    "HALF_DAY_FREQUENCY",
    "WFH_QUOTA_EXCEEDED",
    "LOW_WORK_HOURS",
    "WFO_VIOLATION",
]


def run_flag_engine(db: Session, period_start: date, period_end: date) -> dict[str, int]:
    log.info("flags: starting for %s..%s", period_start, period_end)

    thresholds = {
        t.flag_type: t.threshold_value
        for t in db.query(AppFlagThreshold).filter(AppFlagThreshold.is_active.is_(True)).all()
    }

    employees = {e.emp_code: e for e in db.query(SilverEmployee).all() if e.emp_code}

    # Bucket attendance rows by emp_code (sorted by date).
    att_by_emp: dict[str, list[SilverDailyAttendance]] = defaultdict(list)
    for r in (
        db.query(SilverDailyAttendance)
        .filter(
            SilverDailyAttendance.period_start == period_start,
            SilverDailyAttendance.period_end == period_end,
            SilverDailyAttendance.emp_code.isnot(None),
        )
        .order_by(SilverDailyAttendance.emp_code, SilverDailyAttendance.att_date)
        .all()
    ):
        att_by_emp[r.emp_code].append(r)

    # WFH availed by emp.
    wfh_availed: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for lr in (
        db.query(SilverLeaveTransaction)
        .filter(
            SilverLeaveTransaction.period_start == period_start,
            SilverLeaveTransaction.period_end == period_end,
            SilverLeaveTransaction.transaction_type == "Availed",
        )
        .all()
    ):
        if lr.emp_code and (lr.leave_type or "").strip().lower() == "wfh":
            wfh_availed[lr.emp_code] += lr.days or Decimal("0")

    counts: dict[str, int] = defaultdict(int)
    seen_flag_keys: set[tuple[str, str]] = set()

    for emp_code, att_rows in att_by_emp.items():
        emp = employees.get(emp_code)
        is_pwfh = bool(emp and emp.is_permanent_wfh)

        # Per-flag evaluation. Each returns (should_flag, flag_value, threshold, details).
        for flag_type in FLAG_TYPES:
            result = _evaluate(
                flag_type=flag_type,
                emp=emp,
                emp_code=emp_code,
                att_rows=att_rows,
                wfh_availed=wfh_availed.get(emp_code, Decimal("0")),
                thresholds=thresholds,
                is_pwfh=is_pwfh,
            )
            if not result:
                continue
            flag_value, threshold_value, details = result
            _upsert_flag(
                db,
                emp_code=emp_code,
                employee_name=(emp.name if emp else None),
                period_start=period_start,
                period_end=period_end,
                flag_type=flag_type,
                flag_value=flag_value,
                threshold_value=threshold_value,
                details=details,
            )
            seen_flag_keys.add((emp_code, flag_type))
            counts[flag_type] += 1

    # Flags that no longer apply: deactivate (don't delete — HR may have set
    # is_active=False already, and we must preserve email_sent state).
    _deactivate_stale(db, period_start, seen_flag_keys)

    db.flush()
    log.info("flags: done %s", dict(counts))
    return dict(counts)


# ---- per-flag evaluation ---------------------------------------------------

def _evaluate(
    flag_type: str,
    emp: SilverEmployee | None,
    emp_code: str,
    att_rows: list[SilverDailyAttendance],
    wfh_availed: Decimal,
    thresholds: dict[str, Decimal],
    is_pwfh: bool,
) -> tuple[Decimal, Decimal, dict] | None:
    threshold = thresholds.get(flag_type)
    if threshold is None:
        return None

    if flag_type == "LATE_ARRIVAL":
        if is_pwfh:
            return None
        dates = [
            r.att_date.isoformat()
            for r in att_rows
            if r.late_by_minutes and r.late_by_minutes > 0 and r.status and "Present" in r.status
        ]
        n = len(dates)
        return (Decimal(n), threshold, {"dates": dates}) if Decimal(n) > threshold else None

    if flag_type == "EARLY_DEPARTURE":
        dates = [
            r.att_date.isoformat()
            for r in att_rows
            if r.early_going_by_minutes
            and r.early_going_by_minutes > 0
            and r.status
            and "Present" in r.status
        ]
        n = len(dates)
        return (Decimal(n), threshold, {"dates": dates}) if Decimal(n) > threshold else None

    if flag_type == "ABSENT_WITHOUT_LEAVE":
        if is_pwfh:
            return None
        dates = [
            r.att_date.isoformat()
            for r in att_rows
            if r.is_absent and not r.is_weekly_off and not r.has_approved_leave
        ]
        n = len(dates)
        return (Decimal(n), threshold, {"dates": dates}) if Decimal(n) > threshold else None

    if flag_type == "CONSECUTIVE_ABSENCE":
        if is_pwfh:
            return None
        # Build sorted list of (date, kind) with kind in {"AWL","OFF","OTHER"}.
        # WeeklyOff is transparent — does NOT break a run (PRD §17 + US-011 11h).
        ordered = sorted(att_rows, key=lambda r: r.att_date or date.min)
        longest_run: list[date] = []
        cur_run: list[date] = []
        for r in ordered:
            if r.is_weekly_off:
                continue  # transparent
            if r.is_absent and not r.has_approved_leave:
                cur_run.append(r.att_date)
            else:
                if len(cur_run) > len(longest_run):
                    longest_run = cur_run
                cur_run = []
        if len(cur_run) > len(longest_run):
            longest_run = cur_run
        n = len(longest_run)
        if Decimal(n) >= threshold and n > 0:
            return (
                Decimal(n),
                threshold,
                {"dates": [d.isoformat() for d in longest_run]},
            )
        return None

    if flag_type == "NO_OUT_PUNCH":
        dates = [r.att_date.isoformat() for r in att_rows if r.is_no_out_punch]
        n = len(dates)
        return (Decimal(n), threshold, {"dates": dates}) if Decimal(n) > threshold else None

    if flag_type == "HALF_DAY_FREQUENCY":
        dates = [r.att_date.isoformat() for r in att_rows if r.is_half_present]
        n = len(dates)
        return (Decimal(n), threshold, {"dates": dates}) if Decimal(n) > threshold else None

    if flag_type == "WFH_QUOTA_EXCEEDED":
        credits = Decimal(emp.wfh_credits_monthly if emp else 0)
        # threshold for this flag is treated as "any excess above credits" (PRD §17:
        # default threshold value is 0 = any excess). flag_value = excess days.
        excess = wfh_availed - credits
        if excess > threshold:
            return (excess, credits, {"availed": float(wfh_availed), "credits": float(credits)})
        return None

    if flag_type == "LOW_WORK_HOURS":
        # threshold is minutes (default 300). Flag if ANY present day < threshold.
        dates = [
            r.att_date.isoformat()
            for r in att_rows
            if r.status
            and "Present" in r.status
            and not r.is_weekly_off
            and r.work_duration_minutes is not None
            and Decimal(r.work_duration_minutes) < threshold
        ]
        n = len(dates)
        return (Decimal(n), threshold, {"dates": dates}) if n > 0 else None

    if flag_type == "WFO_VIOLATION":
        if is_pwfh or not emp:
            return None
        # For each absent-without-leave day, check that day's scheduled work mode.
        schedule_attrs = {
            0: "schedule_monday",
            1: "schedule_tuesday",
            2: "schedule_wednesday",
            3: "schedule_thursday",
            4: "schedule_friday",
            5: "schedule_saturday",
            6: "schedule_sunday",
        }
        dates: list[str] = []
        for r in att_rows:
            if (
                r.is_absent
                and not r.is_weekly_off
                and not r.has_approved_leave
                and r.att_date is not None
            ):
                attr = schedule_attrs[r.att_date.weekday()]
                if (getattr(emp, attr) or "").strip().upper() == "WFO":
                    dates.append(r.att_date.isoformat())
        n = len(dates)
        return (Decimal(n), threshold, {"dates": dates}) if Decimal(n) >= threshold and n > 0 else None

    return None


def _upsert_flag(
    db: Session,
    *,
    emp_code: str,
    employee_name: str | None,
    period_start: date,
    period_end: date,
    flag_type: str,
    flag_value: Decimal,
    threshold_value: Decimal,
    details: dict,
) -> None:
    """Upsert keyed on (emp_code, flag_type, period_start). On update, we
    preserve is_active, email_sent, and email_sent_at — those are HR-driven."""
    upsert(
        db,
        model=GoldEmployeeFlag,
        conflict_cols=["emp_code", "flag_type", "period_start"],
        values=dict(
            emp_code=emp_code,
            employee_name=employee_name,
            period_start=period_start,
            period_end=period_end,
            flag_type=flag_type,
            flag_value=flag_value,
            threshold_value=threshold_value,
            flag_details=details,
            is_active=True,
            email_sent=False,
        ),
        # Don't auto-resurrect resolved flags (FR-009 / US-011 AC).
        # Don't reset email_sent — preserve send history.
        update_cols=[
            "employee_name",
            "period_end",
            "flag_value",
            "threshold_value",
            "flag_details",
        ],
    )


def _deactivate_stale(
    db: Session,
    period_start: date,
    seen_keys: set[tuple[str, str]],
) -> None:
    """Flags from a prior run that no longer apply this run → is_active = False."""
    existing = (
        db.query(GoldEmployeeFlag)
        .filter(GoldEmployeeFlag.period_start == period_start, GoldEmployeeFlag.is_active.is_(True))
        .all()
    )
    for f in existing:
        if (f.emp_code, f.flag_type) not in seen_keys:
            f.is_active = False
