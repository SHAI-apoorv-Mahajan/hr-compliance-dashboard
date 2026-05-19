# HR Compliance Dashboard — Project Requirements Document

**Version:** 2.0  
**Status:** FINAL — Do not modify without developer approval  
**Prepared for:** Cursor AI (full-stack code generation)  
**Last Updated:** May 2026

---

## CRITICAL INSTRUCTION FOR AI CODE GENERATION

Read this entire document before writing a single line of code. Every section is load-bearing. Do not infer, guess, or substitute any detail that is explicitly stated here. Where something is not mentioned, use the best standard practice for the given tech stack. Do not hallucinate library APIs — use only well-known, stable versions of the libraries listed in Section 2.

---

## 1. Title & One-Line Pitch

**HR Compliance Dashboard** — An internal web application that ingests employee attendance and leave Excel exports, runs a medallion data pipeline to flag non-compliant employees, and sends automated notice emails via Microsoft Graph API.

---

## 2. Problem Statement

ShortHills Tech HR currently reviews attendance manually from three Excel files: a GreytHR leave ledger, a biometric attendance report, and a team roster/schedule sheet. This process is:
- Time-consuming: cross-referencing three files manually for 30+ employees is error-prone
- Inconsistent: no standardized threshold for what constitutes a flag-worthy pattern
- Action-delayed: sending compliance emails requires composing individual emails each time

There is no single tool that ingests these files, cross-references the data, surfaces violations, and enables one-click notice emails.

---

## 3. Goals & Non-Goals

### Goals
- Parse all three Excel files into a structured, queryable database (Medallion pipeline: Bronze → Silver → Gold)
- Flag employees automatically based on configurable thresholds across 9 violation types
- Enable HR to send templated compliance emails to flagged employees via Microsoft Graph API
- Present a clean analytics dashboard with attendance trends and flag summaries
- Deploy with zero manual setup beyond `docker compose up --build`

### Non-Goals (v1)
- No manager login or team-scoped access control (single HR admin only)
- No mobile app or responsive-first design (desktop browser only)
- No real-time biometric data streaming (file upload only)
- No payroll integration
- No multi-tenancy (single company only: ShortHills Tech)
- No Microsoft Graph API setup automation (HR configures Azure AD credentials manually)
- No automated email scheduling (emails are manually triggered by HR)

---

## 4. Target Users & Personas

**Primary Persona: HR Admin (single user)**
- Name: ShortHills Tech HR Team
- Technical level: Non-technical (comfortable with Excel and web dashboards)
- Core need: Upload monthly Excel exports, see who needs to be flagged, send emails in minutes
- Pain point: Currently spends hours cross-referencing three Excel files manually each month
- Access: Internal network only; JWT-authenticated

---

## 5. Core User Journeys

**Journey 1 — Monthly Compliance Review (primary)**
HR logs in → navigates to Upload page → uploads Biometric Excel for the period → uploads GreytHR Excel for the period → clicks "Run Pipeline" → waits for processing → navigates to Dashboard and sees summary cards populate → goes to Flags page → filters by flag type → selects flagged employees → chooses a template → previews rendered email → sends → sees "Sent" status in Email History.

**Journey 2 — First-Time Setup**
HR opens app for first time → logs in with default credentials (hr@shorthills.ai / HR@ShortHills2024) → navigates to Upload → uploads Roster file (once, not period-specific) → uploads Biometric + GreytHR for first period → runs pipeline → views dashboard to confirm data loaded correctly.

**Journey 3 — Threshold Tuning**
HR notices too many late-arrival flags that feel excessive → navigates to Settings → sees current threshold (3 occurrences) → changes to 5 → saves → returns to Upload page → re-runs pipeline for current period → flags list updates to reflect new threshold.

**Journey 4 — Email Template Management**
HR wants a custom tone for WFH violation emails → navigates to Email Center → clicks "Create New Template" → fills in name, selects flag type (WFH_QUOTA_EXCEEDED), writes subject and body using {{variable}} placeholders → clicks Preview to see rendered output with dummy values → saves → uses in next send cycle.

**Journey 5 — Employee Drill-Down**
HR sees an employee with high absent count on the dashboard → clicks employee name in the directory → views calendar heatmap for the period (green/red/yellow/grey cells) → identifies 4 consecutive red (absent) cells → checks leave analysis tab — no leave applied → returns to Flags page → sends Consecutive Absence email.

**Journey 6 — Email History Audit**
HR needs to confirm a compliance email was sent last month → navigates to Email Center → Email History tab → filters by employee name → sees sent timestamp, template used, and status "sent" → no action needed.

---

## 6. Functional Requirements

Each FR is testable. FR-IDs are used in user stories.

