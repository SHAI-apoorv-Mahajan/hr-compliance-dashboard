"""Upload routers — three file types plus history/delete. FR-002/3/4/5.

Failure handling: the bronze_uploads row is committed BEFORE parsing so we
have a stable ID. If parsing fails, we rollback the failed transaction first,
then open a fresh transaction to mark the upload as failed and persist the
error message. This avoids PendingRollbackError when the parser hits a DB
constraint.
"""

from __future__ import annotations

import logging
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from database import get_db
from models import (
    AppUser,
    BronzeUpload,
    BronzeGreytHRRaw,
    BronzeBiometricRaw,
    BronzeRosterRaw,
)
from routers.deps import get_current_user
from schemas.upload import UploadHistoryItem, UploadResponse
from services.parsers.biometric_parser import parse_biometric
from services.parsers.greythr_parser import parse_greythr
from services.parsers.roster_parser import parse_roster_and_upsert_employees

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/upload", tags=["upload"])


def _require_xlsx(file: UploadFile) -> None:
    name = (file.filename or "").lower()
    if not name.endswith(".xlsx"):
        raise HTTPException(status_code=422, detail="Only .xlsx files are accepted")


def _reject_overlap(
    db: Session, file_type: str, period_start: date, period_end: date
) -> None:
    """FR-005: reject if any existing processed upload of this file_type overlaps the period."""
    overlap = (
        db.query(BronzeUpload)
        .filter(
            BronzeUpload.file_type == file_type,
            BronzeUpload.status == "processed",
            or_(
                and_(
                    BronzeUpload.period_start <= period_end,
                    BronzeUpload.period_end >= period_start,
                ),
            ),
        )
        .first()
    )
    if overlap:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A {file_type} file for this period has already been uploaded. "
                "Delete it first to re-upload."
            ),
        )


def _create_upload_row(
    db: Session,
    *,
    file_type: str,
    filename: str | None,
    period_start: date | None,
    period_end: date | None,
) -> BronzeUpload:
    upload = BronzeUpload(
        file_type=file_type,
        original_filename=filename,
        period_start=period_start,
        period_end=period_end,
        status="processing",
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload


def _mark_failed(db: Session, upload_id: UUID, error: str) -> None:
    """Rollback any failed transaction, then mark the upload as failed in a
    new transaction. Best-effort — never re-raises."""
    try:
        db.rollback()
    except Exception:
        pass
    try:
        row = db.get(BronzeUpload, upload_id)
        if row:
            row.status = "failed"
            row.error_message = error[:1000]
            db.commit()
    except Exception:
        log.exception("could not mark upload %s failed", upload_id)
        try:
            db.rollback()
        except Exception:
            pass


@router.post("/greythr", response_model=UploadResponse, status_code=201)
async def upload_greythr(
    file: UploadFile = File(...),
    period_start: date = Form(...),
    period_end: date = Form(...),
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> UploadResponse:
    _require_xlsx(file)
    _reject_overlap(db, "greythr", period_start, period_end)
    upload = _create_upload_row(
        db,
        file_type="greythr",
        filename=file.filename,
        period_start=period_start,
        period_end=period_end,
    )
    content = await file.read()
    try:
        row_count = parse_greythr(db, upload.id, content, period_start, period_end)
        upload.status = "processed"
        upload.row_count = row_count
        db.commit()
        db.refresh(upload)
    except HTTPException as exc:
        _mark_failed(db, upload.id, str(exc.detail))
        raise
    except Exception as exc:
        _mark_failed(db, upload.id, str(exc))
        log.exception("greythr upload failed")
        raise HTTPException(
            status_code=422, detail=f"Failed to parse GreytHR file: {exc}"
        ) from exc
    return UploadResponse.model_validate(upload, from_attributes=True)


@router.post("/biometric", response_model=UploadResponse, status_code=201)
async def upload_biometric(
    file: UploadFile = File(...),
    period_start: date = Form(...),
    period_end: date = Form(...),
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> UploadResponse:
    _require_xlsx(file)
    _reject_overlap(db, "biometric", period_start, period_end)
    upload = _create_upload_row(
        db,
        file_type="biometric",
        filename=file.filename,
        period_start=period_start,
        period_end=period_end,
    )
    content = await file.read()
    try:
        row_count = parse_biometric(db, upload.id, content)
        upload.status = "processed"
        upload.row_count = row_count
        db.commit()
        db.refresh(upload)
    except HTTPException as exc:
        _mark_failed(db, upload.id, str(exc.detail))
        raise
    except Exception as exc:
        _mark_failed(db, upload.id, str(exc))
        log.exception("biometric upload failed")
        raise HTTPException(
            status_code=422, detail=f"Failed to parse biometric file: {exc}"
        ) from exc
    return UploadResponse.model_validate(upload, from_attributes=True)


@router.post("/roster", response_model=UploadResponse, status_code=201)
async def upload_roster(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> UploadResponse:
    _require_xlsx(file)
    # Roster has no period. Re-uploads are allowed (upsert into silver_employees).
    upload = _create_upload_row(
        db,
        file_type="roster",
        filename=file.filename,
        period_start=None,
        period_end=None,
    )
    content = await file.read()
    try:
        row_count = parse_roster_and_upsert_employees(db, upload.id, content)
        upload.status = "processed"
        upload.row_count = row_count
        db.commit()
        db.refresh(upload)
    except HTTPException as exc:
        _mark_failed(db, upload.id, str(exc.detail))
        raise
    except Exception as exc:
        _mark_failed(db, upload.id, str(exc))
        log.exception("roster upload failed")
        raise HTTPException(
            status_code=422, detail=f"Failed to parse roster file: {exc}"
        ) from exc
    return UploadResponse.model_validate(upload, from_attributes=True)


@router.get("/history", response_model=list[UploadHistoryItem])
def upload_history(
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> list[BronzeUpload]:
    rows = db.query(BronzeUpload).order_by(BronzeUpload.uploaded_at.desc()).all()
    return rows


@router.delete("/{upload_id}", status_code=204, response_class=Response)
def delete_upload(
    upload_id: UUID,
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> Response:
    upload = db.get(BronzeUpload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    for model in (BronzeGreytHRRaw, BronzeBiometricRaw, BronzeRosterRaw):
        db.query(model).filter(model.upload_id == upload_id).delete()
    db.delete(upload)
    db.commit()
    return Response(status_code=204)
