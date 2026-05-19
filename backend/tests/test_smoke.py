"""US-004 smoke test."""


def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_seed_thresholds_present(seeded_db):
    from models import AppFlagThreshold

    n = seeded_db.query(AppFlagThreshold).count()
    assert n == 9


def test_seed_templates_present(seeded_db):
    from models import AppEmailTemplate

    n = seeded_db.query(AppEmailTemplate).count()
    assert n == 8


def test_seed_idempotent(seeded_db):
    from seed import seed_defaults
    from models import AppFlagThreshold, AppEmailTemplate, AppUser

    seed_defaults(seeded_db)  # run a second time
    assert seeded_db.query(AppUser).count() == 1
    assert seeded_db.query(AppEmailTemplate).count() == 8
    assert seeded_db.query(AppFlagThreshold).count() == 9
