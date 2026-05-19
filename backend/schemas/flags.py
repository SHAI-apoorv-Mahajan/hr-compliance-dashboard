from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FlagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    emp_code: Optional[str] = None
    employee_name: Optional[str] = None
    period_start: Optional[date]
    period_end: Optional[date]
    flag_type: Optional[str]
    flag_value: Optional[float] = None
    threshold_value: Optional[float] = None
    flag_details: Optional[dict] = None
    is_active: bool
    email_sent: bool
    email_sent_at: Optional[datetime] = None


class RecomputeRequest(BaseModel):
    period_start: date
    period_end: date