| ID | Requirement |
|---|---|
| FR-001 | The system shall authenticate an HR user via email + password and return a signed JWT (HS256, 24h expiry) on success. Invalid credentials shall return HTTP 401 with `{"detail": "Invalid email or password"}`. All non-auth endpoints shall return HTTP 401 if the token is missing or expired. |
| FR-002 | The system shall accept .xlsx GreytHR leave files with columns: Sl No, Employee No, Name, Manager No, Manager Name, Leave Type, Transaction Type, Posted Date, From Date, To Date, Days, Expire Date, Reason, Remarks. From Date and To Date shall be converted from Excel serial numbers to dates using `datetime(1899,12,30) + timedelta(days=n)`. |
| FR-003 | The system shall parse biometric .xlsx files using the block-parsing algorithm (Section 4.2 of Implementation Details): employee blocks identified by "Emp Code:" marker rows; time strings converted to minutes; status values stripped of whitespace; ½Present Unicode character (U+00BD) preserved. |
| FR-004 | The system shall parse roster .xlsx files and upsert silver_employees records matched by normalized name (case-insensitive, whitespace-normalized). "Permanent WFH" working model shall set `is_permanent_wfh = true`. Intime window values (e.g., "10:30am") shall be parsed to TIME type; non-parseable values default to NULL. |
| FR-005 | Uploading a file of the same type with an overlapping period shall be rejected before any DB write with HTTP 409 and message: "A {file_type} file for this period has already been uploaded. Delete it first to re-upload." |
| FR-006 | The silver pipeline shall cross-reference each biometric absent record against GreytHR Availed leave transactions covering that date. Matching records shall set `has_approved_leave = true` and `approved_leave_type`. |
| FR-007 | Permanent WFH employees (`is_permanent_wfh = true`) shall not have absence records flagged. Their NS-shift biometric records are expected and shall not generate ABSENT_WITHOUT_LEAVE, WFO_VIOLATION, or LATE_ARRIVAL flags. |
| FR-008 | The gold pipeline shall compute `gold_period_stats` per employee per period: present_days, absent_days, absent_without_leave_days, late_arrival_count, early_departure_count, no_out_punch_count, half_day_count, wfh_days_availed, wfh_credits_allocated. Pipeline runs shall be idempotent (upsert, not insert). |
| FR-009 | The gold pipeline shall evaluate all 9 flag types (LATE_ARRIVAL, EARLY_DEPARTURE, ABSENT_WITHOUT_LEAVE, CONSECUTIVE_ABSENCE, NO_OUT_PUNCH, HALF_DAY_FREQUENCY, WFH_QUOTA_EXCEEDED, LOW_WORK_HOURS, WFO_VIOLATION) against thresholds from `app_flag_thresholds`. Each triggered flag shall be written to `gold_employee_flags` with `flag_value`, `threshold_value`, and `flag_details` JSON containing affected dates. Re-running shall refresh existing flags without creating duplicates. |
| FR-010 | The dashboard overview page shall display: total employees, count of flagged employees this period, overall attendance rate %, WFH compliance %, emails sent this period. It shall include: bar chart (attendance by employee), pie chart (flag distribution by type), line chart (late arrival trend over periods). All charts shall reflect the selected period. |
| FR-011 | The attendance page shall display a per-employee summary table. Clicking an employee shall show a calendar heatmap: green=Present, red=Absent, yellow=½Present, grey=WeeklyOff, blue=Approved Leave. Each cell click shall show InTime, OutTime, LateBy, EarlyGoingBy for that day. |
| FR-012 | The flags page shall allow HR to filter flags by type, employee, and period. HR shall be able to mark individual flags as resolved (resolved flags hidden from default view). HR shall be able to bulk-select flags and initiate email send. |
| FR-013 | The email send flow shall: (1) let HR select employees and a template, (2) preview the rendered email with all `{{variables}}` substituted, (3) send via Microsoft Graph API, (4) log each attempt to `app_email_log` with status: sent / failed / not_configured. One email per flag type per employee. |
| FR-014 | If any of GRAPH_TENANT_ID, GRAPH_CLIENT_ID, GRAPH_CLIENT_SECRET are empty strings, the send endpoint shall return HTTP 503 with: `{"detail": "Email service is not configured. Please set GRAPH_TENANT_ID, GRAPH_CLIENT_ID, and GRAPH_CLIENT_SECRET in the environment."}`. The app shall not crash. The frontend shall display this as a warning banner (not a crash screen). |
| FR-015 | HR shall be able to create, edit, and delete email templates. Each template has: name, flag_type (optional), subject, body (supports `{{variable}}` syntax), available_variables list. Deleting a template that has email_log entries shall soft-delete (set `is_active = false`) rather than hard-delete. |
| FR-016 | HR shall be able to view and update `threshold_value` for all 9 flag types from Settings. Changes shall take effect on the next pipeline run. Existing flags are not retroactively modified. |
| FR-017 | On first startup (empty `app_users` table), the system shall seed: default HR user (email: hr@shorthills.ai, password: HR@ShortHills2024, bcrypt-hashed), 8 email templates (defined in Section 8.3 of Implementation Details), 9 flag thresholds with default values (defined in Section 7 of Implementation Details). Seeding shall be idempotent. |
| FR-018 | HR shall be able to trigger the full medallion pipeline from the Upload page for a given period. The button shall be disabled until both biometric and GreytHR files exist for that period. Pipeline progress shall update in the UI without full page refresh. |
| FR-019 | HR shall be able to view email history with columns: recipient, subject, flag type, template used, status, sent_at, sent_by. Filterable by employee and period. |
| FR-020 | HR shall be able to edit any employee's email address inline from the Employee Directory page. |

---

## 7. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-001 | **Zero-dependency startup:** The complete application shall start with `docker compose up --build` from the project root. No installations beyond Docker Desktop are required. First-run boot time shall be under 5 minutes on a standard developer machine. |
| NFR-002 | **Migration-free schema:** DB tables shall be created via SQLAlchemy `Base.metadata.create_all(engine)` on backend startup. Alembic shall NOT be used. The operation is idempotent — restarting the backend shall never raise errors if tables already exist. |
| NFR-003 | **Performance:** Dashboard overview page shall load in under 3 seconds for up to 50 employees and 31 days of data. Pipeline run for one month (50 employees × 31 days ≈ 1,550 records) shall complete in under 30 seconds. |
| NFR-004 | **Security:** JWT tokens use HS256 with 24-hour expiry. Passwords hashed with bcrypt (passlib). `.env` not committed. Frontend never receives raw password hashes or Graph API credentials. `deny` list in settings.json blocks reads of `.env` files. |
| NFR-005 | **Graceful degradation:** No unhandled exceptions shall reach the client. All FastAPI endpoints return `{"detail": "..."}` on error. Python stack traces shall not appear in API responses. Missing Graph config returns HTTP 503, not HTTP 500. |
| NFR-006 | **Data integrity:** Duplicate uploads rejected before any DB write (HTTP 409). Pipeline reruns are idempotent — no duplicate rows in gold tables. |
| NFR-007 | **Cross-platform:** Docker configuration runs identically on macOS, Linux, and Windows (Docker Desktop). No host path assumptions. |
| NFR-008 | **Encoding:** All Excel parsing correctly handles UTF-8, including the Unicode ½ character (U+00BD) in biometric status values. No encoding errors for any employee name. |
| NFR-009 | **Observability:** All pipeline stage transitions (bronze ingest, silver clean, gold analyze) logged to stdout with ISO timestamps and row counts. Failed uploads write full error to `bronze_uploads.error_message`. |

---

## 8. System Context Diagram

```mermaid
graph TB
    subgraph Docker Compose
        FE["Nginx :3000\n(React SPA)"]
        BE["FastAPI :8000\n(Python 3.11)"]
    end
    subgraph External Services
        DB[("Supabase\nPostgreSQL")]
        GRAPH["Microsoft\nGraph API"]
    end

    HR["HR Admin\n(Browser)"] -->|"HTTP :3000"| FE
    FE -->|"/api/* reverse proxy"| BE
    BE -->|"psycopg2 + SQLAlchemy\ncreate_all on startup"| DB
    BE -->|"httpx · OAuth2 token\n+ sendMail"| GRAPH
    HR -->|".xlsx file upload"| FE
```

---

## 9. Tech Stack & Key Architectural Decisions

| Layer | Technology | Rationale |
|---|---|---|
| Frontend | React 18 (Vite), TailwindCSS, React Router v6, Axios, Recharts | Vite for fast builds; Recharts for charts without heavy dependencies; Tailwind for utility-first styling without a component library |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.x, Pydantic v2 | FastAPI for async-ready typed APIs; SQLAlchemy 2.x for ORM with `create_all` avoiding migration tooling entirely |
| Database | PostgreSQL via Supabase (remote, no local container) | Remote managed DB eliminates local Postgres container and removes the single biggest source of Docker compose errors |
| Auth | JWT (python-jose), bcrypt (passlib) | Simple, stateless; single-user internal tool does not need OAuth or a third-party auth provider |
| Excel Parsing | pandas + openpyxl | Biometric file requires custom block-parsing (not a flat table); openpyxl row iterator handles it correctly; pandas handles flat GreytHR and roster sheets |
| Email | Microsoft Graph API via httpx | Company already uses Microsoft 365; Graph API `sendMail` is the standard approach; feature gracefully disabled if not configured |
| Containerization | Docker + Docker Compose (2 services: backend, frontend) | No local DB container (Supabase is remote); only 2 services minimizes compose complexity and startup errors |
| DB Schema Management | SQLAlchemy `create_all()` only — no Alembic | `create_all` is idempotent and requires zero configuration; Alembic migrations were the primary source of first-run errors in previous projects |

