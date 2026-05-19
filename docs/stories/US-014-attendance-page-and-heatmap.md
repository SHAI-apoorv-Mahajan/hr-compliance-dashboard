# US-014 — Attendance analysis page with calendar heatmap

**Epic:** Analytics UI

## Story
- **As an** HR admin
- **I want** an attendance analysis page with a per-employee summary and a clickable calendar heatmap
- **So that** I can drill into one employee's daily attendance patterns.

## Acceptance criteria
- **Given** the page at `/attendance` with a selected period, **when** it loads, **then** I see a table per employee with columns: Present, Absent, Absent w/o Leave, Late, Early, No Out-Punch, Half Days, Work Hours — sourced from `gold_period_stats` (FR-011).
- **Given** I click an employee row, **when** the detail view opens, **then** a calendar heatmap renders one cell per day of the period with these exact colors: green=Present, red=Absent, yellow=½Present, grey=WeeklyOff, blue=Approved Leave (FR-011).
- **Given** a cell click, **when** the popover opens, **then** it shows InTime, OutTime, LateBy, EarlyGoingBy for that day (FR-011).
- **Given** a Permanent WFH employee on an NS-shift "Absent" day, **when** rendered, **then** the cell is **not** colored red (these are expected; PRD §27 quirk #8) — use a neutral/grey color or hide.
- **Given** no data for a day (employee not in biometric file for that date), **when** rendered, **then** the cell is empty/grey.

## Dependencies
- US-010

## Estimate
**M** — Calendar grid component + cell click popover + per-employee table.

## Linked FR-IDs
- FR-011

## Linked entities
- `silver_daily_attendance`, `silver_employees`, `gold_period_stats`

## Infrastructure dependencies
- `/api/v1/attendance?period_start=&period_end=`, `/api/v1/attendance/{emp_code}?period_start=&period_end=`.
