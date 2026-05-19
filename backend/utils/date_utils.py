"""Date / time helpers — Excel serial conversion (PRD §27 #1), HH:MM → minutes."""

import re
from datetime import date, datetime, timedelta, time


EXCEL_EPOCH = datetime(1899, 12, 30)


def excel_serial_to_date(serial: int | float | str | None) -> date | None:
    if serial is None or serial == "":
        return None
    try:
        n = int(float(serial))
    except (TypeError, ValueError):
        return None
    return (EXCEL_EPOCH + timedelta(days=n)).date()


def hhmm_to_minutes(value: str | None) -> int:
    """Convert "HH:MM" to minutes. Falsy / unparseable → 0 (we never want None for arithmetic)."""
    if not value:
        return 0
    s = str(value).strip()
    if not s:
        return 0
    try:
        parts = s.split(":")
        if len(parts) != 2:
            return 0
        return int(parts[0]) * 60 + int(parts[1])
    except (ValueError, AttributeError):
        return 0


def parse_time_string(value: str | None) -> time | None:
    """Parse loose time strings to a `time`. Returns None on unparseable input
    (FR-004 / FR-004 fallback for intime_window free-text rotational comments).

    Accepts: "10:30am", "10:30 AM", "10:30", "1:05pm", " 10:30 ".
    """
    if not value:
        return None
    s = str(value).strip().lower().replace(" ", "")
    if not s:
        return None
    # Match "HH:MM" with optional am/pm suffix.
    m = re.fullmatch(r"(\d{1,2}):(\d{2})(am|pm)?", s)
    if not m:
        return None
    try:
        hour = int(m.group(1))
        minute = int(m.group(2))
        suffix = m.group(3)
        if suffix == "pm" and hour != 12:
            hour += 12
        elif suffix == "am" and hour == 12:
            hour = 0
        if 0 <= hour < 24 and 0 <= minute < 60:
            return time(hour=hour, minute=minute)
    except ValueError:
        return None
    return None
