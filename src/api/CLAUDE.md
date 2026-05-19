# src/api — FastAPI routers, Pydantic schemas, DI

Maps to `backend/routers/` and `backend/schemas/` in the runtime layout (PRD §22).

## Conventions
- One router file per resource: `auth.py`, `upload.py`, `pipeline.py`, `employees.py`, `attendance.py`, `leave.py`, `flags.py`, `email.py`, `settings.py`, `analytics.py`.
- Every router declares `prefix="/api/v1/<resource>"` and is registered once in `main.py`.
- Every non-auth route depends on `get_current_user` — never apply auth via global middleware. If you forget the dep, security-reviewer blocks the PR.
- Routers return Pydantic response models from `backend/schemas/` — never raw ORM rows.

## Error shape
Every error response is `{"detail": "..."}` only. No stack traces. Standard codes:
- 401: missing / expired token (FR-001)
- 409: duplicate-period upload (FR-005)
- 422: validation (missing Excel columns, malformed payload)
- 503: missing GRAPH_* env vars on `/email/send` (FR-014)

## DI patterns
- `get_db()` → SQLAlchemy session (yield + finally close).
- `get_current_user()` → `app_users` row, raises 401 on bad token.
- `get_email_service()` → returns the service even when Graph is unconfigured (the service itself returns 503 — endpoints don't pre-check env vars).

## File uploads
- `multipart/form-data`. `file: UploadFile`, `period_start: date`, `period_end: date` (omit period for roster).
- Reject non-`.xlsx` at the dependency layer before invoking the parser.

## Pagination
Not implemented in v1 (≤ 50 employees fits in one response). If a list grows, use cursor-based, not offset.
