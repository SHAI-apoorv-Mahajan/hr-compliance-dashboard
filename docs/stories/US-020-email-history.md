# US-020 — Email history audit view

**Epic:** Email

## Story
- **As an** HR admin
- **I want** to view a chronological log of every email send attempt
- **So that** I can audit who was notified, when, with which template, and whether delivery succeeded.

## Acceptance criteria
- **Given** the Email Center → Email History tab, **when** it loads, **then** I see a table with columns: recipient, subject, flag type (joined from `gold_employee_flags.flag_type` via `flag_id`), template used (joined from `app_email_templates.name`), status (`sent | failed | not_configured`), `sent_at`, `sent_by` (FR-019).
- **Given** the filter controls, **when** I filter by employee or period, **then** `GET /api/v1/email/logs?emp_code=&period_start=&period_end=` returns only matching rows (FR-019).
- **Given** a failed send, **when** I hover or expand the row, **then** the `error_message` is visible (e.g., Graph API error body) so I can diagnose.
- **Given** a `not_configured` row, **when** displayed, **then** it is visually distinct from `failed` (yellow vs red) so HR can distinguish setup gaps from delivery failures.

## Dependencies
- US-016

## Estimate
**S** — Single endpoint + table UI with joins.

## Linked FR-IDs
- FR-019

## Linked entities
- `app_email_log`, `app_email_templates`, `gold_employee_flags`, `silver_employees`

## Infrastructure dependencies
- `/api/v1/email/logs`.
