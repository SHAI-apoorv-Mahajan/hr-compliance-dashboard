"""Idempotent seed: default HR user, 8 email templates, 9 flag thresholds.

Each block is guarded by `count == 0` so re-runs are no-ops (FR-017).
"""

import logging
from decimal import Decimal

from sqlalchemy.orm import Session

from models import AppEmailTemplate, AppFlagThreshold, AppUser
from utils.auth_utils import hash_password

log = logging.getLogger(__name__)


DEFAULT_HR_EMAIL = "hr@shorthills.ai"
DEFAULT_HR_PASSWORD = "HR@ShortHills2024"


_VARIABLES = [
    "employee_name",
    "emp_code",
    "period",
    "period_start",
    "period_end",
    "flag_count",
    "flag_dates",
    "threshold",
    "sender_name",
]


_TEMPLATES = [
    {
        "name": "Late Arrivals Notice",
        "flag_type": "LATE_ARRIVAL",
        "subject": "Attendance Notice – Late Arrivals | {{period}}",
        "body": (
            "Dear {{employee_name}},\n\n"
            "We have reviewed your attendance records for {{period}} and noted that you arrived "
            "late on {{flag_count}} occasion(s) ({{flag_dates}}).\n\n"
            "As per company policy, your shift start time requires you to be logged in by your "
            "designated InTime. Repeated late arrivals impact team productivity and project "
            "delivery.\n\n"
            "We request you to ensure punctual attendance going forward. Please acknowledge this "
            "email or connect with the HR team if there are any concerns.\n\n"
            "Regards,\n{{sender_name}}"
        ),
    },
    {
        "name": "Uninformed Absence Notice",
        "flag_type": "ABSENT_WITHOUT_LEAVE",
        "subject": "Attendance Concern – Uninformed Absence | {{period}}",
        "body": (
            "Dear {{employee_name}},\n\n"
            "Our records indicate that you were absent without an approved leave on "
            "{{flag_count}} day(s) during {{period}} ({{flag_dates}}).\n\n"
            "An uninformed absence affects team planning and is a non-compliance with company "
            "attendance policy. Kindly ensure that any planned or unplanned absence is "
            "regularized through the GreytHR leave management system.\n\n"
            "If these absences were due to an emergency or technical difficulty, please contact "
            "HR immediately to regularize.\n\n"
            "Regards,\n{{sender_name}}"
        ),
    },
    {
        "name": "Consecutive Absence Notice",
        "flag_type": "CONSECUTIVE_ABSENCE",
        "subject": "Urgent: Consecutive Absence Without Leave | {{period}}",
        "body": (
            "Dear {{employee_name}},\n\n"
            "We have observed that you have been continuously absent for {{flag_count}} or more "
            "consecutive working days ({{flag_dates}}) during {{period}} without an approved "
            "leave on record.\n\n"
            "This is a serious compliance concern. Please respond to this email within 24 hours "
            "with a valid reason or proof of leave. Failure to respond may result in escalation "
            "per company policy.\n\n"
            "Regards,\n{{sender_name}}"
        ),
    },
    {
        "name": "Missing Out-Punch Notice",
        "flag_type": "NO_OUT_PUNCH",
        "subject": "Biometric Compliance – Missing Out-Punch | {{period}}",
        "body": (
            "Dear {{employee_name}},\n\n"
            "Your biometric attendance records for {{period}} show that you did not clock out on "
            "{{flag_count}} occasion(s) ({{flag_dates}}).\n\n"
            "Regular and complete biometric punching (both in and out) is mandatory. Incomplete "
            "records affect payroll and compliance reporting. Please ensure you clock out before "
            "leaving the premises each day.\n\n"
            "Regards,\n{{sender_name}}"
        ),
    },
    {
        "name": "WFH Quota Exceeded",
        "flag_type": "WFH_QUOTA_EXCEEDED",
        "subject": "WFH Policy Non-Compliance | {{period}}",
        "body": (
            "Dear {{employee_name}},\n\n"
            "As per company policy, your monthly WFH allocation for {{period}} is {{threshold}} "
            "day(s). Our records indicate you have availed {{flag_count}} WFH day(s) this "
            "period, exceeding your quota.\n\n"
            "Please ensure that WFH requests remain within the approved limits. For any "
            "exceptions or special circumstances, please write to HR in advance for approval.\n\n"
            "Regards,\n{{sender_name}}"
        ),
    },
    {
        "name": "WFO Compliance",
        "flag_type": "WFO_VIOLATION",
        "subject": "Work-From-Office Compliance | {{period}}",
        "body": (
            "Dear {{employee_name}},\n\n"
            "As per your roster, you are required to be present at the office on designated WFO "
            "days. Our records show that you were absent on {{flag_count}} WFO-mandated day(s) "
            "({{flag_dates}}) during {{period}} without an approved leave.\n\n"
            "Please ensure compliance with your scheduled WFO days. Reach out to your manager or "
            "HR if there is a genuine concern that requires a roster change.\n\n"
            "Regards,\n{{sender_name}}"
        ),
    },
    {
        "name": "Early Departures Notice",
        "flag_type": "EARLY_DEPARTURE",
        "subject": "Attendance Notice – Early Departures | {{period}}",
        "body": (
            "Dear {{employee_name}},\n\n"
            "We have noted that you left office earlier than your scheduled shift end on "
            "{{flag_count}} occasion(s) during {{period}} ({{flag_dates}}).\n\n"
            "Regular early departures without prior approval are not in line with our attendance "
            "policy. If you need to leave early on any day, please inform your manager and mark "
            "it in GreytHR.\n\n"
            "Regards,\n{{sender_name}}"
        ),
    },
    {
        "name": "Repeated Half-Days",
        "flag_type": "HALF_DAY_FREQUENCY",
        "subject": "Attendance Pattern – Repeated Half-Days | {{period}}",
        "body": (
            "Dear {{employee_name}},\n\n"
            "Your attendance records for {{period}} reflect {{flag_count}} half-day markings. "
            "While occasional half-days are understandable, a pattern of frequent half-days "
            "impacts project commitments and team schedules.\n\n"
            "We request you to plan your attendance better and use the leave application process "
            "for planned absences.\n\n"
            "Regards,\n{{sender_name}}"
        ),
    },
]


