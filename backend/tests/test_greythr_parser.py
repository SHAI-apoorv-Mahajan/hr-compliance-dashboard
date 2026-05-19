"""US-005 / FR-002 — GreytHR parser."""

from datetime import date
from decimal import Decimal
import pytest

from models import BronzeGreytHRRaw, BronzeUpload
from services.parsers.greythr_parser import parse_greythr
from tests.fixtures import build_greythr_xlsx, date_to_excel_serial


def _make_upload(db) -> BronzeUpload:
    u = BronzeUpload(file_type="greythr", original_filename="g.xlsx", status="processing")
    db.add(u)
    db.flush()
    return u


def test_excel_serial_conversion(db):
    upload = _make_upload(db)
    content = build_greythr_xlsx(
        [
            {
                "Sl No": 1,
                "Employee No": "E001",
                "Name": "Alice",
                "Leave Type": "WFH",
                "Transaction Type": "Availed",
                "Posted Date": "20 Mar 2026 18:12",
                "From Date": date_to_excel_serial(date(2026, 4, 1)),
                "To Date": date_to_excel_serial(date(2026, 4, 1)),
                "Days": 1,
                "Reason": "wfh",
                "Remarks": "",
            }
        ]
    )
    n = parse_greythr(db, upload.id, content, date(2026, 4, 1), date(2026, 4, 30))
    assert n == 1
    row = db.query(BronzeGreytHRRaw).first()
    assert row.from_date == date(2026, 4, 1)
    assert row.to_date == date(2026, 4, 1)


def test_decimal_days_preserved(db):
    upload = _make_upload(db)
    content = build_greythr_xlsx(
        [
            {
                "Sl No": 1,
                "Employee No": "E001",
                "Name": "Alice",
                "Leave Type": "CASUAL-SICK LEAVE",
                "Transaction Type": "Availed",
                "From Date": date_to_excel_serial(date(2026, 4, 1)),
                "To Date": date_to_excel_serial(date(2026, 4, 1)),
                "Days": 0.5,
            }
        ]
    )
    parse_greythr(db, upload.id, content, date(2026, 4, 1), date(2026, 4, 30))
    row = db.query(BronzeGreytHRRaw).first()
    assert row.days == Decimal("0.5")


def test_missing_column_raises_422(db):
    upload = _make_upload(db)
    # Build a file with the From Date column removed.
    import io

    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Sl No", "Employee No", "Name"])
    ws.append([1, "E001", "Alice"])
    buf = io.BytesIO()
    wb.save(buf)

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        parse_greythr(db, upload.id, buf.getvalue(), date(2026, 4, 1), date(2026, 4, 30))
    assert exc.value.status_code == 422
    assert "missing required columns" in exc.value.detail


def test_nullable_expire_date(db):
    upload = _make_upload(db)
    content = build_greythr_xlsx(
        [
            {
                "Sl No": 1,
                "Employee No": "E001",
                "Name": "A",
                "Leave Type": "WFH",
                "Transaction Type": "Availed",
                "From Date": date_to_excel_serial(date(2026, 4, 1)),
                "To Date": date_to_excel_serial(date(2026, 4, 1)),
                "Days": 1,
                # Expire Date intentionally absent.
            }
        ]
    )
    parse_greythr(db, upload.id, content, date(2026, 4, 1), date(2026, 4, 30))
    row = db.query(BronzeGreytHRRaw).first()
    assert row.expire_date is None
