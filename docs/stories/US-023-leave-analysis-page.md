# US-023 — Leave analysis page

**Epic:** Analytics UI

## Story
- **As an** HR admin
- **I want** a leave analysis page per period
- **So that** I can see leave types, WFH availed vs quota, and lapsed credits per employee.

## Acceptance criteria
- **Given** the page at `/leave` with a selected period, **when** it loads, **then** I see a per-employee table with one column per leave type (sum of `silver_leave_transactions.days` where `transaction_type='Availed'` covering the period) (PRD §19 Page 6).
- **Given** the same table, **when** rendered, **then** there is a "WFH availed vs quota" column comparing `wfh_days_availed` against `silver_employees.wfh_credits_monthly` — values exceeding quota visually highlighted (red).
- **Given** a Lapsed credits view (toggle or column), **when** shown, **then** rows are derived from `silver_leave_transactions.transaction_type='Lapsed'`.
- **Given** the period selector, **when** changed, **then** the table re-fetches from `GET /api/v1/leave?period_start=&period_end=`.

## Dependencies
- US-009, US-010

## Estimate
**S** — Single tabular view + one endpoint with aggregations.

## Linked FR-IDs
- Supports FR-008 (gold stats consumed here) and FR-011 (the leave dimension of analysis).

## Linked entities
- `silver_leave_transactions`, `silver_employees`, `gold_period_stats`

## Infrastructure dependencies
- `/api/v1/leave`, `/api/v1/leave/{emp_code}`.
