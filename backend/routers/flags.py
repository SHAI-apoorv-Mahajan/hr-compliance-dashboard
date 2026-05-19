"""Flag list / resolve / recompute. FR-012 / US-015."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import AppUser, GoldEmployeeFlag
from routers.deps import get_current_user
from schemas.flags import FlagOut, RecomputeRequest
from services.flag_engine import run_flag_engine


router = APIRouter(prefix="/api/v1/flags", tags=["flags"])


@router.get("", response_model=list[FlagOut])
def list_flags(
    period_start: date | None = Query(default=None),
    period_end: date | None = Query(default=None),
    flag_type: str | None = Query(default=None),
    emp_code: str | None = Query(default=None),
    include_resolved: bool = Query(default=False),
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> list[GoldEmployeeFlag]:
    q = db.query(GoldEmployeeFlag)
    if not include_resolved:
        q = q.filter(GoldEmployeeFlag.is_active.is_(True))
    if period_start:
        q = q.filter(GoldEmployeeFlag.period_start == period_start)
    if period_end:
        q = q.filter(GoldEmployeeFlag.period_end == period_end)
    if flag_type:
        q = q.filter(GoldEmployeeFlag.flag_type == flag_type)
    if emp_code:
        q = q.filter(GoldEmployeeFlag.emp_code == emp_code)
    return q.order_by(GoldEmployeeFlag.flag_type, GoldEmployeeFlag.employee_name).all()


@router.patch("/{flag_id}/resolve", response_model=FlagOut)
def resolve_flag(
    flag_id: UUID,
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> GoldEmployeeFlag:
    flag = db.get(GoldEmployeeFlag, flag_id)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    flag.is_active = False
    db.commit()
    db.refresh(flag)
    return flag


@router.post("/recompute", response_model=dict[str, int])
def recompute_flags(
    payload: RecomputeRequest,
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> dict[str, int]:
    counts = run_flag_engine(db, payload.period_start, payload.period_end)
    db.commit()
    return counts
