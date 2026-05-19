"""Application layer — auth, templates, thresholds, audit log."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database import Base
from models._types import JSONBType, UUIDType


class AppUser(Base):
    __tablename__ = "app_users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20), default="hr")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    last_login: Mapped[Optional[datetime]] = mapped_column()


class AppEmailTemplate(Base):
    __tablename__ = "app_email_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    flag_type: Mapped[Optional[str]] = mapped_column(String(60))
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    available_variables: Mapped[Optional[list]] = mapped_column(JSONBType())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )


class AppFlagThreshold(Base):
    __tablename__ = "app_flag_thresholds"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    flag_type: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    threshold_value: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    threshold_unit: Mapped[Optional[str]] = mapped_column(String(20))
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )


class AppEmailLog(Base):
    __tablename__ = "app_email_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    flag_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUIDType(), ForeignKey("gold_employee_flags.id", ondelete="SET NULL")
    )
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUIDType(), ForeignKey("app_email_templates.id", ondelete="SET NULL")
    )
    emp_code: Mapped[Optional[str]] = mapped_column(String(20))
    recipient_email: Mapped[Optional[str]] = mapped_column(String(150))
    subject: Mapped[Optional[str]] = mapped_column(String(255))
    body_preview: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[Optional[str]] = mapped_column(String(20))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    sent_at: Mapped[Optional[datetime]] = mapped_column()
    sent_by: Mapped[Optional[str]] = mapped_column(String(150))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
