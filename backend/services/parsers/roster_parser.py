"""Team Timings & Roster parser. FR-004 / PRD §14.3.

Note: the source column is "Intime window onpen till" — that typo is verbatim
in the customer's file (PRD §27 #5). Do not normalize it.

This parser does double duty: ingest into bronze_roster_raw AND upsert into
silver_employees keyed on normalized name (case-insensitive, whitespace-
collapsed).
"""

from __future__ import annotations

import io
import logging
from typing import Any
from uuid import UUID

import pandas as pd
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from models import BronzeRosterRaw, SilverEmployee
from utils.date_utils import parse_time_string

log = logging.getLogger(__name__)


REQUIRED_COLUMNS = [
    "Name",
    "Project",
    "Client",
    "In team Role",
    "Billing status",
    "Working Model",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
    "Intime window onpen till",
    "Shift Time (Day)",
    "Shift Time (Night)",
    "Comments",
    "WFH Credits",
]


def normalize_name(name: str | None) -> str | None:
    if not name:
        return None
    return " ".join(str(name).split()).strip()


def parse_roster_and_upsert_employees(
    db: Session, upload_id: UUID, content: bytes
) -> int:
    try:
        df = pd.read_excel(io.BytesIO(content), sheet_name=0, dtype=object)
    except Exception as exc:
        raise HTTPException(
            status_code=422, detail=f"Cannot read roster Excel: {exc}"
        ) from exc

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Roster file missing required columns: {', '.join(missing)}",
        )

    rows = 0
    for _, row in df.iterrows():
        raw_name = _to_str(row.get("Name"))
        if not raw_name:
            continue

        working_model = _to_str(row.get("Working Model"))
        is_permanent_wfh = (working_model or "").strip().lower() == "permanent wfh"
        wfh_credits = _to_int(row.get("WFH Credits"))
        if wfh_credits is None:
            wfh_credits = 0  # PRD §27 #6 — intern blanks default to 0.
        intime_window = _to_str(row.get("Intime window onpen till"))
        intime_deadline = parse_time_string(intime_window)

        db.add(
            BronzeRosterRaw(
                upload_id=upload_id,
                name=raw_name,
                project=_to_str(row.get("Project")),
                client=_to_str(row.get("Client")),
                in_team_role=_to_str(row.get("In team Role")),
                billing_status=_to_str(row.get("Billing status")),
                working_model=working_model,
                monday=_to_str(row.get("Monday")),
                tuesday=_to_str(row.get("Tuesday")),
                wednesday=_to_str(row.get("Wednesday")),
                thursday=_to_str(row.get("Thursday")),
                friday=_to_str(row.get("Friday")),
                saturday=_to_str(row.get("Saturday")),
                sunday=_to_str(row.get("Sunday")),
                intime_window=intime_window,
                shift_time_day=_to_str(row.get("Shift Time (Day)")),
                shift_time_night=_to_str(row.get("Shift Time (Night)")),
                comments=_to_str(row.get("Comments")),
                wfh_credits=wfh_credits,
            )
        )

        # Upsert silver_employees by case-insensitive normalized name.
        norm = normalize_name(raw_name)
        existing = (
            db.query(SilverEmployee)
            .filter(func.lower(SilverEmployee.name) == norm.lower())
            .first()
        )
        common_fields = dict(
            name=norm,
            project=_to_str(row.get("Project")),
            client=_to_str(row.get("Client")),
            in_team_role=_to_str(row.get("In team Role")),
            billing_status=_to_str(row.get("Billing status")),
            working_model=working_model,
            is_permanent_wfh=is_permanent_wfh,
            wfh_credits_monthly=wfh_credits,
            intime_deadline=intime_deadline,
            shift_time_day=_to_str(row.get("Shift Time (Day)")),
            shift_time_night=_to_str(row.get("Shift Time (Night)")),
            schedule_monday=_to_str(row.get("Monday")),
            schedule_tuesday=_to_str(row.get("Tuesday")),
            schedule_wednesday=_to_str(row.get("Wednesday")),
            schedule_thursday=_to_str(row.get("Thursday")),
            schedule_friday=_to_str(row.get("Friday")),
            schedule_saturday=_to_str(row.get("Saturday")),
            schedule_sunday=_to_str(row.get("Sunday")),
            comments=_to_str(row.get("Comments")),
            roster_upload_id=upload_id,
        )
        if existing:
            for k, v in common_fields.items():
                setattr(existing, k, v)
        else:
            db.add(SilverEmployee(**common_fields))

        rows += 1

    db.flush()
    log.info("roster: parsed %d rows for upload=%s", rows, upload_id)
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
    s = str(v).strip()
    if not s:
        return None
    try:
        return int(float(s))
    except (TypeError, ValueError):
        return None