_THRESHOLDS = [
    ("LATE_ARRIVAL", Decimal("3"), "count", "Late arrivals per period exceeding N"),
    (
        "EARLY_DEPARTURE",
        Decimal("3"),
        "count",
        "Early departures per period exceeding N",
    ),
    (
        "ABSENT_WITHOUT_LEAVE",
        Decimal("2"),
        "days",
        "Absent without leave exceeding N days",
    ),
    (
        "CONSECUTIVE_ABSENCE",
        Decimal("2"),
        "days",
        "Consecutive absent-without-leave days",
    ),
    ("NO_OUT_PUNCH", Decimal("3"), "count", "No clock-out occurrences exceeding N"),
    ("HALF_DAY_FREQUENCY", Decimal("4"), "count", "Half-day occurrences exceeding N"),
    (
        "WFH_QUOTA_EXCEEDED",
        Decimal("0"),
        "days",
        "WFH availed > monthly credit (any excess)",
    ),
    (
        "LOW_WORK_HOURS",
        Decimal("300"),
        "minutes",
        "Work duration on present day < N minutes",
    ),
    ("WFO_VIOLATION", Decimal("1"), "count", "Scheduled WFO day, absent without leave"),
]


def seed_defaults(db: Session) -> None:
    """Idempotent. Each insert guarded by count check."""
    try:
        _seed_users(db)
        _seed_templates(db)
        _seed_thresholds(db)
        db.commit()
        log.info("seed: defaults reconciled")
    except Exception:
        log.exception("seed: failed — continuing app startup (NFR-005)")
        db.rollback()


def _seed_users(db: Session) -> None:
    if db.query(AppUser).count() > 0:
        return
    db.add(
        AppUser(
            email=DEFAULT_HR_EMAIL,
            password_hash=hash_password(DEFAULT_HR_PASSWORD),
            full_name="HR Admin",
            role="hr",
        )
    )
    log.info("seed: inserted default HR user")


def _seed_templates(db: Session) -> None:
    if db.query(AppEmailTemplate).count() > 0:
        return
    for t in _TEMPLATES:
        db.add(
            AppEmailTemplate(
                name=t["name"],
                flag_type=t["flag_type"],
                subject=t["subject"],
                body=t["body"],
                available_variables=_VARIABLES,
            )
        )
    log.info("seed: inserted %d email templates", len(_TEMPLATES))


def _seed_thresholds(db: Session) -> None:
    if db.query(AppFlagThreshold).count() > 0:
        return
    for flag_type, value, unit, description in _THRESHOLDS:
        db.add(
            AppFlagThreshold(
                flag_type=flag_type,
                threshold_value=value,
                threshold_unit=unit,
                description=description,
            )
        )
    log.info("seed: inserted %d flag thresholds", len(_THRESHOLDS))
