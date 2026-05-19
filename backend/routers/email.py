"""Email router. FR-013/14/15/19, US-016/17/18/20."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from config import get_settings
from database import get_db
from models import (
    AppEmailLog,
    AppEmailTemplate,
    AppUser,
    GoldEmployeeFlag,
    SilverEmployee,
)
from routers.deps import get_current_user
from schemas.email import (
    ConfigStatus,
    EmailLogOut,
    RenderedEmail,
    SendRequest,
    SendResult,
    TemplateIn,
    TemplateOut,
)
from services.email_service import (
    assert_graph_configured,
    build_vars_for_flag,
    fetch_graph_token,
    graph_send,
    log_send_attempt,
    render,
)

router = APIRouter(prefix="/api/v1/email", tags=["email"])


# ---- config-status (FR-014, US-017) ---------------------------------------


@router.get("/config-status", response_model=ConfigStatus)
def config_status(_user: AppUser = Depends(get_current_user)) -> ConfigStatus:
    s = get_settings()
    missing = []
    if not s.GRAPH_TENANT_ID:
        missing.append("GRAPH_TENANT_ID")
    if not s.GRAPH_CLIENT_ID:
        missing.append("GRAPH_CLIENT_ID")
    if not s.GRAPH_CLIENT_SECRET:
        missing.append("GRAPH_CLIENT_SECRET")
    return ConfigStatus(configured=not missing, missing=missing)


# ---- templates CRUD (FR-015, US-018) --------------------------------------


@router.get("/templates", response_model=list[TemplateOut])
def list_templates(
    include_inactive: bool = Query(default=False),
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> list[AppEmailTemplate]:
    q = db.query(AppEmailTemplate)
    if not include_inactive:
        q = q.filter(AppEmailTemplate.is_active.is_(True))
    return q.order_by(AppEmailTemplate.name).all()


@router.post("/templates", response_model=TemplateOut, status_code=201)
def create_template(
    payload: TemplateIn,
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> AppEmailTemplate:
    t = AppEmailTemplate(
        name=payload.name,
        flag_type=payload.flag_type,
        subject=payload.subject,
        body=payload.body,
        available_variables=[
            "employee_name",
            "emp_code",
            "period",
            "period_start",
            "period_end",
            "flag_count",
            "flag_dates",
            "threshold",
            "sender_name",
        ],
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.put("/templates/{template_id}", response_model=TemplateOut)
def update_template(
    template_id: UUID,
    payload: TemplateIn,
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> AppEmailTemplate:
    t = db.get(AppEmailTemplate, template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    t.name = payload.name
    t.flag_type = payload.flag_type
    t.subject = payload.subject
    t.body = payload.body
    db.commit()
    db.refresh(t)
    return t


@router.delete("/templates/{template_id}", status_code=204, response_class=Response)
def delete_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> Response:
    t = db.get(AppEmailTemplate, template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    # If referenced in app_email_log, soft-delete; otherwise hard-delete (FR-015).
    referenced = (
        db.query(AppEmailLog).filter(AppEmailLog.template_id == template_id).first()
    )
    if referenced:
        t.is_active = False
        db.commit()
    else:
        db.delete(t)
        db.commit()
    return Response(status_code=204)


# ---- send (FR-013/14, US-016) ---------------------------------------------


@router.post("/send", response_model=list[SendResult] | list[RenderedEmail])
def send(
    payload: SendRequest,
    current: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = db.get(AppEmailTemplate, payload.template_id)
    if not template or not template.is_active:
        raise HTTPException(status_code=404, detail="Template not found")

    flags = (
        db.query(GoldEmployeeFlag)
        .filter(GoldEmployeeFlag.id.in_(payload.flag_ids))
        .all()
    )
    if not flags:
        raise HTTPException(status_code=404, detail="No flags found for given flag_ids")

    employees = {e.emp_code: e for e in db.query(SilverEmployee).all() if e.emp_code}

    # Dedup: one email per (flag_type, emp_code) per send batch (FR-013).
    chosen: dict[tuple[str, str], GoldEmployeeFlag] = {}
    for f in flags:
        key = (f.flag_type or "", f.emp_code or "")
        if key not in chosen:
            chosen[key] = f

    rendered: list[RenderedEmail] = []
    for f in chosen.values():
        emp = employees.get(f.emp_code) if f.emp_code else None
        vars = build_vars_for_flag(f, emp)
        subject, body = render(template.subject, template.body, vars)
        rendered.append(
            RenderedEmail(
                flag_id=f.id,
                emp_code=f.emp_code,
                recipient_email=emp.email if emp else None,
                subject=subject,
                body=body,
            )
        )

    if payload.preview_only:
        return rendered

    assert_graph_configured()
    token = fetch_graph_token()

    results: list[SendResult] = []
    for f, r in zip(chosen.values(), rendered):
        if not r.recipient_email:
            log_send_attempt(
                db,
                flag=f,
                template=template,
                recipient="",
                subject=r.subject,
                body=r.body,
                status="failed",
                error="Employee has no email on record",
                sent_by=current.email,
            )
            results.append(
                SendResult(
                    flag_id=f.id,
                    emp_code=f.emp_code,
                    recipient_email=None,
                    status="failed",
                    error_message="Employee has no email on record",
                )
            )
            continue
        ok, err = graph_send(token, r.recipient_email, r.subject, r.body)
        status_val = "sent" if ok else "failed"
        log_send_attempt(
            db,
            flag=f,
            template=template,
            recipient=r.recipient_email,
            subject=r.subject,
            body=r.body,
            status=status_val,
            error=err,
            sent_by=current.email,
        )
        results.append(
            SendResult(
                flag_id=f.id,
                emp_code=f.emp_code,
                recipient_email=r.recipient_email,
                status=status_val,
                error_message=err,
            )
        )

    db.commit()
    return results


# ---- email logs (FR-019, US-020) ------------------------------------------


@router.get("/logs", response_model=list[EmailLogOut])
def list_logs(
    emp_code: str | None = Query(default=None),
    period_start: date | None = Query(default=None),
    period_end: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
) -> list[AppEmailLog]:
    q = db.query(AppEmailLog)
    if emp_code:
        q = q.filter(AppEmailLog.emp_code == emp_code)
    if period_start and period_end:
        # period filter joins via flag
        q = q.join(
            GoldEmployeeFlag, AppEmailLog.flag_id == GoldEmployeeFlag.id, isouter=True
        ).filter(
            GoldEmployeeFlag.period_start == period_start,
            GoldEmployeeFlag.period_end == period_end,
        )
    return q.order_by(AppEmailLog.created_at.desc()).limit(500).all()
