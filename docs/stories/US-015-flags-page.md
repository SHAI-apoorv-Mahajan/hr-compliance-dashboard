# US-015 — Flagged employees page (filter, resolve, bulk select)

**Epic:** Compliance UI

## Story
- **As an** HR admin
- **I want** a flags page where I can filter, resolve, and bulk-select flags
- **So that** I can quickly act on the violations I care about and tee up email sends.

## Acceptance criteria
- **Given** the page at `/flags`, **when** it loads, **then** I see a filter bar (flag type, employee, period) and a table of `gold_employee_flags` rows where `is_active = TRUE` (FR-012).
- **Given** the table, **when** rendered, **then** columns include: Employee, Flag Type, Flag Value, Threshold, Dates Affected (from `flag_details`), Email Sent, Actions (Send Email, Mark Resolved) (FR-012).
- **Given** I click "Mark Resolved" on a flag, **when** the request succeeds, **then** `PATCH /api/v1/flags/{flag_id}/resolve` is called, `is_active` is set to `FALSE`, and the row disappears from the default view (FR-012).
- **Given** I bulk-select multiple flags, **when** I click "Send Bulk Emails", **then** I'm navigated to (or modal-opened to) the email send flow (US-018) pre-populated with the selected flag IDs.
- **Given** changed thresholds, **when** I `POST /api/v1/flags/recompute` for the period, **then** the gold flag engine reruns over existing silver/gold data without touching bronze.

## Dependencies
- US-011

## Estimate
**M** — Filter bar + table + resolve PATCH + bulk-select wiring.

## Linked FR-IDs
- FR-012

## Linked entities
- `gold_employee_flags`, `silver_employees`

## Infrastructure dependencies
- `/api/v1/flags`, `/api/v1/flags/{id}/resolve`, `/api/v1/flags/recompute`.
