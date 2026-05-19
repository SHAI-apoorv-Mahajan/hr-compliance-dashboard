# US-006 — Biometric attendance file upload + block parser

**Epic:** Ingestion

## Story
- **As an** HR admin
- **I want** to upload the biometric daily attendance Excel for a period
- **So that** raw attendance, late-by minutes, and status flags are available for the silver pipeline.

## Acceptance criteria
- **Given** a biometric `.xlsx` file in the report-style block format, **when** I `POST /api/v1/upload/biometric` (multipart with `file`, `period_start`, `period_end`), **then** the parser implements the algorithm in PRD §14.2 exactly — `openpyxl.load_workbook(..., read_only=True, data_only=True)`, iterating from column B (index 1), identifying employee blocks via the `"Emp Code:"` marker, skipping the next-row column header, and ending blocks on `"Total Duration="` rows (FR-003).
- **Given** each data row, **when** parsed, **then** `att_date` parses with `%d-%b-%Y`, time strings (`"HH:MM"`) are stored verbatim in bronze, `status` values are `.strip()`-ed, the Unicode ½ (U+00BD) is preserved in `"½Present"` and `"½Present (No OutPunch)"`, and `work_duration_minutes`, `late_by_minutes`, `early_going_by_minutes` are converted via `hours*60 + minutes`.
- **Given** a row with a missing date or non-date marker, **when** parsed, **then** the row is skipped (parser continues with `continue`, no exception).
- **Given** an `NS` shift / `Absent` status row (Permanent WFH employee), **when** parsed, **then** the row is written to bronze as-is — no special filtering at ingest time.
- **Given** any required column is missing or unreadable, **when** parsing starts, **then** HTTP 422 is returned with a descriptive message and `bronze_uploads.error_message` is populated.

## Dependencies
- US-001, US-002, US-003

## Estimate
**L** — Block parser is the trickiest piece of the project; needs unit tests with synthetic .xlsx fixtures covering the marker row, header skip, summary row, ½ character, and trailing spaces.

## Linked FR-IDs
- FR-003

## Linked entities
- `bronze_uploads`, `bronze_biometric_raw`

## Infrastructure dependencies
- `openpyxl`, `pandas`.
- `/app/uploads` volume.
- Auth (JWT).
