from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_type: str
    original_filename: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    uploaded_at: datetime
    row_count: Optional[int] = None
    status: str
    error_message: Optional[str] = None


class UploadHistoryItem(UploadResponse):
    pass
