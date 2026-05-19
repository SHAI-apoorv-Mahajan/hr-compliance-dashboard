"""Pipeline trigger + status. FR-018."""

from __future__ import annotations

import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import (
    AppUser,
    BronzeUpload,
    GoldEmployeeFlag,
    GoldPeriodStat,
    SilverDailyAttendance,
    SilverLeaveTransaction,
)
from routers.deps import get_current_user
from schemas.pipeline import PipelineRunRequest, PipelineRunResult, PipelineStatusResult
from services.flag_engine import run_flag_engine
from services.pipeline.bronze_to_silver import run_bronze_to_silver
from services.pipeline.silver_to_gold import run_silver_to_gold_stats

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])


@router.post("/run", response_model=PipelineRunResult)
def run_pipeline(
    payload: PipelineRunRequest,
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> PipelineRunResult:
    if payload.period_start > payload.period_end:
        raise HTTPException(
            status_code=422, detail="period_start must be <= period_end"
        )

    has_greythr = _has_upload(db, "greythr", payload.period_start, payload.period_end)
    has_biometric = _has_upload(
        db, "biometric", payload.period_start, payload.period_end
    )
    if not has_greythr or not has_biometric:
        missing = []
        if not has_biometric:
            missing.append("biometric")
        if not has_greythr:
            missing.append("greythr")
        raise HTTPException(
            status_code=409,
            detail=f"Cannot run pipeline — missing upload(s): {', '.join(missing)}",
        )

    try:
        silver_counts = run_bronze_to_silver(
            db, payload.period_start, payload.period_end
        )
        stats_count = run_silver_to_gold_stats(
            db, payload.period_start, payload.period_end
        )
        flag_counts = run_flag_engine(db, payload.period_start, payload.period_end)
        db.commit()
    except Exception as exc:
        db.rollback()
        log.exception("pipeline run failed")
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {exc}") from exc

    return PipelineRunResult(
        period_start=payload.period_start,
        period_end=payload.period_end,
        silver=silver_counts,
        gold_stats=stats_count,
        flags=flag_counts,
    )


@router.get("/status/{period_start}/{period_end}", response_model=PipelineStatusResult)
def pipeline_status(
    period_start: date,
    period_end: date,
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> PipelineStatusResult:
    return PipelineStatusResult(
        period_start=period_start,
        period_end=period_end,
        has_greythr=_has_upload(db, "greythr", period_start, period_end),
        has_biometric=_has_upload(db, "biometric", period_start, period_end),
        silver_leave_rows=db.query(SilverLeaveTransaction)
        .filter(
            SilverLeaveTransaction.period_start == period_start,
            SilverLeaveTransaction.period_end == period_end,
        )
        .count(),
        silver_attendance_rows=db.query(SilverDailyAttendance)
        .filter(
            SilverDailyAttendance.period_start == period_start,
            SilverDailyAttendance.period_end == period_end,
        )
        .count(),
        gold_stat_rows=db.query(GoldPeriodStat)
        .filter(
            GoldPeriodStat.period_start == period_start,
            GoldPeriodStat.period_end == period_end,
        )
        .count(),
        active_flags=db.query(GoldEmployeeFlag)
        .filter(
            GoldEmployeeFlag.period_start == period_start,
            GoldEmployeeFlag.period_end == period_end,
            GoldEmployeeFlag.is_active.is_(True),
        )
        .count(),
    )


def _has_upload(
    db: Session, file_type: str, period_start: date, period_end: date
) -> bool:
    return (
        db.query(BronzeUpload)
        .filter(
            BronzeUpload.file_type == file_type,
            BronzeUpload.status == "processed",
            BronzeUpload.period_start == period_start,
            BronzeUpload.period_end == period_end,
        )
        .first()
        is not None
    )
