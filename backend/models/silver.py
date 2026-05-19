"""Silver layer — cleaned, typed, cross-referenced.

Free-text columns use TEXT to absorb whatever real customer data sends.
"""

import uuid
from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database import Base
from models._types import UUIDType


class SilverEmployee(Base):
    __tablename__ = "silver_employees"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    emp_code: Mapped[Optional[str]] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    project: Mapped[Optional[str]] = mapped_column(Text)
    client: Mapped[Optional[str]] = mapped_column(Text)
    in_team_role: Mapped[Optional[str]] = mapped_column(Text)
    billing_status: Mapped[Optional[str]] = mapped_column(Text)
    working_model: Mapped[Optional[str]] = mapped_column(Text)
    is_permanent_wfh: Mapped[bool] = mapped_column(Boolean, default=False)
    wfh_credits_monthly: Mapped[int] = mapped_column(default=4)
    intime_deadline: Mapped[Optional[time]] = mapped_column(Time)
    shift_time_day: Mapped[Optional[str]] = mapped_column(Text)
    shift_time_night: Mapped[Optional[str]] = mapped_column(Text)
    schedule_monday: Mapped[Optional[str]] = mapped_column(String(20))
    schedule_tuesday: Mapped[Optional[str]] = mapped_column(String(20))
    schedule_wednesday: Mapped[Optional[str]] = mapped_column(String(20))
    schedule_thursday: Mapped[Optional[str]] = mapped_column(String(20))
    schedule_friday: Mapped[Optional[str]] = mapped_column(String(20))
    schedule_saturday: Mapped[Optional[str]] = mapped_column(String(20))
    schedule_sunday: Mapped[Optional[str]] = mapped_column(String(20))
    comments: Mapped[Optional[str]] = mapped_column(Text)
    roster_upload_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUIDType(), ForeignKey("bronze_uploads.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )


class SilverLeaveTransaction(Base):
    __tablename__ = "silver_leave_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    upload_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("bronze_uploads.id", ondelete="CASCADE")
    )
    emp_code: Mapped[Optional[str]] = mapped_column(String(40))
    employee_name: Mapped[Optional[str]] = mapped_column(Text)
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
    period_start: Mapped[Optional[date]] = mapped_column()
    period_end: Mapped[Optional[date]] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class SilverDailyAttendance(Base):
    __tablename__ = "silver_daily_attendance"
    __table_args__ = (
        UniqueConstraint("emp_code", "att_date", "upload_id", name="uq_silver_emp_date_upload"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    upload_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), ForeignKey("bronze_uploads.id", ondelete="CASCADE")
    )
    emp_code: Mapped[Optional[str]] = mapped_column(String(40))
    employee_name: Mapped[Optional[str]] = mapped_column(Text)
    att_date: Mapped[Optional[date]] = mapped_column()
    in_time: Mapped[Optional[time]] = mapped_column(Time)
    out_time: Mapped[Optional[time]] = mapped_column(Time)
    shift: Mapped[Optional[str]] = mapped_column(Text)
    scheduled_in_time: Mapped[Optional[time]] = mapped_column(Time)
    scheduled_out_time: Mapped[Optional[time]] = mapped_column(Time)
    work_duration_minutes: Mapped[Optional[int]] = mapped_column()
    ot_minutes: Mapped[Optional[int]] = mapped_column()
    total_duration_minutes: Mapped[Optional[int]] = mapped_column()
    late_by_minutes: Mapped[Optional[int]] = mapped_column()
    early_going_by_minutes: Mapped[Optional[int]] = mapped_column()
    status: Mapped[Optional[str]] = mapped_column(Text)
    is_half_present: Mapped[bool] = mapped_column(Boolean, default=False)
    is_no_out_punch: Mapped[bool] = mapped_column(Boolean, default=False)
    is_absent: Mapped[bool] = mapped_column(Boolean, default=False)
    is_weekly_off: Mapped[bool] = mapped_column(Boolean, default=False)
    has_approved_leave: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_leave_type: Mapped[Optional[str]] = mapped_column(Text)
    period_start: Mapped[Optional[date]] = mapped_column()
    period_end: Mapped[Optional[date]] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
