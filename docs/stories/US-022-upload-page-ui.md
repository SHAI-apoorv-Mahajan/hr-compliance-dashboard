# US-022 — Upload page UI (three cards + history)

**Epic:** Ingestion

## Story
- **As an** HR admin
- **I want** an Upload page with three file-upload cards (GreytHR, Biometric, Roster) and a history table
- **So that** I can see what's been ingested for the period and what's still missing before running the pipeline.

## Acceptance criteria
- **Given** the page at `/upload`, **when** it loads, **then** I see three cards (GreytHR, Biometric, Roster), each showing: current status (uploaded ✓ / not yet ✗ for the selected period), last upload filename, last upload date, row count — sourced from `GET /api/v1/upload/history` (PRD §19 Page 3).
- **Given** a card, **when** I click "Upload" and choose a `.xlsx` file, **then** it POSTs to the relevant `/api/v1/upload/{type}` endpoint (with `period_start`/`period_end` from the period selector for GreytHR and Biometric, no period for Roster) and the card updates to reflect the new status on success.
- **Given** the upload history table at the bottom of the page, **when** rendered, **then** every `bronze_uploads` row is shown with file_type, filename, period, uploaded_at, row_count, status, and a Delete action.
- **Given** I click Delete on a history row, **when** the request returns 200, **then** the corresponding bronze child rows are removed and the row disappears from the table — making a re-upload for that period possible (US-008).
- **Given** a non-`.xlsx` file is chosen, **when** I try to upload, **then** the frontend rejects it client-side with a user-friendly message (no API call wasted).

## Dependencies
- US-005, US-006, US-007, US-008, US-012

## Estimate
**M** — Three near-identical cards + history table + delete confirmation modal + period selector.

## Linked FR-IDs
- Supports FR-002, FR-003, FR-004, FR-005, FR-018 (UI side of these).

## Linked entities
- `bronze_uploads`

## Infrastructure dependencies
- `/api/v1/upload/history`, `/api/v1/upload/{id}` DELETE, plus the three upload endpoints.
