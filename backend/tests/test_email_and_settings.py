"""US-017/18/19 — Email config-status, template CRUD, threshold settings."""


def test_config_status_unconfigured(auth_client):
    r = auth_client.get("/api/v1/email/config-status")
    assert r.status_code == 200
    body = r.json()
    assert body["configured"] is False
    assert "GRAPH_TENANT_ID" in body["missing"]
    assert "GRAPH_CLIENT_ID" in body["missing"]
    assert "GRAPH_CLIENT_SECRET" in body["missing"]


def test_send_returns_503_when_unconfigured(auth_client, db):
    # Need a flag + a template to even attempt send.
    from models import AppEmailTemplate, GoldEmployeeFlag

    template = db.query(AppEmailTemplate).first()
    assert template is not None

    flag = GoldEmployeeFlag(
        emp_code="E001",
        employee_name="Alice",
        flag_type="LATE_ARRIVAL",
        flag_value=4,
        threshold_value=3,
        flag_details={"dates": ["2026-04-01"]},
    )
    db.add(flag)
    db.commit()
    db.refresh(flag)

    r = auth_client.post(
        "/api/v1/email/send",
        json={
            "flag_ids": [str(flag.id)],
            "template_id": str(template.id),
            "preview_only": False,
        },
    )
    assert r.status_code == 503
    assert "Email service is not configured" in r.json()["detail"]


def test_send_preview_works_without_graph(auth_client, db):
    from models import AppEmailTemplate, GoldEmployeeFlag, SilverEmployee

    template = (
        db.query(AppEmailTemplate)
        .filter(AppEmailTemplate.flag_type == "LATE_ARRIVAL")
        .first()
    )
    assert template is not None

    db.add(SilverEmployee(emp_code="E001", name="Alice Doe", email="alice@example.com"))
    flag = GoldEmployeeFlag(
        emp_code="E001",
        employee_name="Alice Doe",
        flag_type="LATE_ARRIVAL",
        flag_value=4,
        threshold_value=3,
        flag_details={"dates": ["2026-04-01", "2026-04-02"]},
    )
    db.add(flag)
    db.commit()
    db.refresh(flag)

    r = auth_client.post(
        "/api/v1/email/send",
        json={
            "flag_ids": [str(flag.id)],
            "template_id": str(template.id),
            "preview_only": True,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert "Alice Doe" in body[0]["body"]
    assert "{{" not in body[0]["body"]  # all variables substituted
    assert body[0]["recipient_email"] == "alice@example.com"


def test_template_crud(auth_client):
    # Create.
    r = auth_client.post(
        "/api/v1/email/templates",
        json={
            "name": "Custom WFO Notice",
            "flag_type": "WFO_VIOLATION",
            "subject": "WFO compliance — {{period}}",
            "body": "Hi {{employee_name}}, please follow WFO rules.",
        },
    )
    assert r.status_code == 201
    tid = r.json()["id"]

    # Update.
    r = auth_client.put(
        f"/api/v1/email/templates/{tid}",
        json={
            "name": "Custom WFO Notice v2",
            "flag_type": "WFO_VIOLATION",
            "subject": "WFO compliance",
            "body": "Hi {{employee_name}}.",
        },
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Custom WFO Notice v2"

    # Delete (no email log references → hard delete).
    r = auth_client.delete(f"/api/v1/email/templates/{tid}")
    assert r.status_code == 204


def test_threshold_update(auth_client):
    r = auth_client.get("/api/v1/settings/thresholds")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 9

    r = auth_client.put(
        "/api/v1/settings/thresholds/LATE_ARRIVAL",
        json={"threshold_value": 5},
    )
    assert r.status_code == 200
    assert r.json()["threshold_value"] == 5.0


def test_negative_threshold_rejected(auth_client):
    r = auth_client.put(
        "/api/v1/settings/thresholds/LATE_ARRIVAL",
        json={"threshold_value": -1},
    )
    assert r.status_code == 422
