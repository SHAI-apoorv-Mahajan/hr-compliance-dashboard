# US-011 — Gold pipeline: 9-flag evaluation engine

**Epic:** Pipeline

## Story
- **As an** HR admin
- **I want** the gold stage to evaluate all 9 flag types against the editable thresholds
- **So that** `gold_employee_flags` reflects every current violation, refreshed idempotently on every run.

## Acceptance criteria
- **Given** thresholds in `app_flag_thresholds` and silver/gold tables populated, **when** the flag engine runs, **then** each of the 9 flag types is evaluated per PRD §17 rules (LATE_ARRIVAL, EARLY_DEPARTURE, ABSENT_WITHOUT_LEAVE, CONSECUTIVE_ABSENCE, NO_OUT_PUNCH, HALF_DAY_FREQUENCY, WFH_QUOTA_EXCEEDED, LOW_WORK_HOURS, WFO_VIOLATION) and written to `gold_employee_flags` with `flag_value`, `threshold_value`, and `flag_details` JSONB listing affected dates (FR-009).
- **Given** an employee with `is_permanent_wfh = TRUE`, **when** flag evaluation runs, **then** no LATE_ARRIVAL, ABSENT_WITHOUT_LEAVE, or WFO_VIOLATION flags are produced for them (FR-007).
- **Given** CONSECUTIVE_ABSENCE evaluation, **when** computing the run length, **then** WeeklyOff days are skipped (treated as transparent, not as breaks) and the longest absent-without-leave run ≥ threshold triggers the flag (PRD §17).
- **Given** the pipeline is re-run, **when** the flag engine writes, **then** existing flags for `(emp_code, flag_type, period_start)` are updated, not duplicated (FR-009); flags that no longer apply have their `is_active` left as the HR admin set it (do not auto-resurrect resolved flags).
- **Given** WFH_QUOTA_EXCEEDED, **when** evaluating, **then** `flag_value` = excess days = `availed - wfh_credits_monthly`, `threshold_value` = `wfh_credits_monthly`.
- **Given** LOW_WORK_HOURS, **when** evaluating, **then** any present day with `work_duration_minutes < threshold` counts; `flag_value` = number of such days; threshold = 300 minutes by default.

## Dependencies
- US-010

## Estimate
**XL** — 9 separate evaluation paths, each with edge cases (permanent WFH skip, consecutive run, WFH excess, schedule-day lookup for WFO).

## Per-flag-type sub-tasks (one PR each, ship in this order)

Each sub-task: build one flag function in `backend/services/flag_engine.py`, wire it into the dispatcher, add one pytest module, and verify idempotency.

| # | Sub-task | Effort | Dependency on sibling | Notes |
|---|---|---|---|---|
| 11a | Engine skeleton + dispatcher + `gold_employee_flags` upsert helper | S | — | The upsert keyed on `(emp_code, flag_type, period_start)` lives here. All later sub-tasks call into it. |
| 11b | **LATE_ARRIVAL** | S | 11a | `late_by_minutes > 0` AND status contains `Present`; skip Permanent WFH (FR-007). |
| 11c | **EARLY_DEPARTURE** | S | 11a | `early_going_by_minutes > 0` AND status contains `Present`. |
| 11d | **NO_OUT_PUNCH** | S | 11a | `is_no_out_punch = TRUE`. |
| 11e | **HALF_DAY_FREQUENCY** | S | 11a | `is_half_present = TRUE`. |
| 11f | **LOW_WORK_HOURS** | S | 11a | Present day with `work_duration_minutes < threshold`; `flag_value` = count of such days. |
| 11g | **ABSENT_WITHOUT_LEAVE** | M | 11a | `is_absent` AND NOT `is_weekly_off` AND NOT `has_approved_leave` AND NOT `is_permanent_wfh`. |
| 11h | **CONSECUTIVE_ABSENCE** | M | 11g | Reuse 11g's absent-without-leave set; longest run; WeeklyOff transparent (skipped, not break). |
| 11i | **WFO_VIOLATION** | M | 11g | For each absent-without-leave day, look up `silver_employees.schedule_<weekday>` — flag when it equals `'WFO'`. |
| 11j | **WFH_QUOTA_EXCEEDED** | M | 11a | Sum Availed `WFH` leave days vs `silver_employees.wfh_credits_monthly`. `flag_value` = excess. |

Each sub-task closes when: implementation merged, pytest module green, manual rerun on the same period produces no duplicates.

## Linked FR-IDs
- FR-009 (and reinforces FR-007)

## Linked entities
- `gold_employee_flags`, `gold_period_stats`, `silver_daily_attendance`, `silver_leave_transactions`, `silver_employees`, `app_flag_thresholds`

## Infrastructure dependencies
- `app_flag_thresholds` seeded (US-002).
- Unique-ish composite check on `(emp_code, flag_type, period_start)` in the engine code path.
