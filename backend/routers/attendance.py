"""Attendance summary + daily detail. FR-011 / US-014."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from models import AppUser, GoldPeriodStat, SilverDailyAttendance, SilverEmployee
from routers.deps import get_current_user
from schemas.attendance import AttendanceDay, AttendanceSummaryRow


router = APIRouter(prefix="/api/v1/attendance", tags=["attendance"])


@router.get("", response_model=list[AttendanceSummaryRow])
def list_summary(
    period_start: date = Query(...),
    period_end: date = Query(...),
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> list[AttendanceSummaryRow]:
    name_lookup = {e.emp_code: e.name for e in db.query(SilverEmployee).all() if e.emp_code}
    rows = (
        db.query(GoldPeriodStat)
        .filter(
            GoldPeriodStat.period_start == period_start,
            GoldPeriodStat.period_end == period_end,
        )
        .all()
    )
    return [
        AttendanceSummaryRow(
            emp_code=r.emp_code,
            name=name_lookup.get(r.emp_code),
            present_days=float(r.present_days or 0),
            absent_days=float(r.absent_days or 0),
            absent_without_leave_days=float(r.absent_without_leave_days or 0),
            late_arrival_count=r.late_arrival_count or 0,
            early_departure_count=r.early_departure_count or 0,
            no_out_punch_count=r.no_out_punch_count or 0,
            half_day_count=r.half_day_count or 0,
            total_work_minutes=r.total_work_minutes or 0,
        )
        for r in rows
    ]


@router.get("/{emp_code}", response_model=list[AttendanceDay])
def list_employee_days(
    emp_code: str,
    period_start: date = Query(...),
    period_end: date = Query(...),
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> list[SilverDailyAttendance]:
    return (
        db.query(SilverDailyAttendance)
        .filter(
            SilverDailyAttendance.emp_code == emp_code,
            SilverDailyAttendance.period_start == period_start,
            SilverDailyAttendance.period_end == period_end,
        )
        .order_by(SilverDailyAttendance.att_date)
        .all()
    )
