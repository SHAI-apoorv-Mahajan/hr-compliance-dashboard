# US-008 — Reject duplicate uploads for overlapping periods

**Epic:** Ingestion

## Story
- **As an** HR admin
- **I want** the system to reject a second upload of the same file type covering an overlapping period
- **So that** I don't accidentally double-ingest a month's data and corrupt the pipeline.

## Acceptance criteria
- **Given** an existing `bronze_uploads` row for `file_type='greythr'` covering `2026-04-01..2026-04-30`, **when** I `POST /api/v1/upload/greythr` for any period overlapping that range, **then** the response is HTTP 409 with `{"detail": "A greythr file for this period has already been uploaded. Delete it first to re-upload."}` and **no rows** are inserted into any table (FR-005).
- **Given** an existing biometric upload, **when** I try to re-upload biometric for the same period, **then** I receive the same 409 with `"A biometric file..."`.
- **Given** an existing roster upload, **when** I upload a new roster, **then** the upload is **allowed** (roster has no period — overwrites; per PRD §14.3 "upload once; update when policies change").
- **Given** an HR admin who wants to re-upload, **when** they `DELETE /api/v1/upload/{upload_id}`, **then** the bronze upload row and its dependent bronze rows are deleted, after which a fresh upload of that period succeeds.

## Dependencies
- US-005, US-006, US-007

## Estimate
**S** — Single pre-write guard query + delete endpoint.

## Linked FR-IDs
- FR-005

## Linked entities
- `bronze_uploads`, `bronze_greythr_raw`, `bronze_biometric_raw`, `bronze_roster_raw`

## Infrastructure dependencies
- DB indexes on `(file_type, period_start, period_end)` recommended for fast overlap check.
- Auth (JWT).
