from datetime import datetime, time
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    emp_code: Optional[str] = None
    name: str
    email: Optional[str] = None
    project: Optional[str] = None
    client: Optional[str] = None
    in_team_role: Optional[str] = None
    billing_status: Optional[str] = None
    working_model: Optional[str] = None
    is_permanent_wfh: bool
    wfh_credits_monthly: int
    intime_deadline: Optional[time] = None
    schedule_monday: Optional[str] = None
    schedule_tuesday: Optional[str] = None
    schedule_wednesday: Optional[str] = None
    schedule_thursday: Optional[str] = None
    schedule_friday: Optional[str] = None
    schedule_saturday: Optional[str] = None
    schedule_sunday: Optional[str] = None
    comments: Optional[str] = None
    updated_at: datetime


class EmailUpdate(BaseModel):
    email: EmailStr
