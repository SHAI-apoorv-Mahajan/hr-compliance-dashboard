"""Gold layer — per-employee aggregates and triggered flags."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database import Base
from models._types import JSONBType, UUIDType


class GoldPeriodStat(Base):
    __tablename__ = "gold_period_stats"
    __table_args__ = (
        UniqueConstraint(
            "emp_code", "period_start", "period_end", name="uq_gold_period"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    emp_code: Mapped[Optional[str]] = mapped_column(String(20))
    period_start: Mapped[Optional[date]] = mapped_column()
    period_end: Mapped[Optional[date]] = mapped_column()
    total_working_days: Mapped[Optional[int]] = mapped_column()
    present_days: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    absent_days: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    absent_without_leave_days: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    late_arrival_count: Mapped[Optional[int]] = mapped_column()
    early_departure_count: Mapped[Optional[int]] = mapped_column()
    no_out_punch_count: Mapped[Optional[int]] = mapped_column()
    half_day_count: Mapped[Optional[int]] = mapped_column()
    wfh_days_availed: Mapped[Optional[int]] = mapped_column()
    wfh_credits_allocated: Mapped[Optional[int]] = mapped_column()
    total_work_minutes: Mapped[Optional[int]] = mapped_column()
    avg_daily_work_minutes: Mapped[Optional[int]] = mapped_column()
    leave_summary: Mapped[Optional[dict]] = mapped_column(JSONBType())
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class GoldEmployeeFlag(Base):
    __tablename__ = "gold_employee_flags"
    __table_args__ = (
        UniqueConstraint("emp_code", "flag_type", "period_start", name="uq_gold_flag"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(), primary_key=True, default=uuid.uuid4
    )
    emp_code: Mapped[Optional[str]] = mapped_column(String(20))
    employee_name: Mapped[Optional[str]] = mapped_column(String(150))
    period_start: Mapped[Optional[date]] = mapped_column()
    period_end: Mapped[Optional[date]] = mapped_column()
    flag_type: Mapped[Optional[str]] = mapped_column(String(60))
    flag_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    threshold_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    flag_details: Mapped[Optional[dict]] = mapped_column(JSONBType())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    email_sent_at: Mapped[Optional[datetime]] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
