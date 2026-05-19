"""US-007 / FR-004 — Roster parser + silver_employees upsert."""

from datetime import time
from uuid import uuid4

from models import BronzeRosterRaw, BronzeUpload, SilverEmployee
from services.parsers.roster_parser import parse_roster_and_upsert_employees
from tests.fixtures import build_roster_xlsx


def _make_upload(db):
    u = BronzeUpload(file_type="roster", original_filename="r.xlsx", status="processing")
    db.add(u)
    db.flush()
    return u


def test_typo_column_required_verbatim(db):
    u = _make_upload(db)
    content = build_roster_xlsx(
        [
            {
                "Name": "Alice Doe",
                "Project": "P",
                "Client": "C",
                "In team Role": "Dev",
                "Billing status": "Billable",
                "Working Model": "Hybrid",
                "Monday": "WFO",
                "Tuesday": "WFO",
                "Wednesday": "WFH",
                "Thursday": "WFO",
                "Friday": "WFH",
                "Saturday": "Dayoff",
                "Sunday": "Dayoff",
                "Intime window onpen till": "10:30am",
                "Shift Time (Day)": "10:00-19:00",
                "Shift Time (Night)": "",
                "Comments": "",
                "WFH Credits": 4,
            }
        ]
    )
    n = parse_roster_and_upsert_employees(db, u.id, content)
    assert n == 1
    emp = db.query(SilverEmployee).filter(SilverEmployee.name == "Alice Doe").first()
    assert emp is not None
    assert emp.intime_deadline == time(10, 30)


def test_permanent_wfh_flag(db):
    u = _make_upload(db)
    content = build_roster_xlsx(
        [
            {
                "Name": "Pat Permanent",
                "Working Model": "Permanent WFH",
                "Monday": "WFH",
                "Tuesday": "WFH",
                "Wednesday": "WFH",
                "Thursday": "WFH",
                "Friday": "WFH",
                "Saturday": "Dayoff",
                "Sunday": "Dayoff",
                "Intime window onpen till": "",
                "Project": "P",
                "Client": "C",
                "In team Role": "Dev",
                "Billing status": "Billable",
                "Shift Time (Day)": "",
                "Shift Time (Night)": "",
                "Comments": "",
                "WFH Credits": 0,
            }
        ]
    )
    parse_roster_and_upsert_employees(db, u.id, content)
    emp = db.query(SilverEmployee).first()
    assert emp.is_permanent_wfh is True


def test_intern_blank_credits_defaults_to_zero(db):
    u = _make_upload(db)
    content = build_roster_xlsx(
        [
            {
                "Name": "Bhavya Mendiratta",
                "Working Model": "Hybrid",
                "Monday": "WFO",
                "Tuesday": "WFO",
                "Wednesday": "WFO",
                "Thursday": "WFO",
                "Friday": "WFO",
                "Saturday": "Dayoff",
                "Sunday": "Dayoff",
                "Intime window onpen till": "10:30am",
                "Project": "P",
                "Client": "C",
                "In team Role": "Intern",
                "Billing status": "Non-Billable",
                "Shift Time (Day)": "",
                "Shift Time (Night)": "",
                "Comments": "",
                # WFH Credits intentionally blank.
            }
        ]
    )
    parse_roster_and_upsert_employees(db, u.id, content)
    emp = db.query(SilverEmployee).first()
    assert emp.wfh_credits_monthly == 0


def test_unparseable_intime_yields_null(db):
    u = _make_upload(db)
    content = build_roster_xlsx(
        [
            {
                "Name": "Lovneet",
                "Working Model": "Hybrid",
                "Monday": "WFO",
                "Tuesday": "WFO",
                "Wednesday": "WFO",
                "Thursday": "WFO",
                "Friday": "WFO",
                "Saturday": "Dayoff",
                "Sunday": "Dayoff",
                "Intime window onpen till": "Rotational — see comments",
                "Project": "P",
                "Client": "C",
                "In team Role": "Dev",
                "Billing status": "Billable",
                "Shift Time (Day)": "",
                "Shift Time (Night)": "",
                "Comments": "Rotational",
                "WFH Credits": 4,
            }
        ]
    )
    parse_roster_and_upsert_employees(db, u.id, content)
    emp = db.query(SilverEmployee).first()
    assert emp.intime_deadline is None


def test_reupload_upserts_by_normalized_name(db):
    u1 = _make_upload(db)
    content = build_roster_xlsx(
        [
            {
                "Name": "  alice   doe  ",  # whitespace + lowercase
                "Working Model": "Hybrid",
                "Monday": "WFO",
                "Tuesday": "WFO",
                "Wednesday": "WFH",
                "Thursday": "WFO",
                "Friday": "WFH",
                "Saturday": "Dayoff",
                "Sunday": "Dayoff",
                "Intime window onpen till": "10:30am",
                "Project": "Old",
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
    parse_roster_and_upsert_employees(db, u1.id, content)

    u2 = _make_upload(db)
    content2 = build_roster_xlsx(
        [
            {
                "Name": "Alice Doe",
                "Working Model": "Hybrid",
                "Monday": "WFO",
                "Tuesday": "WFO",
                "Wednesday": "WFH",
                "Thursday": "WFO",
                "Friday": "WFH",
                "Saturday": "Dayoff",
                "Sunday": "Dayoff",
                "Intime window onpen till": "10:30am",
                "Project": "New",
                "Client": "C",
                "In team Role": "Dev",
                "Billing status": "Billable",
                "Shift Time (Day)": "",
                "Shift Time (Night)": "",
                "Comments": "",
                "WFH Credits": 6,
            }
        ]
    )
    parse_roster_and_upsert_employees(db, u2.id, content2)

    employees = db.query(SilverEmployee).all()
    assert len(employees) == 1
    assert employees[0].project == "New"
    assert employees[0].wfh_credits_monthly == 6
