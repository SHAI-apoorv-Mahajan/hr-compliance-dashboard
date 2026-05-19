"""US-006 / FR-003 — Biometric block parser."""

from datetime import date

import pytest

from models import BronzeBiometricRaw, BronzeUpload
from services.parsers.biometric_parser import parse_biometric
from tests.fixtures import build_biometric_xlsx


def _make_upload(db):
    u = BronzeUpload(
        file_type="biometric", original_filename="b.xlsx", status="processing"
    )
    db.add(u)
    db.flush()
    return u


def _day(
    d,
    status="Present",
    late_by="00:00",
    early_by="00:00",
    in_time="10:00",
    out_time="19:00",
    work="09:00",
):
    return {
        "att_date": d,
        "in_time": in_time,
        "out_time": out_time,
        "shift": "UB",
        "sched_in": "10:00",
        "sched_out": "19:00",
        "work_dur": work,
        "ot": "00:00",
        "total_dur": work,
        "late_by": late_by,
        "early_by": early_by,
        "status": status,
        "punch": f"{in_time}-{out_time}",
    }


def test_marker_row_recognized(db):
    u = _make_upload(db)
    content = build_biometric_xlsx(
        [
            {
                "emp_code": "E001",
                "emp_name": "Alice Doe",
                "days": [_day(date(2026, 4, 1))],
            }
        ]
    )
    parse_biometric(db, u.id, content)
    rows = db.query(BronzeBiometricRaw).all()
    assert len(rows) == 1
    assert rows[0].emp_code == "E001"
    assert rows[0].employee_name == "Alice Doe"
    assert rows[0].att_date == date(2026, 4, 1)


def test_header_row_after_marker_skipped(db):
    u = _make_upload(db)
    content = build_biometric_xlsx(
        [
            {
                "emp_code": "E001",
                "emp_name": "Alice",
                "days": [_day(date(2026, 4, 1)), _day(date(2026, 4, 2))],
            }
        ]
    )
    parse_biometric(db, u.id, content)
    rows = db.query(BronzeBiometricRaw).order_by(BronzeBiometricRaw.att_date).all()
    # Only data rows are kept — column header row "Att. Date / InTime / ..." was skipped.
    assert [r.att_date for r in rows] == [date(2026, 4, 1), date(2026, 4, 2)]


def test_total_duration_row_ends_block(db):
    u = _make_upload(db)
    content = build_biometric_xlsx(
        [
            {
                "emp_code": "E001",
                "emp_name": "Alice",
                "days": [_day(date(2026, 4, 1))],
            },
            {
                "emp_code": "E002",
                "emp_name": "Bob",
                "days": [_day(date(2026, 4, 1))],
            },
        ]
    )
    parse_biometric(db, u.id, content)
    rows = db.query(BronzeBiometricRaw).all()
    emp_codes = sorted({r.emp_code for r in rows})
    assert emp_codes == ["E001", "E002"]
    # Each row has the right emp_code (so the SUMMARY row reset current_emp_code).
    by_name = {r.emp_code: r.employee_name for r in rows}
    assert by_name["E001"] == "Alice"
    assert by_name["E002"] == "Bob"


def test_half_present_unicode_preserved(db):
    u = _make_upload(db)
    content = build_biometric_xlsx(
        [
            {
                "emp_code": "E001",
                "emp_name": "Alice",
                "days": [_day(date(2026, 4, 1), status="½Present")],
            }
        ]
    )
    parse_biometric(db, u.id, content)
    row = db.query(BronzeBiometricRaw).first()
    assert "½" in row.status
    assert row.status == "½Present"


def test_trailing_space_stripped(db):
    u = _make_upload(db)
    content = build_biometric_xlsx(
        [
            {
                "emp_code": "E001",
                "emp_name": "Alice",
                "days": [_day(date(2026, 4, 1), status="Present ")],
            }
        ]
    )
    parse_biometric(db, u.id, content)
    row = db.query(BronzeBiometricRaw).first()
    assert row.status == "Present"


def test_minutes_conversion(db):
    u = _make_upload(db)
    content = build_biometric_xlsx(
        [
            {
                "emp_code": "E001",
                "emp_name": "Alice",
                "days": [_day(date(2026, 4, 1), late_by="00:15", work="08:30")],
            }
        ]
    )
    parse_biometric(db, u.id, content)
    row = db.query(BronzeBiometricRaw).first()
    assert row.late_by_minutes == 15
    assert row.work_duration_minutes == 8 * 60 + 30


def test_empty_file_raises(db):
    u = _make_upload(db)
    import io
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["", "Daily Attendance Report (Detailed Summary Report)"])
    buf = io.BytesIO()
    wb.save(buf)

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        parse_biometric(db, u.id, buf.getvalue())
    assert exc.value.status_code == 422
