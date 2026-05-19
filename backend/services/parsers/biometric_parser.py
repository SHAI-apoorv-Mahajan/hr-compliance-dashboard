"""Biometric attendance parser — block format. FR-003 / PRD §14.2.

The file is NOT a flat table. It is a sequence of employee blocks:
  - "Emp Code:" marker row → start block
  - column-header row (skipped)
  - one row per attendance day
  - "Total Duration=" row → end block

This parser implements the algorithm verbatim. Trailing spaces on status
strings are common and must be .strip()'d; the Unicode ½ (U+00BD) in
"½Present" must be preserved (PRD §27 #3, #4).
"""

from __future__ import annotations

import io
import logging
from datetime import datetime
from typing import Iterator
from uuid import UUID

import openpyxl
from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import BronzeBiometricRaw
from utils.date_utils import hhmm_to_minutes

log = logging.getLogger(__name__)


def parse_biometric(db: Session, upload_id: UUID, content: bytes) -> int:
    """Parse the biometric .xlsx and persist to bronze_biometric_raw.

    Returns row count. Raises HTTPException 422 on bad input.
    """
    try:
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception as exc:
        raise HTTPException(
            status_code=422, detail=f"Cannot read biometric Excel: {exc}"
        ) from exc

    ws = wb.active
    if ws is None:
        raise HTTPException(
            status_code=422, detail="Biometric Excel has no active sheet"
        )

    rows = 0
    for record in _iter_records(ws):
        db.add(BronzeBiometricRaw(upload_id=upload_id, **record))
        rows += 1

    db.flush()
    log.info("biometric: parsed %d rows for upload=%s", rows, upload_id)

    if rows == 0:
        # An empty parse is almost always wrong — the user uploaded the wrong file.
        raise HTTPException(
            status_code=422,
            detail=(
                "Biometric file produced 0 rows. Verify the file is the "
                "Daily Attendance Report (Detailed Summary) export."
            ),
        )
    return rows


def _iter_records(ws) -> Iterator[dict]:
    current_emp_code: str | None = None
    current_emp_name: str | None = None
    skip_next_row = False

    for row in ws.iter_rows(values_only=True):
        cells = [str(c).strip() if c is not None else "" for c in row]
        # Pad to ensure index access doesn't IndexError on short rows.
        while len(cells) < 16:
            cells.append("")

        # EMPLOYEE MARKER — column B (index 1) is "Emp Code:"
        if cells[1] == "Emp Code:":
            current_emp_code = cells[2] or None
            # Real files have "Employee Name :" label at col 4 and the actual
            # name at col 5+. Skip the label token itself when picking the name.
            name_parts = [
                c
                for c in cells[4:]
                if c and c.lower().rstrip(":").strip() != "employee name"
            ]
            current_emp_name = name_parts[0] if name_parts else None
            skip_next_row = True
            continue

        if skip_next_row:
            skip_next_row = False
            continue

        # SUMMARY row ends the block.
        if cells[1].startswith("Total Duration="):
            current_emp_code = None
            current_emp_name = None
            continue

        if not current_emp_code:
            continue
        if (
            not cells[1]
            or cells[1] == "Daily Attendance Report (Detailed Summary Report)"
        ):
            continue

        # DATA ROW — cells[1] is a date string like "01-Apr-2026".
        try:
            att_date = datetime.strptime(cells[1], "%d-%b-%Y").date()
        except (ValueError, TypeError):
            continue

        yield {
            "emp_code": current_emp_code,
            "employee_name": current_emp_name,
            "att_date": att_date,
            "in_time": cells[2] or None,
            "out_time": cells[3] or None,
            "shift": cells[4] or None,
            "scheduled_in_time": cells[6] or None,
            "scheduled_out_time": cells[7] or None,
            "work_duration_minutes": hhmm_to_minutes(cells[9]),
            "ot_minutes": hhmm_to_minutes(cells[10]),
            "total_duration_minutes": hhmm_to_minutes(cells[11]),
            "late_by_minutes": hhmm_to_minutes(cells[12]),
            "early_going_by_minutes": hhmm_to_minutes(cells[13]),
            # Preserve raw status verbatim (including U+00BD ½).
            "status": cells[14] or "",
            "punch_records": cells[15] or None,
        }