---

## 10. Open Questions

- [ ] When Microsoft Graph API is eventually configured, will the Azure AD app use Client Credentials flow or Delegated flow? (PRD assumes Client Credentials — app-only permission `Mail.Send`)
- [ ] Should the pipeline produce a downloadable PDF/Excel compliance report in a future version?
- [ ] Are there employees whose roster changes mid-month (e.g., WFO days change)? Current model assumes the roster is static per month.

---

## 11. Out of Scope (v1)

- Manager-level login with team-scoped data visibility
- Automated monthly pipeline scheduling (cron/celery)
- Payroll integration or leave balance deduction
- Multi-company / multi-tenant support
- Microsoft Graph API setup wizard in the UI
- Mobile-responsive design
- PDF/Excel export of compliance reports
- Role-based access control beyond a single HR admin
- Employee self-service portal

---

## 12. Success Metrics

| Metric | Target | How Measured |
|---|---|---|
| Monthly HR time on compliance review | < 30 minutes (from ~3 hours manually) | HR self-reported after 3 months |
| Pipeline run time for one period | < 30 seconds | Backend stdout logs |
| Email send success rate | > 95% (once Graph is configured) | `app_email_log.status = 'sent'` count / total attempts |
| First-run startup success | 100% (no manual intervention) | `docker compose up --build` completes without errors |
| Flag false-positive rate | < 10% (HR resolves < 10% of flags) | `gold_employee_flags.is_active = false` / total flags |

---

---

# IMPLEMENTATION DETAILS
## (Sections below are authoritative specifications for code generation — do not skip)

---

## 13. Database Connection

```
postgresql+psycopg2://postgres.cblbhphawxrjnygwlkin:n0h6VpgjuvyZHacq@aws-1-ap-south-1.pooler.supabase.com:5432/postgres
```

Store in `.env` as `DATABASE_URL`. Use `pool_pre_ping=True` and `pool_recycle=300` in engine creation to handle Supabase connection drops gracefully.

---

## 14. Data Sources

### 14.1 Source File 1 — GreytHR Leave Sheet

**Format:** Flat table Excel (.xlsx), single sheet `Sheet1`.

**Columns (exact, in order):**
`Sl No`, `Employee No`, `Name`, `Manager No`, `Manager Name`, `Leave Type`, `Transaction Type`, `Posted Date`, `From Date`, `To Date`, `Days`, `Expire Date`, `Reason`, `Remarks`

**Critical Parsing Notes:**
- `From Date` and `To Date` are stored as **Excel serial date numbers** (integers like `46101`). Convert using: `datetime(1899, 12, 30) + timedelta(days=int(serial))`. Do NOT use pandas auto-detect — it will fail on these columns.
- `Posted Date` is a formatted string like `"20 Mar 2026 18:12"` — parse with `pd.to_datetime`.
- `Days` can be decimal (e.g., `0.5` for half day).
- `Expire Date` may be empty/NaN — handle as nullable.
- `Leave Type` values: `WFH`, `Earned Leave`, `CASUAL-SICK LEAVE`, `Hospitalisation Leave`, `Paternity Leave`, `Maternity Leave`.
- `Transaction Type` values: `Availed`, `Granted`, `Lapsed`, `Withdrawn`, `Opening Balance`.
- Only rows where `Transaction Type = 'Availed'` count as actual leave taken for cross-referencing.

### 14.2 Source File 2 — Biometric Attendance Sheet

**Format:** Report-style Excel (.xlsx), single sheet `Sheet1`. **This is NOT a flat table.** It is a sequence of employee blocks.

**Block structure per employee:**
```
Row: [blank, "Daily Attendance Report (Detailed Summary Report)"]  ← skip
Row: [blank, "<date range string>"]                                 ← skip
Row: [blank, "Company:", "Shorthills GGn", ..., "Printed On: ..."] ← skip
Row: [blank, "Emp Code:", <emp_code>, "Employee Name :", ..., <name>]  ← EMPLOYEE MARKER
Row: [blank, "Att. Date", "InTime", "OutTime", ...]                ← column header, skip
Row: [date, intime, outtime, shift, ...]                           ← DATA ROWS
Row: [blank, "Total Duration=...", ...]                            ← SUMMARY ROW, end block
```

**Biometric Parsing Algorithm (implement exactly):**

```python
# Use openpyxl to read the sheet
wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
ws = wb.active

current_emp_code = None
current_emp_name = None
skip_next_row = False  # True after EMPLOYEE MARKER row (to skip column header row)
records = []

for row in ws.iter_rows(values_only=True):
    cells = [str(c).strip() if c is not None else "" for c in row]

    # EMPLOYEE MARKER: column B == "Emp Code:"
    if cells[1] == "Emp Code:":
        current_emp_code = cells[2]  # column C
        # Name is first non-empty value after index 4
        name_parts = [c for c in cells[4:] if c]
        current_emp_name = name_parts[0] if name_parts else ""
        skip_next_row = True
        continue

    if skip_next_row:
        skip_next_row = False
        continue

    # SUMMARY ROW
    if cells[1].startswith("Total Duration="):
        current_emp_code = None
        current_emp_name = None
        continue

    if not current_emp_code:
        continue
    if not cells[1] or cells[1] == "Daily Attendance Report (Detailed Summary Report)":
        continue

    # DATA ROW: cells[1] is a date string like "01-Apr-2026"
    try:
        att_date = datetime.strptime(cells[1], "%d-%b-%Y").date()
    except (ValueError, TypeError):
        continue

    records.append({
        "emp_code": current_emp_code,
        "employee_name": current_emp_name,
        "att_date": att_date,
        "in_time": cells[2] or None,
        "out_time": cells[3] or None,
        "shift": cells[4] or None,
        "scheduled_in_time": cells[6] or None,
        "scheduled_out_time": cells[7] or None,
        "work_duration": cells[9] or "00:00",
        "ot": cells[10] or "00:00",
        "total_duration": cells[11] or "00:00",
        "late_by": cells[12] or "00:00",
        "early_going_by": cells[13] or "00:00",
        "status": cells[14] or "",
        "punch_records": cells[15] or ""
    })
```

**Time conversion:** Convert `"HH:MM"` strings to minutes: `hours * 60 + minutes`.

**Status values (always `.strip()`):**
- `"Present"` — normal present
- `"Absent"` — absent
- `"WeeklyOff"` — weekly off
- `"½Present"` — half-present (Unicode ½, U+00BD)
- `"Present  (No OutPunch)"` — no clock-out
- `"½Present (No OutPunch)"` — half-present, no clock-out

Derive booleans: `is_half_present = "½Present" in status`, `is_no_out_punch = "No OutPunch" in status`, `is_absent = status.strip() == "Absent"`, `is_weekly_off = "WeeklyOff" in status`.

