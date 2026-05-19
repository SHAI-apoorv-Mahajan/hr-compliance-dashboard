# US-007 — Roster file upload + silver_employees upsert

**Epic:** Ingestion

## Story
- **As an** HR admin
- **I want** to upload the team roster Excel once (or whenever policies change)
- **So that** `silver_employees` is populated with working model, schedule, WFH credits, and InTime deadline data.

## Acceptance criteria
- **Given** a roster `.xlsx` with the exact columns from PRD §14.3 (including the typo `"Intime window onpen till"`), **when** I `POST /api/v1/upload/roster` (multipart with `file` only — no period), **then** every data row is written to `bronze_roster_raw` and upserted into `silver_employees` matched by normalized name (`" ".join(name.split())`, case-insensitive) (FR-004).
- **Given** an employee with `Working Model = "Permanent WFH"`, **when** upserted, **then** `silver_employees.is_permanent_wfh = TRUE`.
- **Given** an `Intime window onpen till` value like `"10:30am"`, **when** parsed, **then** `intime_deadline` is set to TIME `10:30:00`; **given** a non-parseable value (e.g., a free-text rotational comment), **then** `intime_deadline` is NULL.
- **Given** an existing `silver_employees` row matched by name, **when** the roster is re-uploaded, **then** that row is updated in place (not duplicated), `roster_upload_id` is set to the latest upload, and `updated_at` advances.
- **Given** a row where `WFH Credits` is blank (intern case — Bhavya Mendiratta, Apoorv Mahajan), **when** parsed, **then** `wfh_credits_monthly` defaults to `0` (PRD §27 quirk #6).
- **Given** a missing required column, **when** uploading, **then** HTTP 422 is returned with the missing-column message and no DB writes occur.

## Dependencies
- US-001, US-002, US-003

## Estimate
**M** — Flat-table parse, but name normalization + upsert + intime parsing all need coverage.

## Linked FR-IDs
- FR-004

## Linked entities
- `bronze_uploads`, `bronze_roster_raw`, `silver_employees`

## Infrastructure dependencies
- `pandas`, `openpyxl`.
- Auth (JWT).
