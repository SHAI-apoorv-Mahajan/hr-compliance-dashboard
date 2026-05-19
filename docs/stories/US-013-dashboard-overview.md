# US-013 — Dashboard overview page

**Epic:** Analytics UI

## Story
- **As an** HR admin
- **I want** an overview dashboard with summary cards and trend charts for the selected period
- **So that** I can spot compliance issues at a glance.

## Acceptance criteria
- **Given** gold data exists for the selected period, **when** I navigate to `/dashboard`, **then** I see five summary cards: Total Employees, Flagged This Period (red badge), Attendance Rate %, WFH Compliance %, Emails Sent This Period (FR-010).
- **Given** the same data, **when** the page renders, **then** I see: a bar chart of attendance % by employee, a pie chart of flag distribution by type, and a line chart of LATE_ARRIVAL trend across the last N periods (FR-010).
- **Given** the period selector dropdown, **when** I change the period, **then** all cards and charts re-fetch from `GET /api/v1/analytics/overview?period_start=&period_end=` and re-render (FR-010).
- **Given** up to 50 employees × 31 days of data, **when** the page first loads, **then** time-to-interactive is under 3 seconds (NFR-003).
- **Given** the email service is not configured, **when** the page renders, **then** the "Emails Sent This Period" card shows `0` (not an error) — covered by the global config-status banner from US-018.

## Dependencies
- US-010, US-011

## Estimate
**M** — Three Recharts charts + 5 cards + analytics endpoints.

## Linked FR-IDs
- FR-010

## Linked entities
- `gold_period_stats`, `gold_employee_flags`, `silver_employees`, `app_email_log`

## Infrastructure dependencies
- `recharts`, `react-router-dom`, `axios`.
- `/api/v1/analytics/overview`, `/api/v1/analytics/attendance-chart`, `/api/v1/analytics/flag-distribution`.
