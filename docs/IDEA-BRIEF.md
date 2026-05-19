# Idea Brief — HR Compliance Dashboard

> Distilled summary of [PRD.md](PRD.md). PRD is the source of truth — refer to it for any detail not captured here.

## One-liner
Internal web app that ingests three monthly Excel exports (GreytHR leave, biometric attendance, team roster), runs a Bronze → Silver → Gold medallion pipeline to flag non-compliant employees against 9 configurable thresholds, and sends templated compliance emails via Microsoft Graph API.

## Problem
ShortHills Tech HR currently cross-references three Excel files manually for 30+ employees each month. The process is slow, inconsistent, and email follow-ups are composed by hand. There is no single tool that ingests, cross-references, surfaces violations, and enables one-click notice emails.

## Primary user
Single HR admin (non-technical). Internal network only. JWT-authenticated. No manager or employee logins in v1.

## Core journey
Log in → upload monthly Biometric + GreytHR (and Roster, once) → click "Run Pipeline" → view dashboard summary → filter flagged employees → preview templated email with variable substitution → send via Graph API → audit in Email History.

## Goals (v1)
- Parse three Excel formats, including the report-style biometric block format and Excel serial date integers in GreytHR.
- Cross-reference biometric absences against approved GreytHR leave before flagging.
- Skip flagging for `is_permanent_wfh = True` employees on NS-shift absences.
- Evaluate 9 flag types (LATE_ARRIVAL, EARLY_DEPARTURE, ABSENT_WITHOUT_LEAVE, CONSECUTIVE_ABSENCE, NO_OUT_PUNCH, HALF_DAY_FREQUENCY, WFH_QUOTA_EXCEEDED, LOW_WORK_HOURS, WFO_VIOLATION) against editable thresholds.
- Render template emails with `{{variable}}` substitution and send via Graph API `sendMail`.
- Zero-setup deploy: `docker compose up --build` only.

## Non-goals (v1)
Manager logins, role-based access, mobile design, real-time biometric streaming, payroll integration, multi-tenancy, automated scheduling, in-UI Graph setup wizard.

## Tech stack (locked by PRD §9)
- **Frontend:** React 18 + Vite, TailwindCSS, React Router v6, Axios, Recharts.
- **Backend:** Python 3.11, FastAPI, SQLAlchemy 2.x, Pydantic v2.
- **DB:** PostgreSQL via Supabase (remote — no local container). Schema via `Base.metadata.create_all(engine)`. **No Alembic.**
- **Auth:** JWT HS256, 24h expiry, bcrypt via passlib.
- **Excel:** pandas + openpyxl (block-parser for biometric).
- **Email:** Microsoft Graph API via httpx, with graceful 503 degradation when env vars missing.
- **Container:** Docker Compose, 2 services (backend, frontend). No DB container.

## Critical constraints (must not be inferred away)
1. GreytHR `From Date` / `To Date` are Excel serial integers — convert with `datetime(1899,12,30) + timedelta(days=n)`. Do not use pandas auto-detect.
2. Biometric file is a sequence of employee blocks with "Emp Code:" marker rows — implement Section 14.2 algorithm exactly.
3. Roster column name `"Intime window onpen till"` is a typo — use it verbatim.
4. Unicode `½` (U+00BD) preserved throughout. UTF-8 everywhere.
5. Missing Graph env vars → HTTP 503, never a crash. Frontend renders a warning banner.
6. `create_all` only. No migrations. Seed runs on startup, idempotent (`if table empty` guards).
7. Permanent WFH employees on NS shift are not flagged for absence.
8. Pipeline reruns are fully idempotent — upsert keys defined per gold table.

## Success metrics (PRD §12)
- HR monthly review time: < 30 min (from ~3 hrs).
- Pipeline run for one period: < 30 s.
- First-run `docker compose up --build`: 100% success.
- Email send success: > 95% (once Graph configured).

## Open questions (PRD §10 — track, do not block)
- Azure AD flow: PRD assumes Client Credentials with app-only `Mail.Send`.
- PDF/Excel compliance report export — deferred.
- Mid-month roster changes — current model assumes static per month.

## Functional requirement IDs
FR-001 through FR-020 (PRD §6). All are testable and back the user stories under [stories/](stories/).
