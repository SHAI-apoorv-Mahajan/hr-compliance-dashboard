"""Cross-dialect type definitions.

Production: PostgreSQL with native UUID and JSONB.
Tests: SQLite with CHAR(36) string-UUIDs and TEXT JSON.

Using `.with_variant(...)` keeps Postgres semantics unchanged while letting
the test suite materialize tables on SQLite.
"""

from __future__ import annotations

import uuid

from sqlalchemy import CHAR, JSON, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


class _UUIDCharType(TypeDecorator):
    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        try:
            return uuid.UUID(value)
        except (ValueError, AttributeError, TypeError):
            return value


def UUIDType():
    return PG_UUID(as_uuid=True).with_variant(_UUIDCharType(), "sqlite")


def JSONBType():
    return PG_JSONB().with_variant(JSON(), "sqlite")
