# US-005 — GreytHR leave file upload + parser

**Epic:** Ingestion

## Story
- **As an** HR admin
- **I want** to upload the GreytHR leave Excel for a period
- **So that** approved leave data is available for the silver pipeline's absence cross-referencing.

## Acceptance criteria
- **Given** a valid GreytHR `.xlsx` file with the columns listed in PRD §14.1, **when** I `POST /api/v1/upload/greythr` (multipart with `file`, `period_start`, `period_end`), **then** a row is inserted into `bronze_uploads` (`file_type='greythr'`, `status='processing'`), every data row is parsed and written to `bronze_greythr_raw`, `From Date` and `To Date` are converted from Excel serial integers via `datetime(1899,12,30) + timedelta(days=int(serial))` (FR-002), and `bronze_uploads.status` ends at `'processed'` with `row_count` populated.
- **Given** an uploaded file, **when** parsing finishes, **then** `Posted Date` is parsed via `pd.to_datetime`, `Expire Date` is nullable, and `Days` decimals (e.g., `0.5`) are preserved as `NUMERIC(5,2)`.
- **Given** a file missing one of the required columns, **when** I upload, **then** the response is HTTP 422 with a clear column-level message, and no rows are written to bronze tables.
- **Given** a file whose row contains an unparseable serial, **when** parsing runs, **then** that row's `from_date`/`to_date` is NULL and the parser continues (per NFR-009 — surface error to `bronze_uploads.error_message` if anything failed).
- **Given** a non-`.xlsx` file, **when** I upload, **then** the response is HTTP 422 with `{"detail": "Only .xlsx files are accepted"}`.

## Dependencies
- US-001, US-002, US-003

## Estimate
**M** — Standard parser + endpoint, but the serial-date conversion and column validation deserve real tests.

## Linked FR-IDs
- FR-002

## Linked entities
- `bronze_uploads`, `bronze_greythr_raw`

## Infrastructure dependencies
- `pandas`, `openpyxl`, `python-multipart`.
- `/app/uploads` volume mounted (per docker-compose).
- Auth (JWT required).
