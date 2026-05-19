# US-012 — Pipeline trigger endpoint + UI button

**Epic:** Pipeline

## Story
- **As an** HR admin
- **I want** to trigger the full medallion pipeline for a given period from the Upload page
- **So that** I can refresh dashboard data after uploading the month's files.

## Acceptance criteria
- **Given** both biometric and GreytHR uploads exist for a period, **when** HR clicks "Run Pipeline" on `/upload`, **then** the frontend calls `POST /api/v1/pipeline/run` with `{period_start, period_end}` and the backend runs bronze→silver→gold in sequence, returning a JSON summary (`{stage: rows_processed}`) on completion (FR-018).
- **Given** either upload is missing for the period, **when** the page renders, **then** the "Run Pipeline" button is **disabled** with a tooltip explaining which file is missing (FR-018).
- **Given** the pipeline is running, **when** HR watches the UI, **then** a progress indicator updates without a full page refresh (poll `/api/v1/pipeline/status/...` or stream).
- **Given** the pipeline succeeds, **when** complete, **then** total wall-clock time for ≤50 employees × ≤31 days is under 30 seconds (NFR-003).
- **Given** an error occurs mid-pipeline, **when** the failure is caught, **then** the affected `bronze_uploads.error_message` is updated, the API returns HTTP 500 with `{"detail": "Pipeline failed at <stage>: <message>"}` (no Python traceback per NFR-005), and the UI shows the message in a banner.

## Dependencies
- US-009, US-010, US-011

## Estimate
**M** — Endpoint orchestration + frontend polling + error surfacing.

## Linked FR-IDs
- FR-018

## Linked entities
- `bronze_uploads`, `silver_*`, `gold_*`

## Infrastructure dependencies
- Auth (JWT).
