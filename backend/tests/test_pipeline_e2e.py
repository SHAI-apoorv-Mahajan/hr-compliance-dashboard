"""US-009/10/11/12 — End-to-end medallion pipeline + flag engine.

Builds synthetic data for a small team:
  - Alice: present every weekday, 2 late arrivals (within threshold of 3)
  - Bob: 3 ABSENT days, 1 covered by approved Earned Leave, 2 uncovered →
    ABSENT_WITHOUT_LEAVE flag (threshold 2 → triggered at 2 > threshold? No,
    threshold is "> N", so we need 3 to trigger; we'll make Bob have 3 uncovered)
  - Charlie: Permanent WFH employee on NS shift — must NOT be flagged.
  - Dave: WFH availed 6 days vs 4 credit → WFH_QUOTA_EXCEEDED.
"""

from datetime import date

from tests.fixtures import (
    build_biometric_xlsx,
    build_greythr_xlsx,
    build_roster_xlsx,
    date_to_excel_serial,
)


PERIOD_START = date(2026, 4, 1)
PERIOD_END = date(2026, 4, 30)


def _present(d, late_by="00:00", early_by="00:00", in_time="10:00", out_time="19:00", work="09:00"):
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
        "status": "Present",
        "punch": f"{in_time}-{out_time}",
    }


def _absent(d):
    return {
        "att_date": d,
        "shift": "UB",
        "sched_in": "10:00",
        "sched_out": "19:00",
        "work_dur": "00:00",
        "ot": "00:00",
        "total_dur": "00:00",
        "late_by": "00:00",
        "early_by": "00:00",
        "status": "Absent",
        "punch": "",
    }


def _weeklyoff(d):
    return {
        "att_date": d,
        "shift": "UB",
        "work_dur": "00:00",
        "ot": "00:00",
        "total_dur": "00:00",
        "late_by": "00:00",
        "early_by": "00:00",
        "status": "WeeklyOff",
        "punch": "",
    }


def _ns_absent(d):
    """Permanent WFH employees show as Absent on NS shift days. Must not be flagged."""
    rec = _absent(d)
    rec["shift"] = "NS"
    return rec


def _roster_row(name, working_model="Hybrid", schedule=("WFO",) * 5, wfh_credits=4):
    days = list(schedule) + ["Dayoff", "Dayoff"]
    return {
        "Name": name,
        "Project": "P",
        "Client": "C",
        "In team Role": "Dev",
        "Billing status": "Billable",
        "Working Model": working_model,
        "Monday": days[0],
        "Tuesday": days[1],
        "Wednesday": days[2],
        "Thursday": days[3],
        "Friday": days[4],
        "Saturday": days[5],
        "Sunday": days[6],
        "Intime window onpen till": "10:30am",
        "Shift Time (Day)": "10:00-19:00",
        "Shift Time (Night)": "",
        "Comments": "",
        "WFH Credits": wfh_credits,
    }


