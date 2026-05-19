from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


class LeaveSummaryRow(BaseModel):
    emp_code: str
    name: Optional[str] = None
    by_type: dict[str, float]
    wfh_availed: float
    wfh_credits: int
    wfh_excess: float


class LeaveTransaction(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    emp_code: Optional[str]
    leave_type: Optional[str]
    transaction_type: Optional[str]
    from_date: Optional[date]
    to_date: Optional[date]
    days: Optional[float]
    reason: Optional[str] = None
