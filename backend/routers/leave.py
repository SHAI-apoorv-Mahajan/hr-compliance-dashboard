"""Leave analysis. US-023."""

from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from models import AppUser, SilverEmployee, SilverLeaveTransaction
from routers.deps import get_current_user
from schemas.leave import LeaveSummaryRow, LeaveTransaction

router = APIRouter(prefix="/api/v1/leave", tags=["leave"])


@router.get("", response_model=list[LeaveSummaryRow])
def leave_summary(
    period_start: date = Query(...),
    period_end: date = Query(...),
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> list[LeaveSummaryRow]:
    emp_meta: dict[str, dict] = {}
    for e in db.query(SilverEmployee).all():
        if e.emp_code:
            emp_meta[e.emp_code] = {
                "name": e.name,
                "wfh_credits": e.wfh_credits_monthly or 0,
            }

    by_emp: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    wfh: dict[str, float] = defaultdict(float)

    for lr in (
        db.query(SilverLeaveTransaction)
        .filter(
            SilverLeaveTransaction.period_start == period_start,
            SilverLeaveTransaction.period_end == period_end,
            SilverLeaveTransaction.transaction_type == "Availed",
            SilverLeaveTransaction.emp_code.isnot(None),
        )
        .all()
    ):
        days = float(lr.days or 0)
        by_emp[lr.emp_code][lr.leave_type or "Unknown"] += days
        if (lr.leave_type or "").strip().lower() == "wfh":
            wfh[lr.emp_code] += days

    out: list[LeaveSummaryRow] = []
    for emp_code, types in by_emp.items():
        meta = emp_meta.get(emp_code, {"name": None, "wfh_credits": 0})
        availed = wfh.get(emp_code, 0.0)
        credits = meta["wfh_credits"]
        out.append(
            LeaveSummaryRow(
                emp_code=emp_code,
                name=meta["name"],
                by_type=dict(types),
                wfh_availed=availed,
                wfh_credits=credits,
                wfh_excess=max(0.0, availed - credits),
            )
        )
    out.sort(key=lambda r: r.name or r.emp_code)
    return out


@router.get("/{emp_code}", response_model=list[LeaveTransaction])
def leave_for_employee(
    emp_code: str,
    period_start: date = Query(...),
    period_end: date = Query(...),
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> list[SilverLeaveTransaction]:
    return (
        db.query(SilverLeaveTransaction)
        .filter(
            SilverLeaveTransaction.emp_code == emp_code,
            SilverLeaveTransaction.period_start == period_start,
            SilverLeaveTransaction.period_end == period_end,
        )
        .order_by(SilverLeaveTransaction.from_date)
        .all()
    )
