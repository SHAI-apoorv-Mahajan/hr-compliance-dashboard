from datetime import date

from pydantic import BaseModel


class OverviewMetrics(BaseModel):
    period_start: date
    period_end: date
    total_employees: int
    flagged_employees: int
    attendance_rate_pct: float
    wfh_compliance_pct: float
    emails_sent_this_period: int


class AttendanceBar(BaseModel):
    emp_code: str
    name: str | None = None
    attendance_pct: float


class FlagSlice(BaseModel):
    flag_type: str
    count: int


class LateTrendPoint(BaseModel):
    period_start: date
    period_end: date
    late_arrival_total: int
