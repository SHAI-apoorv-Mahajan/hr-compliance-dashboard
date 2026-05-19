"""SQLAlchemy engine, session factory, and Base.

Supabase pooler drops idle connections (PRD §13). pool_pre_ping + pool_recycle
keep the pool healthy without explicit reconnect logic in callers.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import get_settings

_settings = get_settings()

engine = create_engine(
    _settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
)


SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
