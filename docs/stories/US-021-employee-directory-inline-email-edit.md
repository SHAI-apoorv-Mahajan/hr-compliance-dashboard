# US-021 — Employee directory with inline email edit

**Epic:** Employee UI

## Story
- **As an** HR admin
- **I want** an employee directory where I can inline-edit each employee's email
- **So that** compliance emails reach the right inbox without me jumping into the database or roster file.

## Acceptance criteria
- **Given** the page at `/employees`, **when** it loads, **then** I see a table with columns: Emp Code, Name, Email (editable inline), Project, Client, In Team Role, Billing Status, Working Model, WFH Credits, InTime Deadline — sourced from `silver_employees` (PRD §19 Page 4).
- **Given** the Email cell, **when** I click it, **then** it becomes an editable input; on blur or Enter, `PATCH /api/v1/employees/{emp_code}/email` is called with the new value (FR-020).
- **Given** an invalid email format, **when** I save, **then** I receive HTTP 422 with a clear message and the cell reverts to the previous value.
- **Given** a successful update, **when** the response returns, **then** the cell shows the new email and a brief inline confirmation (toast or checkmark).
- **Given** I click an employee row (outside the email cell), **when** the detail sidebar opens, **then** I see all roster fields, Mon–Sun schedule chips, current period stats from `gold_period_stats`, and active flags from `gold_employee_flags`.

## Dependencies
- US-007, US-010, US-011

## Estimate
**M** — Table + inline edit pattern + detail sidebar with multiple joined data sources.

## Linked FR-IDs
- FR-020

## Linked entities
- `silver_employees`, `gold_period_stats`, `gold_employee_flags`

## Infrastructure dependencies
- `/api/v1/employees`, `/api/v1/employees/{emp_code}`, `/api/v1/employees/{emp_code}/email`.
