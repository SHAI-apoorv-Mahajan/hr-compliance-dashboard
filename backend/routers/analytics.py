"""Dashboard analytics. FR-010 / US-013."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import (
    AppEmailLog,
    AppUser,
    GoldEmployeeFlag,
    GoldPeriodStat,
    SilverEmployee,
)
from routers.deps import get_current_user
from schemas.analytics import AttendanceBar, FlagSlice, LateTrendPoint, OverviewMetrics


router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/overview", response_model=OverviewMetrics)
def overview(
    period_start: date = Query(...),
    period_end: date = Query(...),
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> OverviewMetrics:
    total_employees = db.query(SilverEmployee).count()

    stats = (
        db.query(GoldPeriodStat)
        .filter(
            GoldPeriodStat.period_start == period_start,
            GoldPeriodStat.period_end == period_end,
        )
        .all()
    )

    flagged_emps = (
        db.query(GoldEmployeeFlag.emp_code)
        .filter(
            GoldEmployeeFlag.period_start == period_start,
            GoldEmployeeFlag.period_end == period_end,
            GoldEmployeeFlag.is_active.is_(True),
        )
        .distinct()
        .count()
    )

    if stats:
        present_total = sum(float(s.present_days or 0) for s in stats)
        working_total = sum(s.total_working_days or 0 for s in stats)
        attendance_rate = (present_total / working_total * 100.0) if working_total else 0.0

        wfh_emps = [s for s in stats if (s.wfh_credits_allocated or 0) > 0]
        if wfh_emps:
            compliant = sum(
                1 for s in wfh_emps if (s.wfh_days_availed or 0) <= (s.wfh_credits_allocated or 0)
            )
            wfh_compliance = compliant / len(wfh_emps) * 100.0
        else:
            wfh_compliance = 100.0
    else:
        attendance_rate = 0.0
        wfh_compliance = 0.0

    emails_sent = (
        db.query(AppEmailLog)
        .join(GoldEmployeeFlag, AppEmailLog.flag_id == GoldEmployeeFlag.id, isouter=True)
        .filter(
            AppEmailLog.status == "sent",
            GoldEmployeeFlag.period_start == period_start,
            GoldEmployeeFlag.period_end == period_end,
        )
        .count()
    )

    return OverviewMetrics(
        period_start=period_start,
        period_end=period_end,
        total_employees=total_employees,
        flagged_employees=flagged_emps,
        attendance_rate_pct=round(attendance_rate, 1),
        wfh_compliance_pct=round(wfh_compliance, 1),
        emails_sent_this_period=emails_sent,
    )


@router.get("/attendance-chart", response_model=list[AttendanceBar])
def attendance_chart(
    period_start: date = Query(...),
    period_end: date = Query(...),
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> list[AttendanceBar]:
    names = {e.emp_code: e.name for e in db.query(SilverEmployee).all() if e.emp_code}
    out: list[AttendanceBar] = []
    for s in (
        db.query(GoldPeriodStat)
        .filter(
            GoldPeriodStat.period_start == period_start,
            GoldPeriodStat.period_end == period_end,
        )
        .all()
    ):
        working = s.total_working_days or 0
        present = float(s.present_days or 0)
        pct = (present / working * 100.0) if working else 0.0
        out.append(
            AttendanceBar(
                emp_code=s.emp_code,
                name=names.get(s.emp_code),
                attendance_pct=round(pct, 1),
            )
        )
    out.sort(key=lambda b: b.attendance_pct)
    return out


@router.get("/flag-distribution", response_model=list[FlagSlice])
def flag_distribution(
    period_start: date = Query(...),
    period_end: date = Query(...),
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> list[FlagSlice]:
    rows = (
        db.query(GoldEmployeeFlag.flag_type, func.count())
        .filter(
            GoldEmployeeFlag.period_start == period_start,
            GoldEmployeeFlag.period_end == period_end,
            GoldEmployeeFlag.is_active.is_(True),
        )
        .group_by(GoldEmployeeFlag.flag_type)
        .all()
    )
    return [FlagSlice(flag_type=ft, count=c) for ft, c in rows]


@router.get("/late-trend", response_model=list[LateTrendPoint])
def late_trend(
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> list[LateTrendPoint]:
    # Aggregate by period across all gold_period_stats — last 6 distinct periods.
    rows = (
        db.query(
            GoldPeriodStat.period_start,
            GoldPeriodStat.period_end,
            func.sum(GoldPeriodStat.late_arrival_count),
        )
        .group_by(GoldPeriodStat.period_start, GoldPeriodStat.period_end)
        .order_by(GoldPeriodStat.period_start.desc())
        .limit(6)
        .all()
    )
    rows.reverse()
    return [
        LateTrendPoint(period_start=ps, period_end=pe, late_arrival_total=int(total or 0))
        for ps, pe, total in rows
    ]
