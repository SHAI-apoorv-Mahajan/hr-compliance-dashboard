"""Threshold settings. FR-016 / US-019."""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import AppFlagThreshold, AppUser
from routers.deps import get_current_user
from schemas.settings import ThresholdOut, ThresholdUpdate

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


@router.get("/thresholds", response_model=list[ThresholdOut])
def list_thresholds(
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> list[AppFlagThreshold]:
    return db.query(AppFlagThreshold).order_by(AppFlagThreshold.flag_type).all()


@router.put("/thresholds/{flag_type}", response_model=ThresholdOut)
def update_threshold(
    flag_type: str,
    payload: ThresholdUpdate,
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> AppFlagThreshold:
    if payload.threshold_value < 0:
        raise HTTPException(status_code=422, detail="threshold_value must be >= 0")
    row = (
        db.query(AppFlagThreshold)
        .filter(AppFlagThreshold.flag_type == flag_type)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Threshold not found")
    row.threshold_value = Decimal(str(payload.threshold_value))
    db.commit()
    db.refresh(row)
    return row
