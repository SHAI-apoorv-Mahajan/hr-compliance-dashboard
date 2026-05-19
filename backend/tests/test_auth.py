"""US-003 / FR-001 auth tests."""


def test_login_success(client):
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "hr@shorthills.ai", "password": "HR@ShortHills2024"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and len(body["access_token"]) > 20


def test_login_wrong_password(client):
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "hr@shorthills.ai", "password": "wrong"},
    )
    assert r.status_code == 401
    assert r.json() == {"detail": "Invalid email or password"}


def test_login_unknown_email(client):
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "password": "whatever"},
    )
    assert r.status_code == 401
    assert r.json() == {"detail": "Invalid email or password"}


def test_me_requires_auth(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_me_returns_user(auth_client):
    r = auth_client.get("/api/v1/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == "hr@shorthills.ai"
    assert r.json()["role"] == "hr"


def test_other_routes_require_auth(client):
    for path in [
        "/api/v1/employees",
        "/api/v1/upload/history",
        "/api/v1/settings/thresholds",
        "/api/v1/email/templates",
    ]:
        r = client.get(path)
        assert r.status_code == 401, f"{path} should require auth"


def test_last_login_updated(client, db):
    from models import AppUser

    before = db.query(AppUser).first().last_login
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "hr@shorthills.ai", "password": "HR@ShortHills2024"},
    )
    assert r.status_code == 200
    after = db.query(AppUser).first()
    db.refresh(after)
    assert after.last_login is not None
    assert before != after.last_login or before is None
