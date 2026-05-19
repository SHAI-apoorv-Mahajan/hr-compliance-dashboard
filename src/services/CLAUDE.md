# src/services — Business logic

Maps to `backend/services/` (PRD §22). Parsers, pipeline stages, flag engine, email service.

## Layout
```
backend/services/
├── parsers/
│   ├── greythr_parser.py     # FR-002
│   ├── biometric_parser.py   # FR-003 (block parser — see PRD §14.2)
│   └── roster_parser.py      # FR-004
├── pipeline/
│   ├── bronze_to_silver.py   # FR-006, FR-007
│   └── silver_to_gold.py     # FR-008, FR-009
├── flag_engine.py            # 9 flag rules (PRD §17)
└── email_service.py          # Graph API + graceful 503 (FR-013, FR-014)
```

## Parser rules (do not violate)
- **GreytHR `From Date` / `To Date`** are Excel serial integers. Convert via `datetime(1899, 12, 30) + timedelta(days=int(serial))`. **Do not** use pandas auto-detect — it loses precision (PRD §27 #1).
- **Biometric** is a block-parsed report. Use `openpyxl.load_workbook(..., read_only=True, data_only=True)` and the algorithm in PRD §14.2 verbatim. **Do not** use `pd.read_excel`.
- Status values: always `.strip()`. Preserve U+00BD (½). Status `"½Present"` and `"½Present (No OutPunch)"` use Unicode ½ (PRD §27 #3, #4).
- Roster column name `"Intime window onpen till"` is a typo — use it verbatim (PRD §27 #5).
- `wfh_credits` blank in roster → default to `0` (intern case, PRD §27 #6).
- Name normalization: `" ".join(name.split())` before matching roster ↔ biometric (PRD §27 #7).

## Pipeline rules
- All writes are idempotent (upsert keyed on the unique constraints from `src/persistence/CLAUDE.md`).
- Permanent WFH employees (`silver_employees.is_permanent_wfh = TRUE`) are **never** flagged for ABSENT_WITHOUT_LEAVE, WFO_VIOLATION, or LATE_ARRIVAL — their NS-shift absences are expected (FR-007, PRD §27 #8).
- Log every stage transition to stdout with ISO timestamps + row counts (NFR-009).

## Flag engine
- One function per flag type. Each takes the period + thresholds + silver/gold data, returns a list of `gold_employee_flags` rows.
- Re-running must update existing rows (keyed on `(emp_code, flag_type, period_start)`), not create duplicates (FR-009).
- HR-resolved flags (`is_active = FALSE`) must not be auto-resurrected by a re-run.

## Email service
- Before any send: check `GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID`, `GRAPH_CLIENT_SECRET` are non-empty. If any is empty → return HTTP 503 with the exact body from FR-014. Do not crash.
- OAuth2 client-credentials flow against `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token`.
- Send via `https://graph.microsoft.com/v1.0/users/{GRAPH_SENDER_EMAIL}/sendMail`.
- On Graph error: log the full response body to `app_email_log.error_message`. The API response to the client is generic.
- Variable substitution uses `{{name}}` syntax. Available: `employee_name`, `emp_code`, `period`, `period_start`, `period_end`, `flag_count`, `flag_dates`, `threshold`, `sender_name` (= `"HR Team, ShortHills Tech"`).
