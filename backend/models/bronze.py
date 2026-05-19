"""Bronze layer — verbatim Excel ingest. Append-only audit data.

Variable-text fields use TEXT rather than narrow VARCHAR so real customer data
(which contains long roster comments, schedule notes, and free-text intime
windows) ingests without truncation.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from database import Base
from models._types import UUIDType


class BronzeUpload(Base):
    __tablename__ = "bronze_uploads"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    original_filename: Mapped[Optional[str]] = mapped_column(Text)
    period_start: Mapped[Optional[date]] = mapped_column()
    period_end: Mapped[Optional[date]] = mapped_column()
    uploaded_at: Mapped[datetime] = mapped_column(server_default=func.now())
    row_count: Mapped[Optional[int]] = mapped_column()
    status: Mapped[str] = mapped_column(String(20), default="pending")
    error_message: Mapped[Optional[str]] = mapped_column(Text)


class BronzeGreytHRRaw(Base):
    __tablename__ = "bronze_greythr_raw"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    upload_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("bronze_uploads.id", ondelete="CASCADE")
    )
    sl_no: Mapped[Optional[int]] = mapped_column()
    employee_no: Mapped[Optional[str]] = mapped_column(String(40))
    name: Mapped[Optional[str]] = mapped_column(Text)
    manager_no: Mapped[Optional[str]] = mapped_column(String(40))
    manager_name: Mapped[Optional[str]] = mapped_column(Text)
    leave_type: Mapped[Optional[str]] = mapped_column(Text)
    transaction_type: Mapped[Optional[str]] = mapped_column(Text)
    posted_date: Mapped[Optional[datetime]] = mapped_column()
    from_date: Mapped[Optional[date]] = mapped_column()
    to_date: Mapped[Optional[date]] = mapped_column()
    days: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    expire_date: Mapped[Optional[date]] = mapped_column()
    reason: Mapped[Optional[str]] = mapped_column(Text)
    remarks: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class BronzeBiometricRaw(Base):
    __tablename__ = "bronze_biometric_raw"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    upload_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("bronze_uploads.id", ondelete="CASCADE")
    )
    emp_code: Mapped[Optional[str]] = mapped_column(String(40))
    employee_name: Mapped[Optional[str]] = mapped_column(Text)
    att_date: Mapped[Optional[date]] = mapped_column()
    in_time: Mapped[Optional[str]] = mapped_column(String(20))
    out_time: Mapped[Optional[str]] = mapped_column(String(20))
    shift: Mapped[Optional[str]] = mapped_column(Text)
    scheduled_in_time: Mapped[Optional[str]] = mapped_column(String(20))
    scheduled_out_time: Mapped[Optional[str]] = mapped_column(String(20))
    work_duration_minutes: Mapped[Optional[int]] = mapped_column()
    ot_minutes: Mapped[Optional[int]] = mapped_column()
    total_duration_minutes: Mapped[Optional[int]] = mapped_column()
    late_by_minutes: Mapped[Optional[int]] = mapped_column()
    early_going_by_minutes: Mapped[Optional[int]] = mapped_column()
    status: Mapped[Optional[str]] = mapped_column(Text)
    punch_records: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class BronzeRosterRaw(Base):
    __tablename__ = "bronze_roster_raw"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    upload_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("bronze_uploads.id", ondelete="CASCADE")
    )
    name: Mapped[Optional[str]] = mapped_column(Text)
    project: Mapped[Optional[str]] = mapped_column(Text)
    client: Mapped[Optional[str]] = mapped_column(Text)
    in_team_role: Mapped[Optional[str]] = mapped_column(Text)
    billing_status: Mapped[Optional[str]] = mapped_column(Text)
    working_model: Mapped[Optional[str]] = mapped_column(Text)
    monday: Mapped[Optional[str]] = mapped_column(String(20))
    tuesday: Mapped[Optional[str]] = mapped_column(String(20))
    wednesday: Mapped[Optional[str]] = mapped_column(String(20))
    thursday: Mapped[Optional[str]] = mapped_column(String(20))
    friday: Mapped[Optional[str]] = mapped_column(String(20))
    saturday: Mapped[Optional[str]] = mapped_column(String(20))
    sunday: Mapped[Optional[str]] = mapped_column(String(20))
    intime_window: Mapped[Optional[str]] = mapped_column(Text)
    shift_time_day: Mapped[Optional[str]] = mapped_column(Text)
    shift_time_night: Mapped[Optional[str]] = mapped_column(Text)
    comments: Mapped[Optional[str]] = mapped_column(Text)
    wfh_credits: Mapped[Optional[int]] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
