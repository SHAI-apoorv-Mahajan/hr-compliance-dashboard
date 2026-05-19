# US-017 — Graceful 503 when Microsoft Graph is not configured

**Epic:** Email

## Story
- **As an** HR admin running the app before Graph credentials are provisioned
- **I want** the email send endpoint to fail safely with a clear message and the UI to show a warning banner
- **So that** the app remains usable for upload/pipeline/analytics work without crashing.

## Acceptance criteria
- **Given** any of `GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID`, `GRAPH_CLIENT_SECRET` is an empty string, **when** I `POST /api/v1/email/send` (with `preview_only: false`), **then** the response is HTTP 503 with the exact body `{"detail": "Email service is not configured. Please set GRAPH_TENANT_ID, GRAPH_CLIENT_ID, and GRAPH_CLIENT_SECRET in the environment."}` — and the app does not crash (FR-014).
- **Given** the same misconfiguration, **when** the frontend Email Center loads, **then** `GET /api/v1/email/config-status` returns `{configured: false, missing: ["GRAPH_TENANT_ID", ...]}` and a non-dismissable yellow banner renders with: "Email service is not yet configured. Contact the system administrator." (FR-014, PRD §19 Page 8).
- **Given** the misconfigured state, **when** the Settings → System Config tab loads, **then** each of GRAPH_TENANT_ID / CLIENT_ID / SECRET shows as `Set ✓` or `Not Set ✗` — **never the actual value** (PRD §19 Page 9, NFR-004).
- **Given** a `preview_only: true` request, **when** Graph is misconfigured, **then** the preview still renders normally (no Graph call needed).

## Dependencies
- US-016

## Estimate
**S** — Early-return check + config-status endpoint + frontend banner.

## Linked FR-IDs
- FR-014

## Linked entities
- None (config check is env-only).

## Infrastructure dependencies
- Env vars from `.env`.
- `/api/v1/email/config-status`.
