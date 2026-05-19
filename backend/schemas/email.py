from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TemplateIn(BaseModel):
    name: str
    flag_type: Optional[str] = None
    subject: str
    body: str


class TemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    flag_type: Optional[str] = None
    subject: str
    body: str
    available_variables: Optional[list[str]] = None
    is_active: bool
    updated_at: datetime


class SendRequest(BaseModel):
    flag_ids: list[UUID]
    template_id: UUID
    preview_only: bool = False


class RenderedEmail(BaseModel):
    flag_id: UUID
    emp_code: Optional[str]
    recipient_email: Optional[str]
    subject: str
    body: str


class SendResult(BaseModel):
    flag_id: UUID
    emp_code: Optional[str]
    recipient_email: Optional[str]
    status: str
    error_message: Optional[str] = None


class ConfigStatus(BaseModel):
    configured: bool
    missing: list[str]


class EmailLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    flag_id: Optional[UUID]
    template_id: Optional[UUID]
    emp_code: Optional[str]
    recipient_email: Optional[str]
    subject: Optional[str]
    body_preview: Optional[str]
    status: Optional[str]
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    sent_by: Optional[str]
    created_at: datetime
