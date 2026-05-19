# US-019 — Editable flag thresholds in Settings

**Epic:** Settings

## Story
- **As an** HR admin
- **I want** to view and update the 9 flag thresholds from Settings
- **So that** I can tune the system to ShortHills Tech's evolving compliance bar.

## Acceptance criteria
- **Given** the Flag Thresholds tab, **when** it loads, **then** I see a table of all 9 rows from `app_flag_thresholds` with `flag_type`, current `threshold_value`, `threshold_unit`, and `description` (FR-016).
- **Given** a row, **when** I edit `threshold_value` and click Save, **then** `PUT /api/v1/settings/thresholds/{flag_type}` updates the row and `updated_at` advances; client receives HTTP 200 with the updated row (FR-016).
- **Given** the threshold change, **when** I re-run the pipeline (or `/api/v1/flags/recompute`), **then** the new threshold takes effect on the next run (FR-016).
- **Given** existing flags from a previous run, **when** the threshold changes, **then** those flags are **not** retroactively modified — only the next run reflects the new value (FR-016).
- **Given** an invalid `threshold_value` (negative, non-numeric), **when** I save, **then** I receive HTTP 422 with a clear message and the row is unchanged.

## Dependencies
- US-002, US-011

## Estimate
**S** — Two endpoints (GET list, PUT one) + a table UI.

## Linked FR-IDs
- FR-016

## Linked entities
- `app_flag_thresholds`

## Infrastructure dependencies
- `/api/v1/settings/thresholds`, `/api/v1/settings/thresholds/{flag_type}`.
