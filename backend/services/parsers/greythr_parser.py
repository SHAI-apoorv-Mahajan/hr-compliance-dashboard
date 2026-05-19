"""GreytHR leave file parser. FR-002 / PRD §14.1 / §27 quirk #1.

Excel serial integers for From Date / To Date — convert manually via the
1899-12-30 epoch. pandas auto-detect is wrong on these columns.
"""

from __future__ import annotations

import io
import logging
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import BronzeGreytHRRaw
from utils.date_utils import excel_serial_to_date

log = logging.getLogger(__name__)


REQUIRED_COLUMNS = [
    "Sl No",
    "Employee No",
    "Name",
    "Manager No",
    "Manager Name",
    "Leave Type",
    "Transaction Type",
    "Posted Date",
    "From Date",
    "To Date",
    "Days",
    "Expire Date",
    "Reason",
    "Remarks",
]


def parse_greythr(
    db: Session,
    upload_id: UUID,
    content: bytes,
    period_start: date,
    period_end: date,
) -> int:
    """Parse a GreytHR .xlsx and persist rows to bronze_greythr_raw.

    Returns row count. Raises HTTPException 422 on bad input.
    """
    try:
        df = pd.read_excel(io.BytesIO(content), sheet_name=0, dtype=object)
    except Exception as exc:
        raise HTTPException(
            status_code=422, detail=f"Cannot read GreytHR Excel: {exc}"
        ) from exc

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"GreytHR file missing required columns: {', '.join(missing)}",
        )

    rows = 0
    for _, row in df.iterrows():
        from_date = excel_serial_to_date(row.get("From Date"))
        to_date = excel_serial_to_date(row.get("To Date"))
        expire_date = excel_serial_to_date(row.get("Expire Date"))

        posted_raw = row.get("Posted Date")
        try:
            posted_dt = (
                pd.to_datetime(posted_raw, errors="coerce")
                if posted_raw not in (None, "")
                else None
            )
            posted_dt = (
                posted_dt.to_pydatetime()
                if posted_dt is not pd.NaT and posted_dt is not None
                else None
            )
        except Exception:
            posted_dt = None

        db.add(
            BronzeGreytHRRaw(
                upload_id=upload_id,
                sl_no=_to_int(row.get("Sl No")),
                employee_no=_to_str(row.get("Employee No")),
                name=_to_str(row.get("Name")),
                manager_no=_to_str(row.get("Manager No")),
                manager_name=_to_str(row.get("Manager Name")),
                leave_type=_to_str(row.get("Leave Type")),
                transaction_type=_to_str(row.get("Transaction Type")),
                posted_date=posted_dt,
                from_date=from_date,
                to_date=to_date,
                days=_to_decimal(row.get("Days")),
                expire_date=expire_date,
                reason=_to_str(row.get("Reason")),
                remarks=_to_str(row.get("Remarks")),
            )
        )
        rows += 1

    db.flush()
    log.info(
        "greythr: parsed %d rows for upload=%s period=%s..%s",
        rows,
        upload_id,
        period_start,
        period_end,
    )
    return rows


def _to_str(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    s = str(v).strip()
    return s or None


def _to_int(v: Any) -> int | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def _to_decimal(v: Any) -> Decimal | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    try:
        return Decimal(str(v))
    except (InvalidOperation, TypeError, ValueError):
        return None
