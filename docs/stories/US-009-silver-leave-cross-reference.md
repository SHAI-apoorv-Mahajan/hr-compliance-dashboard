# US-009 — Silver pipeline: cross-reference absences against approved leave

**Epic:** Pipeline

## Story
- **As an** HR admin
- **I want** absent biometric records cross-referenced against GreytHR Availed leave
- **So that** an absence covered by an approved leave is not later flagged as a violation.

## Acceptance criteria
- **Given** a biometric record with `is_absent = TRUE` and `is_weekly_off = FALSE`, **when** the silver pipeline runs and a `silver_leave_transactions` row exists for the same `emp_code` with `transaction_type = 'Availed'` where `from_date ≤ att_date ≤ to_date`, **then** `silver_daily_attendance.has_approved_leave = TRUE` and `approved_leave_type` is set to the matching `leave_type` (FR-006).
- **Given** the same absent record but no matching Availed leave, **when** the pipeline runs, **then** `has_approved_leave = FALSE` and `approved_leave_type` is NULL.
- **Given** an employee with `is_permanent_wfh = TRUE`, **when** the silver pipeline runs, **then** cross-reference is **skipped** for their absence rows — `has_approved_leave` stays its default (FALSE) and these rows must not produce ABSENT_WITHOUT_LEAVE, WFO_VIOLATION, or LATE_ARRIVAL flags downstream (FR-007).
- **Given** the pipeline is re-run for the same period, **when** silver writes complete, **then** `silver_daily_attendance` is regenerated (upsert keyed on `(emp_code, att_date, upload_id)`) — no duplicate rows.
- **Given** silver runs, **when** logging occurs, **then** each stage transition emits an ISO-timestamped stdout line with row counts (NFR-009).

## Dependencies
- US-005, US-006, US-007

## Estimate
**L** — Cross-reference join + time string → TIME conversion + derived boolean computation + permanent-WFH branch.

## Linked FR-IDs
- FR-006, FR-007

## Linked entities
- `silver_leave_transactions`, `silver_daily_attendance`, `silver_employees`

## Infrastructure dependencies
- Index on `silver_leave_transactions(emp_code, transaction_type, from_date, to_date)` for the cross-reference join.
