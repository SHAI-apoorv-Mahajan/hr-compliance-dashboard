# US-010 — Gold pipeline: per-employee period statistics

**Epic:** Pipeline

## Story
- **As an** HR admin
- **I want** `gold_period_stats` computed per employee per period
- **So that** the dashboard, employee detail, and flag engine all read from one canonical aggregate.

## Acceptance criteria
- **Given** silver tables populated for a period, **when** the gold pipeline runs, **then** one `gold_period_stats` row exists per `(emp_code, period_start, period_end)` with: `total_working_days`, `present_days` (sum of Present + 0.5×½Present), `absent_days`, `absent_without_leave_days`, `late_arrival_count`, `early_departure_count`, `no_out_punch_count`, `half_day_count`, `wfh_days_availed` (from Availed `leave_type='WFH'`), `wfh_credits_allocated` (from `silver_employees.wfh_credits_monthly`), `total_work_minutes`, `avg_daily_work_minutes` (FR-008).
- **Given** the same period is re-processed, **when** the gold pipeline runs again, **then** the existing row is updated in place (upsert keyed on `(emp_code, period_start, period_end)`) — no duplicates appear (FR-008 idempotency).
- **Given** an employee with zero attendance rows (no biometric data for the period), **when** stats are computed, **then** the employee is **not** present in `gold_period_stats` for that period.
- **Given** `leave_summary` JSONB, **when** populated, **then** it contains a per-leave-type breakdown: `{"WFH": 4, "Earned Leave": 2, ...}`.
- **Given** the pipeline finishes, **when** I `GET /api/v1/pipeline/status/{period_start}/{period_end}`, **then** I receive a JSON shape summarizing rows processed per stage.

## Dependencies
- US-009

## Estimate
**L** — Multiple aggregations + upsert + JSON construction + status endpoint.

## Linked FR-IDs
- FR-008

## Linked entities
- `gold_period_stats`, `silver_daily_attendance`, `silver_leave_transactions`, `silver_employees`

## Infrastructure dependencies
- Unique constraint `(emp_code, period_start, period_end)` from US-002.