def _upload_all(auth_client):
    # 1. Roster.
    roster = build_roster_xlsx(
        [
            _roster_row("Alice Doe"),
            _roster_row("Bob Smith"),
            _roster_row("Charlie WFH", working_model="Permanent WFH", schedule=("WFH",) * 5, wfh_credits=0),
            _roster_row("Dave Cloud"),
            _roster_row("Eve Late"),  # for LATE_ARRIVAL > 3
        ]
    )
    r = auth_client.post("/api/v1/upload/roster", files={"file": ("r.xlsx", roster, "x")})
    assert r.status_code == 201, r.text

    # Look up assigned emp_codes by re-querying via API.
    # Our roster parser doesn't assign emp_code; biometric attaches it.
    # We'll fix emp_codes in our biometric file to E001..E005.
    # Then the silver upsert path uses the name match.

    # 2. Biometric — period 2026-04-01..30.
    # Working dates Mon..Fri: 1,2,3, 6,7,8,9,10, 13,14,15,16,17, 20,21,22,23,24, 27,28,29,30.
    weekdays = [
        date(2026, 4, d) for d in (1, 2, 3, 6, 7, 8, 9, 10, 13, 14, 15, 16, 17, 20, 21, 22, 23, 24, 27, 28, 29, 30)
    ]
    weekends = [date(2026, 4, d) for d in (4, 5, 11, 12, 18, 19, 25, 26)]

    # Alice — all present, 2 late arrivals (within default threshold of 3).
    alice_days = []
    for i, d in enumerate(weekdays):
        if i < 2:
            alice_days.append(_present(d, late_by="00:30"))
        else:
            alice_days.append(_present(d))
    alice_days += [_weeklyoff(d) for d in weekends]

    # Bob — 4 absences without leave (covered by approved Earned Leave for 1 day).
    bob_days = []
    bob_absent_dates = weekdays[:5]
    for d in weekdays:
        if d in bob_absent_dates:
            bob_days.append(_absent(d))
        else:
            bob_days.append(_present(d))
    bob_days += [_weeklyoff(d) for d in weekends]

    # Charlie — Permanent WFH employee, NS-shift absent every weekday.
    charlie_days = [_ns_absent(d) for d in weekdays] + [_weeklyoff(d) for d in weekends]

    # Dave — all present, no late.
    dave_days = [_present(d) for d in weekdays] + [_weeklyoff(d) for d in weekends]

    # Eve — present, 4 late arrivals → triggers LATE_ARRIVAL (threshold 3).
    eve_days = []
    for i, d in enumerate(weekdays):
        if i < 4:
            eve_days.append(_present(d, late_by="00:30"))
        else:
            eve_days.append(_present(d))
    eve_days += [_weeklyoff(d) for d in weekends]

    bio = build_biometric_xlsx(
        [
            {"emp_code": "E001", "emp_name": "Alice Doe", "days": alice_days},
            {"emp_code": "E002", "emp_name": "Bob Smith", "days": bob_days},
            {"emp_code": "E003", "emp_name": "Charlie WFH", "days": charlie_days},
            {"emp_code": "E004", "emp_name": "Dave Cloud", "days": dave_days},
            {"emp_code": "E005", "emp_name": "Eve Late", "days": eve_days},
        ]
    )
    r = auth_client.post(
        "/api/v1/upload/biometric",
        files={"file": ("b.xlsx", bio, "x")},
        data={"period_start": "2026-04-01", "period_end": "2026-04-30"},
    )
    assert r.status_code == 201, r.text

    # 3. GreytHR — Bob has 1 covered absent date (Earned Leave). Dave has 6 WFH days.
    greythr_rows = [
        {
            "Sl No": 1,
            "Employee No": "E002",
            "Name": "Bob Smith",
            "Leave Type": "Earned Leave",
            "Transaction Type": "Availed",
            "From Date": date_to_excel_serial(bob_absent_dates[0]),
            "To Date": date_to_excel_serial(bob_absent_dates[0]),
            "Days": 1,
        },
    ]
    # Dave WFH × 6 days (each as a separate Availed transaction).
    for i in range(6):
        greythr_rows.append(
            {
                "Sl No": i + 2,
                "Employee No": "E004",
                "Name": "Dave Cloud",
                "Leave Type": "WFH",
                "Transaction Type": "Availed",
                "From Date": date_to_excel_serial(weekdays[i]),
                "To Date": date_to_excel_serial(weekdays[i]),
                "Days": 1,
            }
        )
    gx = build_greythr_xlsx(greythr_rows)
    r = auth_client.post(
        "/api/v1/upload/greythr",
        files={"file": ("g.xlsx", gx, "x")},
        data={"period_start": "2026-04-01", "period_end": "2026-04-30"},
    )
    assert r.status_code == 201, r.text


