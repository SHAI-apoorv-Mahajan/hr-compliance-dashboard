"""Dialect-aware upsert helper.

Production runs against PostgreSQL — we use INSERT ... ON CONFLICT DO UPDATE.
Tests run against SQLite — we use INSERT OR REPLACE semantics via a
SELECT-then-INSERT/UPDATE fallback.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session


def upsert(
    db: Session,
    *,
    model: Any,
    conflict_cols: list[str],
    values: dict[str, Any],
    update_cols: list[str] | None = None,
) -> None:
    """Insert `values` into `model`. On conflict on `conflict_cols`, update
    the listed `update_cols` (or every value column if not specified)."""
    update_cols = update_cols or [k for k in values.keys() if k not in conflict_cols]
    dialect_name = db.bind.dialect.name if db.bind else ""

    if dialect_name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        stmt = pg_insert(model).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_cols,
            set_={c: values[c] for c in update_cols},
        )
        db.execute(stmt)
        return

    # Generic fallback (SQLite for tests). Look up by conflict cols.
    q = db.query(model)
    for c in conflict_cols:
        q = q.filter(getattr(model, c) == values[c])
    existing = q.first()
    if existing:
        for c in update_cols:
            setattr(existing, c, values[c])
    else:
        db.add(model(**values))
