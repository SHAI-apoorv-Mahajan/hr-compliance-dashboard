# US-018 — Email template CRUD with soft-delete

**Epic:** Email

## Story
- **As an** HR admin
- **I want** to create, edit, and delete email templates from Settings → Email Templates
- **So that** I can tailor the tone or content of compliance notices.

## Acceptance criteria
- **Given** the Email Templates tab, **when** it loads, **then** I see the 8 seeded templates (FR-017) and any custom ones, each with name, flag_type, subject, body excerpt, and Edit/Delete actions (FR-015).
- **Given** the "Create New Template" form, **when** I fill name, optional flag_type, subject, body (with `{{variable}}` placeholders) and click Preview, **then** the rendered preview substitutes dummy values for every variable so I can validate formatting (FR-015).
- **Given** valid input, **when** I click Save, **then** a `POST /api/v1/email/templates` creates the row with `is_active = TRUE`; **when** I edit an existing template, **then** `PUT /api/v1/email/templates/{id}` updates it and `updated_at` advances (FR-015).
- **Given** I click Delete on a template **with no** `app_email_log` rows referencing it, **when** the request runs, **then** the row is hard-deleted; **given** I delete a template **with** referencing logs, **then** the row is soft-deleted (`is_active = FALSE`) and remains in the DB so audit history is preserved (FR-015).
- **Given** the template list, **when** rendered for the send flow (US-016), **then** only `is_active = TRUE` templates are shown.

## Dependencies
- US-002

## Estimate
**M** — Four endpoints + preview renderer + soft-delete branch + UI form.

## Linked FR-IDs
- FR-015

## Linked entities
- `app_email_templates`, `app_email_log`

## Infrastructure dependencies
- `/api/v1/email/templates*`.