def test_pipeline_full_run_and_flags(auth_client, db):
    _upload_all(auth_client)

    # Need to associate emp_codes back to silver_employees so flag engine sees them.
    # Our roster parser created employees by NAME with NULL emp_code. The pipeline
    # depends on emp_code linkage. We'll patch by setting emp_code from name match.
    from models import SilverEmployee

    name_to_code = {
        "Alice Doe": "E001",
        "Bob Smith": "E002",
        "Charlie WFH": "E003",
        "Dave Cloud": "E004",
        "Eve Late": "E005",
    }
    for emp in db.query(SilverEmployee).all():
        emp.emp_code = name_to_code.get(emp.name)
    db.commit()

    # Run pipeline.
    r = auth_client.post(
        "/api/v1/pipeline/run",
        json={"period_start": "2026-04-01", "period_end": "2026-04-30"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["gold_stats"] == 5  # 5 employees with attendance rows

    # Verify flags.
    r = auth_client.get(
        "/api/v1/flags",
        params={"period_start": "2026-04-01", "period_end": "2026-04-30"},
    )
    assert r.status_code == 200
    flags = r.json()

    by_emp_and_type = {(f["emp_code"], f["flag_type"]) for f in flags}

    # Bob: 4 absent dates, 1 covered → 4 uncovered. Threshold 2 → 4 > 2 → flag.
    assert ("E002", "ABSENT_WITHOUT_LEAVE") in by_emp_and_type
    # Bob: also CONSECUTIVE_ABSENCE — 4 in a row, no covered in the middle, threshold 2.
    # But day 1 is covered; days 2-5 are uncovered. Longest consecutive uncovered run = 4 ≥ 2 → flag.
    assert ("E002", "CONSECUTIVE_ABSENCE") in by_emp_and_type
    # Bob: WFO violations on the uncovered absent weekdays (4 days) — threshold 1, count 4 → flag.
    assert ("E002", "WFO_VIOLATION") in by_emp_and_type

    # Charlie (permanent WFH): NO flags at all.
    charlie_flags = [f for f in flags if f["emp_code"] == "E003"]
    assert charlie_flags == [], f"Permanent WFH employee should have no flags, got {charlie_flags}"

    # Dave: WFH 6 vs credits 4 → WFH_QUOTA_EXCEEDED (excess = 2).
    assert ("E004", "WFH_QUOTA_EXCEEDED") in by_emp_and_type
    dave_wfh = next(f for f in flags if f["emp_code"] == "E004" and f["flag_type"] == "WFH_QUOTA_EXCEEDED")
    assert dave_wfh["flag_value"] == 2.0
    assert dave_wfh["threshold_value"] == 4.0

    # Eve: 4 late → LATE_ARRIVAL (threshold 3).
    assert ("E005", "LATE_ARRIVAL") in by_emp_and_type
    eve_late = next(f for f in flags if f["emp_code"] == "E005" and f["flag_type"] == "LATE_ARRIVAL")
    assert eve_late["flag_value"] == 4.0

    # Alice: only 2 late → no LATE_ARRIVAL flag (3 is not > 3).
    assert ("E001", "LATE_ARRIVAL") not in by_emp_and_type


def test_pipeline_idempotent(auth_client, db):
    _upload_all(auth_client)
    from models import SilverEmployee

    name_to_code = {
        "Alice Doe": "E001",
        "Bob Smith": "E002",
        "Charlie WFH": "E003",
        "Dave Cloud": "E004",
        "Eve Late": "E005",
    }
    for emp in db.query(SilverEmployee).all():
        emp.emp_code = name_to_code.get(emp.name)
    db.commit()

    auth_client.post(
        "/api/v1/pipeline/run",
        json={"period_start": "2026-04-01", "period_end": "2026-04-30"},
    )
    auth_client.post(
        "/api/v1/pipeline/run",
        json={"period_start": "2026-04-01", "period_end": "2026-04-30"},
    )

    from models import GoldEmployeeFlag, GoldPeriodStat

    # No duplicates in gold_period_stats.
    rows = db.query(GoldPeriodStat).all()
    keys = {(r.emp_code, r.period_start, r.period_end) for r in rows}
    assert len(keys) == len(rows)

    # No duplicates in gold_employee_flags.
    frows = db.query(GoldEmployeeFlag).all()
    fkeys = {(r.emp_code, r.flag_type, r.period_start) for r in frows}
    assert len(fkeys) == len(frows)


def test_resolved_flag_not_resurrected(auth_client, db):
    _upload_all(auth_client)
    from models import GoldEmployeeFlag, SilverEmployee

    name_to_code = {
        "Alice Doe": "E001",
        "Bob Smith": "E002",
        "Charlie WFH": "E003",
        "Dave Cloud": "E004",
        "Eve Late": "E005",
    }
    for emp in db.query(SilverEmployee).all():
        emp.emp_code = name_to_code.get(emp.name)
    db.commit()

    auth_client.post(
        "/api/v1/pipeline/run",
        json={"period_start": "2026-04-01", "period_end": "2026-04-30"},
    )
    bob_flag = (
        db.query(GoldEmployeeFlag)
        .filter(
            GoldEmployeeFlag.emp_code == "E002",
            GoldEmployeeFlag.flag_type == "ABSENT_WITHOUT_LEAVE",
        )
        .first()
    )
    assert bob_flag is not None
    flag_id = str(bob_flag.id)

    r = auth_client.patch(f"/api/v1/flags/{flag_id}/resolve")
    assert r.status_code == 200
    assert r.json()["is_active"] is False

    auth_client.post(
        "/api/v1/pipeline/run",
        json={"period_start": "2026-04-01", "period_end": "2026-04-30"},
    )
    db.expire_all()
    bob_flag = db.query(GoldEmployeeFlag).filter(GoldEmployeeFlag.id == bob_flag.id).first()
    # Should remain inactive (HR resolved → no auto-resurrect).
    assert bob_flag.is_active is False
