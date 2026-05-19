# API design

## Prefix and versioning
- All routes prefixed `/api/v1`. The version is part of the URL; breaking changes ship under `/api/v2`.

## Response shape
- Success: the resource (or `{}` for void operations) — no envelope.
- Error: `{"detail": "human-readable message"}` only. Match the FR-specified text when one is defined (FR-001 401, FR-005 409, FR-014 503).

## Status codes
- 200 OK for successful reads and updates.
- 201 Created for new resources.
- 204 No Content for successful deletes (no body).
- 401 for missing/expired JWT.
- 403 reserved for future role-based access (single HR admin in v1, so 403 is rare).
- 409 for duplicate-period uploads (FR-005).
- 422 for validation errors (missing Excel columns, malformed input).
- 503 for missing Graph credentials (FR-014).

## Pydantic schemas
- `schemas/` holds request/response models. Routers import these — never expose SQLAlchemy ORM objects directly.
- Use `ConfigDict(from_attributes=True)` for response models derived from ORM rows.

## File uploads
- All upload endpoints are `multipart/form-data` with `file`, `period_start`, `period_end` (where applicable).
- Reject non-`.xlsx` content types at the dependency layer before the parser runs.
- Use `python-multipart` (already in requirements).

## Pagination
- Not required for v1 — at ≤ 50 employees × 31 days, all lists fit in one response.
- If a future list grows: cursor-based pagination via `?cursor=&limit=`, never offset.

## Idempotency
- Pipeline endpoints are idempotent (FR-008, FR-009). Re-running `POST /api/v1/pipeline/run` for the same period must produce the same gold rows.

## Authorization
- The `get_current_user` FastAPI dependency injects the authenticated user. Routers depend on it explicitly — there is no global middleware that magically protects everything.
