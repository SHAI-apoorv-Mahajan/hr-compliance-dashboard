from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ThresholdOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    flag_type: str
    threshold_value: float
    threshold_unit: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    updated_at: datetime


class ThresholdUpdate(BaseModel):
    threshold_value: float
