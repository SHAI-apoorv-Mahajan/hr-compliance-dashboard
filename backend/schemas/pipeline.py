from datetime import date

from pydantic import BaseModel


class PipelineRunRequest(BaseModel):
    period_start: date
    period_end: date


class PipelineRunResult(BaseModel):
    period_start: date
    period_end: date
    silver: dict[str, int]
    gold_stats: int
    flags: dict[str, int]


class PipelineStatusResult(BaseModel):
    period_start: date
    period_end: date
    has_greythr: bool
    has_biometric: bool
    silver_leave_rows: int
    silver_attendance_rows: int
    gold_stat_rows: int
    active_flags: int
