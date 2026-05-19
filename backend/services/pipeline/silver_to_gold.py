"""Silver → Gold. FR-008.

Aggregates silver_daily_attendance + silver_leave_transactions per
(emp_code, period_start, period_end). Upserts gold_period_stats keyed on the
unique constraint. Re-running rebuilds the row in place.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from models import (
    GoldPeriodStat,
    SilverDailyAttendance,
    SilverEmployee,
    SilverLeaveTransaction,
)
from services.pipeline._upsert import upsert


log = logging.getLogger(__name__)


def run_silver_to_gold_stats(db: Session, period_start: date, period_end: date) -> int:
    log.info("gold/stats: starting for %s..%s", period_start, period_end)

    # Index employee → wfh_credits_monthly + is_permanent_wfh.
    emp_meta: dict[str, dict] = {}
    for e in db.query(SilverEmployee).all():
        if e.emp_code:
            emp_meta[e.emp_code] = {
                "wfh_credits_monthly": e.wfh_credits_monthly or 0,
                "is_permanent_wfh": e.is_permanent_wfh,
            }

    # Bucket attendance rows by emp_code.
    by_emp: dict[str, list[SilverDailyAttendance]] = defaultdict(list)
    rows = (
        db.query(SilverDailyAttendance)
        .filter(
            SilverDailyAttendance.period_start == period_start,
            SilverDailyAttendance.period_end == period_end,
            SilverDailyAttendance.emp_code.isnot(None),
        )
        .all()
    )
    for r in rows:
        by_emp[r.emp_code].append(r)

    # Leave-summary per emp.
    leave_by_emp: dict[str, dict[str, Decimal]] = defaultdict(lambda: defaultdict(lambda: Decimal("0")))
    wfh_availed: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    leave_rows = (
        db.query(SilverLeaveTransaction)
        .filter(
            SilverLeaveTransaction.period_start == period_start,
            SilverLeaveTransaction.period_end == period_end,
            SilverLeaveTransaction.transaction_type == "Availed",
            SilverLeaveTransaction.emp_code.isnot(None),
        )
        .all()
    )
    for lr in leave_rows:
        days = lr.days or Decimal("0")
        leave_by_emp[lr.emp_code][lr.leave_type or "Unknown"] += days
        if (lr.leave_type or "").strip().lower() == "wfh":
            wfh_availed[lr.emp_code] += days

    upsert_count = 0
    for emp_code, att_rows in by_emp.items():
        present_days = Decimal("0")
        absent_days = Decimal("0")
        absent_without_leave = Decimal("0")
        late_count = 0
        early_count = 0
        no_out_count = 0
        half_count = 0
        total_minutes = 0
        working_days = 0

        meta = emp_meta.get(emp_code, {"wfh_credits_monthly": 0, "is_permanent_wfh": False})

        for r in att_rows:
            if r.is_weekly_off:
                continue
            working_days += 1
            if r.is_half_present:
                present_days += Decimal("0.5")
                absent_days += Decimal("0.5")
                half_count += 1
            elif r.is_absent:
                absent_days += Decimal("1")
                if not r.has_approved_leave and not meta["is_permanent_wfh"]:
                    absent_without_leave += Decimal("1")
            else:
                present_days += Decimal("1")

            if r.late_by_minutes and r.late_by_minutes > 0 and r.status and "Present" in r.status:
                late_count += 1
            if r.early_going_by_minutes and r.early_going_by_minutes > 0 and r.status and "Present" in r.status:
                early_count += 1
            if r.is_no_out_punch:
                no_out_count += 1
            if r.work_duration_minutes:
                total_minutes += r.work_duration_minutes

        avg_daily = int(total_minutes / working_days) if working_days else 0
        leave_summary = {k: float(v) for k, v in leave_by_emp[emp_code].items()}

        upsert(
            db,
            model=GoldPeriodStat,
            conflict_cols=["emp_code", "period_start", "period_end"],
            values=dict(
                emp_code=emp_code,
                period_start=period_start,
                period_end=period_end,
                total_working_days=working_days,
                present_days=present_days,
                absent_days=absent_days,
                absent_without_leave_days=absent_without_leave,
                late_arrival_count=late_count,
                early_departure_count=early_count,
                no_out_punch_count=no_out_count,
                half_day_count=half_count,
                wfh_days_availed=int(wfh_availed.get(emp_code, 0)),
                wfh_credits_allocated=meta["wfh_credits_monthly"],
                total_work_minutes=total_minutes,
                avg_daily_work_minutes=avg_daily,
                leave_summary=leave_summary,
            ),
        )
        upsert_count += 1

    db.flush()
    log.info("gold/stats: upserted %d rows", upsert_count)
    return upsert_count
