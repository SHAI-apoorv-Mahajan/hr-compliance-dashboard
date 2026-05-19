# US-016 — Email send flow with preview and Microsoft Graph API

**Epic:** Email

## Story
- **As an** HR admin
- **I want** to select employees, choose a template, preview the rendered email, and send via Microsoft Graph
- **So that** I can dispatch compliance notices in one workflow with an audit trail.

## Acceptance criteria
- **Given** a list of selected flag IDs and a template ID, **when** I `POST /api/v1/email/send` with `preview_only: true`, **then** the response is HTTP 200 with one rendered email per recipient (subject + body with all `{{variables}}` substituted from `gold_employee_flags` + `silver_employees`) — **no** Graph API call is made and no `app_email_log` row is inserted (FR-013).
- **Given** `preview_only: false` and all three `GRAPH_TENANT_ID`/`GRAPH_CLIENT_ID`/`GRAPH_CLIENT_SECRET` are set, **when** I send, **then** the backend fetches an OAuth2 access token from `https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token` and POSTs to `https://graph.microsoft.com/v1.0/users/{GRAPH_SENDER_EMAIL}/sendMail` for each recipient, logging each attempt to `app_email_log` (status `'sent'` or `'failed'` with the Graph error body) (FR-013).
- **Given** a successful send, **when** the response returns, **then** `gold_employee_flags.email_sent = TRUE` and `email_sent_at` is set; **one email per (flag_type, employee)** per send request (FR-013).
- **Given** a Graph API error (non-2xx), **when** logged, **then** the full response body is recorded in `app_email_log.error_message` (not exposed to the client beyond a generic detail message per NFR-005).
- **Given** the substitution rules, **when** rendered, **then** `{{sender_name}}` = `"HR Team, ShortHills Tech"`, and all variables from PRD §18 are available: `{{employee_name}}`, `{{emp_code}}`, `{{period}}`, `{{period_start}}`, `{{period_end}}`, `{{flag_count}}`, `{{flag_dates}}`, `{{threshold}}`, `{{sender_name}}`.

## Dependencies
- US-011, US-015, US-017 (templates)

## Estimate
**L** — OAuth2 token fetch + Graph send + per-recipient loop + variable substitution + audit logging.

## Linked FR-IDs
- FR-013

## Linked entities
- `gold_employee_flags`, `app_email_templates`, `app_email_log`, `silver_employees`

## Infrastructure dependencies
- `httpx`.
- `GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID`, `GRAPH_CLIENT_SECRET`, `GRAPH_SENDER_EMAIL` env vars (or US-017's graceful 503 fallback when missing).