**Shift codes:** `UB` = Universal Band (flexible), `2nd Shift` = afternoon, `NS` = No Shift (Permanent WFH employees — expected, not an error).

### 14.3 Source File 3 — Team Timings & Roster

**Format:** Flat table Excel (.xlsx), single sheet `Sheet1`.

**Columns (exact, including typo):**
`Name`, `Project`, `Client`, `In team Role`, `Billing status`, `Working Model`, `Monday`, `Tuesday`, `Wednesday`, `Thursday`, `Friday`, `Saturday`, `Sunday`, `Intime window onpen till`, `Shift Time (Day)`, `Shift Time (Night)`, `Comments`, `WFH Credits`

**Critical Parsing Notes:**
- Column name is `"Intime window onpen till"` — use this exact string (it is a typo in the source file).
- `Working Model = "Permanent WFH"` → `is_permanent_wfh = True`.
- `WFH Credits` may be blank for interns (Bhavya Mendiratta, Apoorv Mahajan) — default to `0`.
- `Intime window` may contain a free-text note for some employees (e.g., Lovneet's rotational comment) — default to NULL when not parseable as a time.
- Day columns contain: `"WFO"`, `"WFH"`, or `"Dayoff"`.
- This file has no date period. Upload once; update when policies change.
- Match roster employees to biometric emp_codes by name: normalize with `" ".join(name.split())` before matching (case-insensitive).

---

## 15. Database Schema

All tables created via `Base.metadata.create_all(engine)` on startup. Use Python `uuid.uuid4` as default for UUID PKs (not a DB-level default).

### 15.1 Mermaid ERD

```mermaid
erDiagram
    BRONZE_UPLOADS {
        uuid id PK
        varchar file_type
        varchar original_filename
        date period_start
        date period_end
        timestamp uploaded_at
        int row_count
        varchar status
        text error_message
    }
    BRONZE_GREYTHR_RAW {
        uuid id PK
        uuid upload_id FK
        varchar employee_no
        varchar name
        varchar leave_type
        varchar transaction_type
        date from_date
        date to_date
        numeric days
        date expire_date
        text reason
    }
    BRONZE_BIOMETRIC_RAW {
        uuid id PK
        uuid upload_id FK
        varchar emp_code
        varchar employee_name
        date att_date
        varchar in_time
        varchar out_time
        varchar shift
        int work_duration_minutes
        int late_by_minutes
        int early_going_by_minutes
        varchar status
        text punch_records
    }
    BRONZE_ROSTER_RAW {
        uuid id PK
        uuid upload_id FK
        varchar name
        varchar project
        varchar client
        varchar working_model
        varchar monday
        varchar tuesday
        varchar wednesday
        varchar thursday
        varchar friday
        varchar saturday
        varchar sunday
        varchar intime_window
        int wfh_credits
    }
    SILVER_EMPLOYEES {
        uuid id PK
        varchar emp_code UK
        varchar name
        varchar email
        varchar project
        varchar client
        varchar in_team_role
        varchar billing_status
        varchar working_model
        boolean is_permanent_wfh
        int wfh_credits_monthly
        time intime_deadline
        varchar shift_time_day
        varchar shift_time_night
        varchar schedule_monday
        varchar schedule_tuesday
        varchar schedule_wednesday
        varchar schedule_thursday
        varchar schedule_friday
        varchar schedule_saturday
        varchar schedule_sunday
        text comments
        uuid roster_upload_id FK
        timestamp updated_at
    }
    SILVER_LEAVE_TRANSACTIONS {
        uuid id PK
        uuid upload_id FK
        varchar emp_code
        varchar employee_name
        varchar leave_type
        varchar transaction_type
        date from_date
        date to_date
        numeric days
        date period_start
        date period_end
    }
    SILVER_DAILY_ATTENDANCE {
        uuid id PK
        uuid upload_id FK
        varchar emp_code
        date att_date
        time in_time
        time out_time
        varchar shift
        int work_duration_minutes
        int late_by_minutes
        int early_going_by_minutes
        varchar status
        boolean is_half_present
        boolean is_no_out_punch
        boolean is_absent
        boolean is_weekly_off
        boolean has_approved_leave
        varchar approved_leave_type
        date period_start
        date period_end
    }
    GOLD_PERIOD_STATS {
        uuid id PK
        varchar emp_code
        date period_start
        date period_end
        int total_working_days
        numeric present_days
        numeric absent_days
        numeric absent_without_leave_days
        int late_arrival_count
        int early_departure_count
        int no_out_punch_count
        int half_day_count
        int wfh_days_availed
        int wfh_credits_allocated
        int total_work_minutes
        int avg_daily_work_minutes
        jsonb leave_summary
    }
    GOLD_EMPLOYEE_FLAGS {
        uuid id PK
        varchar emp_code
        varchar employee_name
        date period_start
        date period_end
        varchar flag_type
        numeric flag_value
        numeric threshold_value
        jsonb flag_details
        boolean is_active
        boolean email_sent
        timestamp email_sent_at
    }
    APP_USERS {
        uuid id PK
        varchar email UK
        varchar password_hash
        varchar full_name
        varchar role
        boolean is_active
        timestamp last_login
    }
    APP_EMAIL_TEMPLATES {
        uuid id PK
        varchar name
        varchar flag_type
        varchar subject
        text body
        jsonb available_variables
        boolean is_active
        timestamp updated_at
    }
    APP_FLAG_THRESHOLDS {
        uuid id PK
        varchar flag_type UK
        numeric threshold_value
        varchar threshold_unit
        text description
        boolean is_active
        timestamp updated_at
    }
    APP_EMAIL_LOG {
        uuid id PK
        uuid flag_id FK
        uuid template_id FK
        varchar emp_code
        varchar recipient_email
        varchar subject
        text body_preview
        varchar status
        text error_message
        timestamp sent_at
        varchar sent_by
    }

    BRONZE_UPLOADS ||--o{ BRONZE_GREYTHR_RAW : "contains"
    BRONZE_UPLOADS ||--o{ BRONZE_BIOMETRIC_RAW : "contains"
    BRONZE_UPLOADS ||--o{ BRONZE_ROSTER_RAW : "contains"
    BRONZE_UPLOADS ||--o{ SILVER_EMPLOYEES : "sourced from"
    SILVER_EMPLOYEES ||--o{ SILVER_LEAVE_TRANSACTIONS : "emp_code"
    SILVER_EMPLOYEES ||--o{ SILVER_DAILY_ATTENDANCE : "emp_code"
    SILVER_EMPLOYEES ||--o{ GOLD_PERIOD_STATS : "emp_code"
    SILVER_EMPLOYEES ||--o{ GOLD_EMPLOYEE_FLAGS : "emp_code"
    GOLD_EMPLOYEE_FLAGS ||--o{ APP_EMAIL_LOG : "triggers"
    APP_EMAIL_TEMPLATES ||--o{ APP_EMAIL_LOG : "used in"
```

### 15.2 Full Schema Definitions

**Bronze Layer**

```
TABLE: bronze_uploads
  id              UUID PK
  file_type       VARCHAR(20) NOT NULL  -- 'greythr', 'biometric', 'roster'
  original_filename VARCHAR(255)
  period_start    DATE  NULLABLE
  period_end      DATE  NULLABLE
  uploaded_at     TIMESTAMP DEFAULT NOW()
  row_count       INTEGER
  status          VARCHAR(20) DEFAULT 'pending'  -- 'pending','processing','processed','failed'
  error_message   TEXT  NULLABLE

TABLE: bronze_greythr_raw
  id UUID PK | upload_id UUID FK | sl_no INTEGER | employee_no VARCHAR(20)
  name VARCHAR(150) | manager_no VARCHAR(20) | manager_name VARCHAR(150)
  leave_type VARCHAR(100) | transaction_type VARCHAR(50) | posted_date TIMESTAMP
  from_date DATE | to_date DATE | days NUMERIC(5,2) | expire_date DATE
  reason TEXT | remarks TEXT | created_at TIMESTAMP DEFAULT NOW()

TABLE: bronze_biometric_raw
  id UUID PK | upload_id UUID FK | emp_code VARCHAR(20) | employee_name VARCHAR(150)
  att_date DATE | in_time VARCHAR(10) | out_time VARCHAR(10) | shift VARCHAR(20)
  scheduled_in_time VARCHAR(10) | scheduled_out_time VARCHAR(10)
  work_duration_minutes INTEGER | ot_minutes INTEGER | total_duration_minutes INTEGER
  late_by_minutes INTEGER | early_going_by_minutes INTEGER
  status VARCHAR(60) | punch_records TEXT | created_at TIMESTAMP DEFAULT NOW()

TABLE: bronze_roster_raw
  id UUID PK | upload_id UUID FK | name VARCHAR(150) | project VARCHAR(100)
  client VARCHAR(50) | in_team_role VARCHAR(50) | billing_status VARCHAR(50)
  working_model VARCHAR(50) | monday VARCHAR(10) | tuesday VARCHAR(10)
  wednesday VARCHAR(10) | thursday VARCHAR(10) | friday VARCHAR(10)
  saturday VARCHAR(10) | sunday VARCHAR(10) | intime_window VARCHAR(50)
  shift_time_day VARCHAR(100) | shift_time_night VARCHAR(100)
  comments TEXT | wfh_credits INTEGER | created_at TIMESTAMP DEFAULT NOW()
```

**Silver Layer**

```
TABLE: silver_employees
  id UUID PK | emp_code VARCHAR(20) UNIQUE NULLABLE | name VARCHAR(150) NOT NULL
  email VARCHAR(150) NULLABLE | project VARCHAR(100) | client VARCHAR(50)
  in_team_role VARCHAR(50) | billing_status VARCHAR(50) | working_model VARCHAR(50)
  is_permanent_wfh BOOLEAN DEFAULT FALSE | wfh_credits_monthly INTEGER DEFAULT 4
  intime_deadline TIME NULLABLE | shift_time_day VARCHAR(100) | shift_time_night VARCHAR(100)
  schedule_monday VARCHAR(10) | schedule_tuesday VARCHAR(10) | schedule_wednesday VARCHAR(10)
  schedule_thursday VARCHAR(10) | schedule_friday VARCHAR(10) | schedule_saturday VARCHAR(10)
  schedule_sunday VARCHAR(10) | comments TEXT
  roster_upload_id UUID FK(bronze_uploads) NULLABLE
  created_at TIMESTAMP DEFAULT NOW() | updated_at TIMESTAMP DEFAULT NOW()

TABLE: silver_leave_transactions
  id UUID PK | upload_id UUID FK | emp_code VARCHAR(20) | employee_name VARCHAR(150)
  manager_no VARCHAR(20) | manager_name VARCHAR(150) | leave_type VARCHAR(100)
  transaction_type VARCHAR(50) | posted_date TIMESTAMP | from_date DATE | to_date DATE
  days NUMERIC(5,2) | expire_date DATE | reason TEXT | remarks TEXT
  period_start DATE | period_end DATE | created_at TIMESTAMP DEFAULT NOW()

TABLE: silver_daily_attendance
  id UUID PK | upload_id UUID FK | emp_code VARCHAR(20) | employee_name VARCHAR(150)
  att_date DATE | in_time TIME | out_time TIME | shift VARCHAR(20)
  scheduled_in_time TIME | scheduled_out_time TIME
  work_duration_minutes INTEGER | ot_minutes INTEGER | total_duration_minutes INTEGER
  late_by_minutes INTEGER | early_going_by_minutes INTEGER
  status VARCHAR(60) | is_half_present BOOLEAN DEFAULT FALSE
  is_no_out_punch BOOLEAN DEFAULT FALSE | is_absent BOOLEAN DEFAULT FALSE
  is_weekly_off BOOLEAN DEFAULT FALSE | has_approved_leave BOOLEAN DEFAULT FALSE
  approved_leave_type VARCHAR(100) NULLABLE
  period_start DATE | period_end DATE | created_at TIMESTAMP DEFAULT NOW()
  UNIQUE CONSTRAINT: (emp_code, att_date, upload_id)
```

**Gold Layer**

```
TABLE: gold_period_stats
  id UUID PK | emp_code VARCHAR(20) | period_start DATE | period_end DATE
  total_working_days INTEGER | present_days NUMERIC(5,2) | absent_days NUMERIC(5,2)
  absent_without_leave_days NUMERIC(5,2) | late_arrival_count INTEGER
  early_departure_count INTEGER | no_out_punch_count INTEGER | half_day_count INTEGER
  wfh_days_availed INTEGER | wfh_credits_allocated INTEGER
  total_work_minutes INTEGER | avg_daily_work_minutes INTEGER
  leave_summary JSONB | created_at TIMESTAMP DEFAULT NOW()
  UNIQUE CONSTRAINT: (emp_code, period_start, period_end)

TABLE: gold_employee_flags
  id UUID PK | emp_code VARCHAR(20) | employee_name VARCHAR(150)
  period_start DATE | period_end DATE | flag_type VARCHAR(60)
  flag_value NUMERIC(8,2) | threshold_value NUMERIC(8,2) | flag_details JSONB
  is_active BOOLEAN DEFAULT TRUE | email_sent BOOLEAN DEFAULT FALSE
  email_sent_at TIMESTAMP NULLABLE | created_at TIMESTAMP DEFAULT NOW()
```

**Application Tables**

```
TABLE: app_users
  id UUID PK | email VARCHAR(150) UNIQUE NOT NULL | password_hash VARCHAR(255) NOT NULL
  full_name VARCHAR(100) | role VARCHAR(20) DEFAULT 'hr'
  is_active BOOLEAN DEFAULT TRUE | created_at TIMESTAMP DEFAULT NOW()
  last_login TIMESTAMP NULLABLE

  DEFAULT SEED (insert if table empty):
    email: hr@shorthills.ai
    password: HR@ShortHills2024 (bcrypt hashed)
    full_name: HR Admin | role: hr

TABLE: app_email_templates
  id UUID PK | name VARCHAR(150) NOT NULL | flag_type VARCHAR(60) NULLABLE
  subject VARCHAR(255) NOT NULL | body TEXT NOT NULL
  available_variables JSONB | is_active BOOLEAN DEFAULT TRUE
  created_at TIMESTAMP DEFAULT NOW() | updated_at TIMESTAMP DEFAULT NOW()

TABLE: app_flag_thresholds
  id UUID PK | flag_type VARCHAR(60) UNIQUE NOT NULL
  threshold_value NUMERIC(8,2) NOT NULL | threshold_unit VARCHAR(20)
  description TEXT | is_active BOOLEAN DEFAULT TRUE
  updated_at TIMESTAMP DEFAULT NOW()

TABLE: app_email_log
  id UUID PK | flag_id UUID NULLABLE FK(gold_employee_flags)
  template_id UUID NULLABLE FK(app_email_templates)
  emp_code VARCHAR(20) | recipient_email VARCHAR(150)
  subject VARCHAR(255) | body_preview TEXT
  status VARCHAR(20) | error_message TEXT NULLABLE
  sent_at TIMESTAMP NULLABLE | sent_by VARCHAR(150)
  created_at TIMESTAMP DEFAULT NOW()
```

---

## 16. Data Pipeline — Medallion Architecture

### Stage 1 → Bronze (Raw Ingest)
- Accept .xlsx via FastAPI upload endpoint
- Parse using algorithms in Section 14
- Validate expected columns; on mismatch return HTTP 422 with specific message
- Write raw rows to bronze tables
- Duplicate detection: check same `file_type` + overlapping period before insert → HTTP 409 on match
- Update `bronze_uploads.status` to `'processed'` or `'failed'`

### Stage 2 → Silver (Clean & Enrich)
1. Normalize all name strings: strip whitespace, title case
2. Convert biometric time strings (`"10:26"`) to `TIME`. If unparseable → NULL
3. Cross-reference `silver_daily_attendance` absent records against `silver_leave_transactions` Availed rows covering that date → set `has_approved_leave`, `approved_leave_type`
4. Skip absence cross-reference for `is_permanent_wfh = True` employees
5. Upsert `silver_employees` from roster data (update if exists by name, insert if new)
6. Match roster employees to biometric emp_codes by normalized name

### Stage 3 → Gold (Analyze & Flag)
1. Compute `gold_period_stats` per employee (upsert)
2. Evaluate all 9 flag types against `app_flag_thresholds`
3. Insert/update `gold_employee_flags` — check `(emp_code, flag_type, period_start)` before insert to avoid duplicates
4. Pipeline is fully idempotent: re-running recalculates everything

---

## 17. Flag Types & Logic

### Default Thresholds (seed into `app_flag_thresholds` on startup)

| Flag Type | Default Threshold | Unit | Description |
|---|---|---|---|
| `LATE_ARRIVAL` | 3 | count | Late arrivals per period exceeding N |
| `EARLY_DEPARTURE` | 3 | count | Early departures per period exceeding N |
| `ABSENT_WITHOUT_LEAVE` | 2 | days | Absent without leave exceeding N days |
| `CONSECUTIVE_ABSENCE` | 2 | days | Consecutive absent-without-leave days |
| `NO_OUT_PUNCH` | 3 | count | No clock-out occurrences exceeding N |
| `HALF_DAY_FREQUENCY` | 4 | count | Half-day occurrences exceeding N |
| `WFH_QUOTA_EXCEEDED` | 0 | days | WFH availed > monthly credit (any excess) |
| `LOW_WORK_HOURS` | 300 | minutes | Work duration on present day < N minutes |
| `WFO_VIOLATION` | 1 | count | Scheduled WFO day, absent without leave |

### Flag Evaluation Rules

**LATE_ARRIVAL:** `late_by_minutes > 0` AND `status IN ('Present', '½Present')` AND `is_permanent_wfh = False`. Count occurrences > threshold.

**EARLY_DEPARTURE:** `early_going_by_minutes > 0` AND status contains `'Present'`. Count > threshold.

**ABSENT_WITHOUT_LEAVE:** `is_absent = True` AND `is_weekly_off = False` AND `has_approved_leave = False` AND `is_permanent_wfh = False`. Count > threshold.

**CONSECUTIVE_ABSENCE:** From absent-without-leave dates, find longest consecutive run (working days only, skip WeeklyOff). Longest run ≥ threshold → flag.

**NO_OUT_PUNCH:** `is_no_out_punch = True`. Count > threshold.

**HALF_DAY_FREQUENCY:** `is_half_present = True`. Count > threshold.

**WFH_QUOTA_EXCEEDED:** Sum `days` from `silver_leave_transactions` WHERE `leave_type = 'WFH'` AND `transaction_type = 'Availed'`. Compare vs `silver_employees.wfh_credits_monthly`. If availed > credits → flag. `flag_value` = excess days.

**LOW_WORK_HOURS:** Present days where `work_duration_minutes < threshold`. Count > 0 → flag.

**WFO_VIOLATION:** For each absent-without-leave day, check `schedule_{day_of_week}` in `silver_employees`. If `= 'WFO'` → violation. Count > threshold → flag.

---

## 18. Email System

### Microsoft Graph API Configuration

```env
GRAPH_TENANT_ID=           # Azure AD Tenant ID
GRAPH_CLIENT_ID=           # Azure App Client ID
GRAPH_CLIENT_SECRET=       # Azure App Client Secret
GRAPH_SENDER_EMAIL=apoorv.mahajan@shorthills.ai
```

**Graceful degradation (required):** Before any send, check that all three Graph env vars are non-empty. If any are empty:
- Return HTTP 503: `{"detail": "Email service is not configured. Please set GRAPH_TENANT_ID, GRAPH_CLIENT_ID, and GRAPH_CLIENT_SECRET in the environment."}`
- Log warning server-side. App must NOT crash.
- Frontend shows this as a styled warning banner.

**Graph API flow:**
1. POST to `https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token` → get access token
2. POST to `https://graph.microsoft.com/v1.0/users/{sender_email}/sendMail` with token
3. On HTTP error from Graph: log full response body, return error to frontend

### Template Variable Substitution

Use `{{variable_name}}` syntax. Available variables:

```
{{employee_name}}   {{emp_code}}       {{period}}
{{period_start}}    {{period_end}}     {{flag_count}}
{{flag_dates}}      {{threshold}}      {{sender_name}}
```

`{{sender_name}}` = `"HR Team, ShortHills Tech"`

### Default Email Templates (seed 8 templates on startup)

**Template 1 — LATE_ARRIVAL**
Subject: `Attendance Notice – Late Arrivals | {{period}}`
Body:
```
Dear {{employee_name}},

We have reviewed your attendance records for {{period}} and noted that you arrived late on {{flag_count}} occasion(s) ({{flag_dates}}).

As per company policy, your shift start time requires you to be logged in by your designated InTime. Repeated late arrivals impact team productivity and project delivery.

We request you to ensure punctual attendance going forward. Please acknowledge this email or connect with the HR team if there are any concerns.

Regards,
{{sender_name}}
```

**Template 2 — ABSENT_WITHOUT_LEAVE**
Subject: `Attendance Concern – Uninformed Absence | {{period}}`
Body:
```
Dear {{employee_name}},

Our records indicate that you were absent without an approved leave on {{flag_count}} day(s) during {{period}} ({{flag_dates}}).

An uninformed absence affects team planning and is a non-compliance with company attendance policy. Kindly ensure that any planned or unplanned absence is regularized through the GreytHR leave management system.

If these absences were due to an emergency or technical difficulty, please contact HR immediately to regularize.

Regards,
{{sender_name}}
```

**Template 3 — CONSECUTIVE_ABSENCE**
Subject: `Urgent: Consecutive Absence Without Leave | {{period}}`
Body:
```
Dear {{employee_name}},

We have observed that you have been continuously absent for {{flag_count}} or more consecutive working days ({{flag_dates}}) during {{period}} without an approved leave on record.

This is a serious compliance concern. Please respond to this email within 24 hours with a valid reason or proof of leave. Failure to respond may result in escalation per company policy.

Regards,
{{sender_name}}
```

**Template 4 — NO_OUT_PUNCH**
Subject: `Biometric Compliance – Missing Out-Punch | {{period}}`
Body:
```
Dear {{employee_name}},

Your biometric attendance records for {{period}} show that you did not clock out on {{flag_count}} occasion(s) ({{flag_dates}}).

Regular and complete biometric punching (both in and out) is mandatory. Incomplete records affect payroll and compliance reporting. Please ensure you clock out before leaving the premises each day.

Regards,
{{sender_name}}
```

**Template 5 — WFH_QUOTA_EXCEEDED**
Subject: `WFH Policy Non-Compliance | {{period}}`
Body:
```
Dear {{employee_name}},

As per company policy, your monthly WFH allocation for {{period}} is {{threshold}} day(s). Our records indicate you have availed {{flag_count}} WFH day(s) this period, exceeding your quota.

Please ensure that WFH requests remain within the approved limits. For any exceptions or special circumstances, please write to HR in advance for approval.

Regards,
{{sender_name}}
```

**Template 6 — WFO_VIOLATION**
Subject: `Work-From-Office Compliance | {{period}}`
Body:
```
Dear {{employee_name}},

As per your roster, you are required to be present at the office on designated WFO days. Our records show that you were absent on {{flag_count}} WFO-mandated day(s) ({{flag_dates}}) during {{period}} without an approved leave.

Please ensure compliance with your scheduled WFO days. Reach out to your manager or HR if there is a genuine concern that requires a roster change.

Regards,
{{sender_name}}
```

**Template 7 — EARLY_DEPARTURE**
Subject: `Attendance Notice – Early Departures | {{period}}`
Body:
```
Dear {{employee_name}},

We have noted that you left office earlier than your scheduled shift end on {{flag_count}} occasion(s) during {{period}} ({{flag_dates}}).

Regular early departures without prior approval are not in line with our attendance policy. If you need to leave early on any day, please inform your manager and mark it in GreytHR.

Regards,
{{sender_name}}
```

**Template 8 — HALF_DAY_FREQUENCY**
Subject: `Attendance Pattern – Repeated Half-Days | {{period}}`
Body:
```
Dear {{employee_name}},

Your attendance records for {{period}} reflect {{flag_count}} half-day markings. While occasional half-days are understandable, a pattern of frequent half-days impacts project commitments and team schedules.

We request you to plan your attendance better and use the leave application process for planned absences.

Regards,
{{sender_name}}
```

---

## 19. Application Modules & UI Pages

**Page 1 — Login (`/login`)**
Email + password form. On success: store JWT in localStorage, redirect to `/dashboard`. On failure: inline error "Invalid email or password." No registration page.

**Page 2 — Dashboard Overview (`/dashboard`)**
Summary cards: Total Employees, Flagged This Period (red badge), Attendance Rate %, WFH Compliance %, Emails Sent This Period.
Charts: Bar chart (attendance by employee), Pie chart (flag distribution), Line chart (late arrivals trend).
Period selector dropdown.

**Page 3 — Data Upload (`/upload`)**
Three upload cards (GreytHR, Biometric, Roster). Each shows: current status, last upload filename + date, row count. Upload accepts .xlsx only.
Upload history table at bottom.
"Run Pipeline" button: disabled until both GreytHR + Biometric uploaded for period. Shows processing indicator on click.

**Page 4 — Employee Directory (`/employees`)**
Table: Emp Code, Name, Email (editable inline), Project, Client, Role, Billing Status, Working Model, WFH Credits, InTime Deadline.
Row click → detail sidebar: all roster fields, Mon–Sun schedule chips, current period stats, active flags.

**Page 5 — Attendance Analysis (`/attendance`)**
Period selector. Table per employee: Present, Absent, Absent w/o Leave, Late, Early, No Out-Punch, Half Days, Work Hours.
Employee click → calendar heatmap (green/red/yellow/grey/blue). Cell click → InTime, OutTime, LateBy, EarlyGoingBy.

**Page 6 — Leave Analysis (`/leave`)**
Period selector. Per-employee leave types as columns with availed days. WFH availed vs quota column. Lapsed credits view.

**Page 7 — Flagged Employees (`/flags`)**
Filter bar: flag type, employee, period.
Table: Employee, Flag Type, Flag Value, Threshold, Dates Affected, Email Sent, Actions (Send Email, Mark Resolved).
Bulk select → Send Bulk Emails.

**Page 8 — Email Center (`/email`)**
Tab 1 — Send Email: Select employees → Select template → Preview rendered → Confirm send.
If not configured: non-dismissable yellow banner "Email service is not yet configured. Contact the system administrator."
Tab 2 — Email History: Table with recipient, subject, flag type, template, status, sent_at, sent_by.

**Page 9 — Settings (`/settings`)**
Tab 1 — Flag Thresholds: Editable table per flag type. Save per row.
Tab 2 — Email Templates: List with Edit/Delete. "Create New Template" form with preview.
Tab 3 — System Config: Show GRAPH_TENANT_ID / CLIENT_ID / SECRET_SECRET as Set ✓ / Not Set ✗. Never show actual values.

---

## 20. API Endpoints

All prefixed `/api/v1`. All except `/api/v1/auth/login` require `Authorization: Bearer <token>`.

```
Auth:
POST   /api/v1/auth/login
GET    /api/v1/auth/me

Uploads:
POST   /api/v1/upload/greythr      multipart: file, period_start, period_end
POST   /api/v1/upload/biometric    multipart: file, period_start, period_end
POST   /api/v1/upload/roster       multipart: file
GET    /api/v1/upload/history
DELETE /api/v1/upload/{upload_id}

Pipeline:
POST   /api/v1/pipeline/run        body: {period_start, period_end}
GET    /api/v1/pipeline/status/{period_start}/{period_end}

Employees:
GET    /api/v1/employees
GET    /api/v1/employees/{emp_code}
PATCH  /api/v1/employees/{emp_code}/email

Attendance:
GET    /api/v1/attendance?period_start=&period_end=
GET    /api/v1/attendance/{emp_code}?period_start=&period_end=

Leave:
GET    /api/v1/leave?period_start=&period_end=
GET    /api/v1/leave/{emp_code}?period_start=&period_end=

Flags:
GET    /api/v1/flags?period_start=&period_end=&flag_type=&emp_code=
PATCH  /api/v1/flags/{flag_id}/resolve
POST   /api/v1/flags/recompute     body: {period_start, period_end}

Email:
GET    /api/v1/email/templates
POST   /api/v1/email/templates
PUT    /api/v1/email/templates/{id}
DELETE /api/v1/email/templates/{id}
POST   /api/v1/email/send          body: {flag_ids[], template_id, preview_only: bool}
GET    /api/v1/email/logs?emp_code=&period_start=&period_end=
GET    /api/v1/email/config-status

Settings:
GET    /api/v1/settings/thresholds
PUT    /api/v1/settings/thresholds/{flag_type}

Analytics:
GET    /api/v1/analytics/overview?period_start=&period_end=
GET    /api/v1/analytics/attendance-chart?period_start=&period_end=
GET    /api/v1/analytics/flag-distribution?period_start=&period_end=
```

---

## 21. Authentication

- JWT signed with `SECRET_KEY` (env), algorithm `HS256`, expiry 24 hours
- Passwords hashed with bcrypt via passlib
- On startup: if `app_users` empty → seed default user (see Section 15.2)
- All non-auth routes protected via `get_current_user` FastAPI dependency
- Frontend: store token in `localStorage` as `access_token`. Axios interceptor adds `Authorization: Bearer` header. On 401 → redirect to `/login` and clear localStorage

---

## 22. Project Folder Structure

```
project-root/
├── docker-compose.yml
├── .env                          # NOT committed
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                   # FastAPI app entry, startup creates tables + runs seed
│   ├── database.py               # Engine (pool_pre_ping, pool_recycle), session, create_all
│   ├── models/
│   │   ├── bronze.py
│   │   ├── silver.py
│   │   ├── gold.py
│   │   └── app.py
│   ├── schemas/
│   ├── routers/
│   │   ├── auth.py | upload.py | pipeline.py | employees.py
│   │   ├── attendance.py | leave.py | flags.py | email.py
│   │   ├── settings.py | analytics.py
│   ├── services/
│   │   ├── parsers/
│   │   │   ├── greythr_parser.py
│   │   │   ├── biometric_parser.py
│   │   │   └── roster_parser.py
│   │   ├── pipeline/
│   │   │   ├── bronze_to_silver.py
│   │   │   └── silver_to_gold.py
│   │   ├── flag_engine.py
│   │   └── email_service.py
│   ├── utils/
│   │   ├── date_utils.py         # Excel serial date conversion
│   │   └── auth_utils.py
│   └── seed.py
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx | App.jsx
│       ├── api/
│       ├── components/
│       ├── pages/
│       │   ├── Login.jsx | Dashboard.jsx | Upload.jsx | Employees.jsx
│       │   ├── Attendance.jsx | Leave.jsx | Flags.jsx
│       │   ├── EmailCenter.jsx | Settings.jsx
│       ├── context/
│       │   └── AuthContext.jsx
│       └── utils/
```

---

## 23. Docker Configuration

### `docker-compose.yml`
```yaml
version: "3.9"
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./uploads:/app/uploads
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped
```

### `backend/Dockerfile`
```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/uploads
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `backend/requirements.txt`
```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy==2.0.30
psycopg2-binary==2.9.9
pydantic[email]==2.7.1
pydantic-settings==2.2.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
pandas==2.2.2
openpyxl==3.1.2
httpx==0.27.0
python-dotenv==1.0.1
```

### `frontend/Dockerfile`
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### `frontend/nginx.conf`
```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

---

## 24. Environment Variables

### `.env` (actual — do not commit)
```env
DATABASE_URL=postgresql+psycopg2://postgres.cblbhphawxrjnygwlkin:n0h6VpgjuvyZHacq@aws-1-ap-south-1.pooler.supabase.com:5432/postgres
SECRET_KEY=shorthills_hr_dashboard_secret_key_change_before_prod_2024
ACCESS_TOKEN_EXPIRE_HOURS=24
GRAPH_TENANT_ID=
GRAPH_CLIENT_ID=
GRAPH_CLIENT_SECRET=
GRAPH_SENDER_EMAIL=apoorv.mahajan@shorthills.ai
APP_ENV=production
CORS_ORIGINS=http://localhost:3000
```

### `.env.example` (committed)
Same structure with all values empty or placeholder.

---

## 25. Startup Sequence

On backend startup (`main.py` lifespan event), execute in order:
1. Load env from `.env`
2. Create SQLAlchemy engine with `pool_pre_ping=True`, `pool_recycle=300`
3. Call `Base.metadata.create_all(engine)` — idempotent, never drops tables
4. Call `seed_defaults()`:
   - If `app_users` empty → insert default HR user (bcrypt-hash the password)
   - If `app_email_templates` empty → insert all 8 default templates
   - If `app_flag_thresholds` empty → insert all 9 default thresholds
5. Wrap seed in try/except — log errors but do not prevent startup

---

## 26. Error Handling Standards

- All FastAPI endpoints return `{"detail": "human-readable message"}` on error
- Never expose Python stack traces in API responses
- Excel parse errors → HTTP 422 with column-level messages
- Duplicate upload → HTTP 409
- Email not configured → HTTP 503 with setup instruction
- DB connection failure on startup → log and exit code 1
- Pipeline errors → written to `bronze_uploads.error_message`, surfaced in UI

---

## 27. Known Data Quirks (Must Handle — Do Not Skip)

1. **GreytHR date serials:** `From Date` / `To Date` are integers (e.g., `46101`). Convert: `datetime(1899, 12, 30) + timedelta(days=n)`. Do NOT use pandas auto-detect.
2. **Biometric report format:** Block-parsed (not flat table). Use algorithm from Section 14.2 exactly.
3. **Trailing spaces in status:** `"Present "`, `"WeeklyOff "` have trailing spaces. Always `.strip()`.
4. **½ Unicode character:** Status `"½Present"` uses U+00BD. Do not mangle. Use UTF-8 throughout.
5. **Roster column name typo:** Column is `"Intime window onpen till"` — exact string, misspelled as-is.
6. **Intern WFH Credits blank:** Bhavya Mendiratta and Apoorv Mahajan have blank WFH Credits. Default to `0`.
7. **Name normalization:** Use `" ".join(name.split())` before matching roster names to biometric emp codes.
8. **Permanent WFH in biometric:** `NS` shift / `Absent` status for these employees is normal. Do not flag.
9. **Leading blank column in biometric:** Column A is always empty. Data starts from column B (index 1) in openpyxl row iteration.

---

*End of PRD v2. All 27 sections are required. Do not skip any during implementation.*
