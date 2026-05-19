"""Test fixtures.

Backend tests run against a per-test SQLite in-memory database. Model column
types use `.with_variant()` (see models/_types.py) so JSONB → JSON and UUID →
CHAR(36) automatically on SQLite while preserving Postgres semantics in prod.

Env vars are forced BEFORE importing any backend module.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-with-sufficient-length-xx")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_HOURS", "24")
os.environ.setdefault("GRAPH_TENANT_ID", "")
os.environ.setdefault("GRAPH_CLIENT_ID", "")
os.environ.setdefault("GRAPH_CLIENT_SECRET", "")
os.environ.setdefault("GRAPH_SENDER_EMAIL", "")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture
def engine():
    from database import Base

    # StaticPool: every connection shares one in-memory DB.
    eng = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def db(engine):
    Session = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )
    s = Session()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def seeded_db(db):
    """A DB with the default HR user + 8 templates + 9 thresholds (FR-017)."""
    from seed import seed_defaults

    seed_defaults(db)
    return db


@pytest.fixture
def client(engine, monkeypatch):
    """FastAPI TestClient wired to the in-memory engine."""
    from fastapi.testclient import TestClient

    import database as db_mod
    from seed import seed_defaults

    Session = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )
    monkeypatch.setattr(db_mod, "SessionLocal", Session)
    monkeypatch.setattr(db_mod, "engine", engine)

    seed_db = Session()
    try:
        seed_defaults(seed_db)
    finally:
        seed_db.close()

    from main import app

    def _override_get_db():
        s = Session()
        try:
            yield s
        finally:
            s.close()

    from database import get_db

    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client):
    """A TestClient whose default headers include a valid JWT for the seeded HR user."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "hr@shorthills.ai", "password": "HR@ShortHills2024"},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
