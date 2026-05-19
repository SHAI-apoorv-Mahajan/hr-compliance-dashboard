"""US-005/6/7/8/22 — Upload routes + duplicate guard."""

from datetime import date

from tests.fixtures import (
    build_biometric_xlsx,
    build_greythr_xlsx,
    build_roster_xlsx,
    date_to_excel_serial,
)


def _greythr_payload():
    return build_greythr_xlsx(
        [
            {
                "Sl No": 1,
                "Employee No": "E001",
                "Name": "Alice Doe",
                "Leave Type": "WFH",
                "Transaction Type": "Availed",
                "From Date": date_to_excel_serial(date(2026, 4, 1)),
                "To Date": date_to_excel_serial(date(2026, 4, 1)),
                "Days": 1,
            }
        ]
    )


def _biometric_payload():
    return build_biometric_xlsx(
        [
            {
                "emp_code": "E001",
                "emp_name": "Alice Doe",
                "days": [
                    {
                        "att_date": date(2026, 4, 1),
                        "in_time": "10:00",
                        "out_time": "19:00",
                        "shift": "UB",
                        "sched_in": "10:00",
                        "sched_out": "19:00",
                        "work_dur": "09:00",
                        "ot": "00:00",
                        "total_dur": "09:00",
                        "late_by": "00:00",
                        "early_by": "00:00",
                        "status": "Present",
                        "punch": "10:00-19:00",
                    }
                ],
            }
        ]
    )


def _roster_payload(name="Alice Doe"):
    return build_roster_xlsx(
        [
            {
                "Name": name,
                "Working Model": "Hybrid",
                "Monday": "WFO",
                "Tuesday": "WFO",
                "Wednesday": "WFH",
                "Thursday": "WFO",
                "Friday": "WFH",
                "Saturday": "Dayoff",
                "Sunday": "Dayoff",
                "Intime window onpen till": "10:30am",
                "Project": "P",
                "Client": "C",
                "In team Role": "Dev",
                "Billing status": "Billable",
                "Shift Time (Day)": "",
                "Shift Time (Night)": "",
                "Comments": "",
                "WFH Credits": 4,
            }
        ]
    )


def test_upload_greythr_happy_path(auth_client):
    files = {"file": ("g.xlsx", _greythr_payload(), "x")}
    data = {"period_start": "2026-04-01", "period_end": "2026-04-30"}
    r = auth_client.post("/api/v1/upload/greythr", files=files, data=data)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "processed"
    assert body["row_count"] == 1


def test_upload_non_xlsx_rejected(auth_client):
    files = {"file": ("g.csv", b"not xlsx", "text/csv")}
    data = {"period_start": "2026-04-01", "period_end": "2026-04-30"}
    r = auth_client.post("/api/v1/upload/greythr", files=files, data=data)
    assert r.status_code == 422


def test_upload_duplicate_period_rejected_409(auth_client):
    files = {"file": ("g.xlsx", _greythr_payload(), "x")}
    data = {"period_start": "2026-04-01", "period_end": "2026-04-30"}
    r1 = auth_client.post("/api/v1/upload/greythr", files=files, data=data)
    assert r1.status_code == 201

    files2 = {"file": ("g.xlsx", _greythr_payload(), "x")}
    r2 = auth_client.post("/api/v1/upload/greythr", files=files2, data=data)
    assert r2.status_code == 409
    assert "already been uploaded" in r2.json()["detail"]


def test_upload_overlapping_period_rejected_409(auth_client):
    files = {"file": ("g.xlsx", _greythr_payload(), "x")}
    auth_client.post(
        "/api/v1/upload/greythr",
        files=files,
        data={"period_start": "2026-04-01", "period_end": "2026-04-30"},
    )
    # Overlap: April 15 — May 15 overlaps April 1 — April 30.
    files2 = {"file": ("g.xlsx", _greythr_payload(), "x")}
    r = auth_client.post(
        "/api/v1/upload/greythr",
        files=files2,
        data={"period_start": "2026-04-15", "period_end": "2026-05-15"},
    )
    assert r.status_code == 409


def test_upload_roster_no_period_allowed_reupload(auth_client):
    files = {"file": ("r.xlsx", _roster_payload(), "x")}
    r1 = auth_client.post("/api/v1/upload/roster", files=files)
    assert r1.status_code == 201
    files2 = {"file": ("r.xlsx", _roster_payload(), "x")}
    r2 = auth_client.post("/api/v1/upload/roster", files=files2)
    assert r2.status_code == 201


def test_delete_upload_enables_reupload(auth_client):
    files = {"file": ("g.xlsx", _greythr_payload(), "x")}
    data = {"period_start": "2026-04-01", "period_end": "2026-04-30"}
    r1 = auth_client.post("/api/v1/upload/greythr", files=files, data=data)
    assert r1.status_code == 201
    upload_id = r1.json()["id"]

    r_del = auth_client.delete(f"/api/v1/upload/{upload_id}")
    assert r_del.status_code == 204

    files2 = {"file": ("g.xlsx", _greythr_payload(), "x")}
    r2 = auth_client.post("/api/v1/upload/greythr", files=files2, data=data)
    assert r2.status_code == 201


def test_upload_history(auth_client):
    files = {"file": ("g.xlsx", _greythr_payload(), "x")}
    auth_client.post(
        "/api/v1/upload/greythr",
        files=files,
        data={"period_start": "2026-04-01", "period_end": "2026-04-30"},
    )
    r = auth_client.get("/api/v1/upload/history")
    assert r.status_code == 200
    body = r.json()
    assert len(body) >= 1
    assert body[0]["file_type"] == "greythr"
