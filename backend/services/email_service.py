"""Email service. FR-013, FR-014.

Microsoft Graph client-credentials flow. Gracefully returns HTTP 503 when
any of the three GRAPH_* env vars is empty. Never crashes.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from config import get_settings
from models import AppEmailLog, AppEmailTemplate, GoldEmployeeFlag, SilverEmployee

log = logging.getLogger(__name__)


SENDER_NAME = "HR Team, ShortHills Tech"

_VAR_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def assert_graph_configured() -> None:
    s = get_settings()
    if not s.graph_configured:
        raise HTTPException(
            status_code=503,
            detail=(
                "Email service is not configured. Please set GRAPH_TENANT_ID, "
                "GRAPH_CLIENT_ID, and GRAPH_CLIENT_SECRET in the environment."
            ),
        )


def render(
    template_subject: str, template_body: str, vars: dict[str, str]
) -> tuple[str, str]:
    def sub(s: str) -> str:
        return _VAR_RE.sub(lambda m: str(vars.get(m.group(1), m.group(0))), s)

    return sub(template_subject), sub(template_body)


def build_vars_for_flag(
    flag: GoldEmployeeFlag, emp: SilverEmployee | None
) -> dict[str, str]:
    dates: list[str] = []
    details = flag.flag_details or {}
    if isinstance(details, dict) and isinstance(details.get("dates"), list):
        dates = [str(d) for d in details["dates"]]
    period = ""
    if flag.period_start and flag.period_end:
        period = f"{flag.period_start.strftime('%b %Y')}"

    return {
        "employee_name": (emp.name if emp else flag.employee_name) or "",
        "emp_code": flag.emp_code or "",
        "period": period,
        "period_start": flag.period_start.isoformat() if flag.period_start else "",
        "period_end": flag.period_end.isoformat() if flag.period_end else "",
        "flag_count": str(int(flag.flag_value) if flag.flag_value is not None else ""),
        "flag_dates": ", ".join(dates),
        "threshold": str(
            int(flag.threshold_value) if flag.threshold_value is not None else ""
        ),
        "sender_name": SENDER_NAME,
    }


def fetch_graph_token() -> str:
    s = get_settings()
    url = f"https://login.microsoftonline.com/{s.GRAPH_TENANT_ID}/oauth2/v2.0/token"
    data = {
        "client_id": s.GRAPH_CLIENT_ID,
        "client_secret": s.GRAPH_CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }
    with httpx.Client(timeout=20.0) as client:
        resp = client.post(url, data=data)
    if resp.status_code != 200:
        log.error(
            "graph token fetch failed: status=%s body=%s",
            resp.status_code,
            resp.text[:500],
        )
        raise HTTPException(
            status_code=502, detail="Could not obtain Microsoft Graph access token"
        )
    return resp.json()["access_token"]


def graph_send(
    token: str, recipient: str, subject: str, body: str
) -> tuple[bool, str | None]:
    s = get_settings()
    url = f"https://graph.microsoft.com/v1.0/users/{s.GRAPH_SENDER_EMAIL}/sendMail"
    payload = {
        "message": {
            "subject": subject,
            "body": {"contentType": "Text", "content": body},
            "toRecipients": [{"emailAddress": {"address": recipient}}],
        },
        "saveToSentItems": "true",
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, json=payload, headers=headers)
    if 200 <= resp.status_code < 300:
        return True, None
    log.error(
        "graph sendMail failed: status=%s body=%s", resp.status_code, resp.text[:800]
    )
    return False, f"HTTP {resp.status_code}: {resp.text[:500]}"


def log_send_attempt(
    db: Session,
    *,
    flag: GoldEmployeeFlag,
    template: AppEmailTemplate,
    recipient: str,
    subject: str,
    body: str,
    status: str,
    error: Optional[str],
    sent_by: str,
) -> AppEmailLog:
    log_row = AppEmailLog(
        flag_id=flag.id,
        template_id=template.id,
        emp_code=flag.emp_code,
        recipient_email=recipient,
        subject=subject,
        body_preview=body[:500],
        status=status,
        error_message=error,
        sent_at=datetime.now(timezone.utc) if status == "sent" else None,
        sent_by=sent_by,
    )
    db.add(log_row)
    if status == "sent":
        flag.email_sent = True
        flag.email_sent_at = log_row.sent_at
    return log_row
