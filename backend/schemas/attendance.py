from datetime import date, time
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AttendanceSummaryRow(BaseModel):
    emp_code: str
    name: Optional[str] = None
    present_days: float
    absent_days: float
    absent_without_leave_days: float
    late_arrival_count: int
    early_departure_count: int
    no_out_punch_count: int
    half_day_count: int
    total_work_minutes: int


class AttendanceDay(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    att_date: Optional[date]
    in_time: Optional[time]
    out_time: Optional[time]
    shift: Optional[str] = None
    work_duration_minutes: Optional[int] = None
    late_by_minutes: Optional[int] = None
    early_going_by_minutes: Optional[int] = None
    status: Optional[str] = None
    is_half_present: bool
    is_no_out_punch: bool
    is_absent: bool
    is_weekly_off: bool
    has_approved_leave: bool
    approved_leave_type: Optional[str] = None
