# Architecture

> Diagrams and runtime topology. Detailed requirements live in [PRD.md](PRD.md); detailed schema lives in [data-model.md](data-model.md). This document is the visual / structural complement, not a re-statement of those.

## Runtime topology

```mermaid
graph TB
    subgraph Browser
        HR["HR Admin"]
    end

    subgraph DockerCompose["docker-compose (developer machine or single VM)"]
        FE["frontend container · nginx :3000<br/>serves React SPA<br/>reverse-proxies /api/* → backend:8000"]
        BE["backend container · uvicorn :8000<br/>FastAPI · SQLAlchemy 2.x"]
    end

    subgraph External
        SUPA[("Supabase Postgres<br/>aws-1-ap-south-1.pooler<br/>port 5432")]
        GRAPH["Microsoft Graph API<br/>login.microsoftonline.com<br/>graph.microsoft.com"]
    end

    HR -->|"http :3000"| FE
    FE -->|"http :8000 (internal)"| BE
    BE -->|"psycopg2<br/>pool_pre_ping=True<br/>pool_recycle=300"| SUPA
    BE -.->|"OAuth2 client credentials<br/>+ sendMail<br/>(gated on env vars)"| GRAPH
```

The compose file has **two services** — `backend` and `frontend`. There is intentionally no local Postgres container (Supabase is remote; see [ADR-001](decisions/ADR-001-no-alembic-and-no-local-db.md)).

## Backend module map

```mermaid
graph LR
    main["main.py<br/>FastAPI app · lifespan"]
    db["database.py<br/>engine · SessionLocal · Base"]
    seed["seed.py<br/>HR user · 8 templates · 9 thresholds"]

    subgraph routers["routers/"]
        auth_r[auth.py]
        upload_r[upload.py]
        pipe_r[pipeline.py]
        emp_r[employees.py]
        att_r[attendance.py]
        leave_r[leave.py]
        flags_r[flags.py]
        email_r[email.py]
        set_r[settings.py]
        an_r[analytics.py]
    end

    subgraph services["services/"]
        parsers["parsers/<br/>greythr · biometric · roster"]
        pipe["pipeline/<br/>bronze_to_silver · silver_to_gold"]
        fe["flag_engine.py"]
        es["email_service.py"]
    end

    subgraph models["models/"]
        bronze[bronze.py]
        silver[silver.py]
        gold[gold.py]
        app[app.py]
    end

    main --> db
    main --> seed
    main --> routers

    upload_r --> parsers
    pipe_r --> pipe
    flags_r --> fe
    email_r --> es

    pipe --> models
    fe --> models
    es --> models
    parsers --> models
```

## Medallion data flow

```mermaid
flowchart LR
    X1[".xlsx · GreytHR leave"] -->|FR-002| BG[bronze_greythr_raw]
    X2[".xlsx · biometric"] -->|FR-003| BB[bronze_biometric_raw]
    X3[".xlsx · roster"] -->|FR-004| BR[bronze_roster_raw]

    BG -->|silver stage| SLT[silver_leave_transactions]
    BB -->|silver stage<br/>+ time-typed| SDA[silver_daily_attendance]
    BR -->|silver upsert by name| SE[silver_employees]

    SLT -.->|cross-reference<br/>Availed leave covers absence date| SDA
    SE -.->|is_permanent_wfh skip| SDA

    SDA -->|gold aggregate| GPS[gold_period_stats]
    SLT --> GPS
    SE --> GPS

    GPS -->|flag engine<br/>vs app_flag_thresholds| GEF[gold_employee_flags]
    SDA --> GEF
    SLT --> GEF

    GEF -->|email send<br/>FR-013/14| EL[app_email_log]
```

Each transition is **idempotent**: re-running the pipeline for the same period must produce the same gold rows (FR-008, FR-009). The dedup key on `gold_employee_flags` is `(emp_code, flag_type, period_start)`.

## Request lifecycles

### Login (FR-001)

```mermaid
sequenceDiagram
    participant BR as Browser
    participant FE as Frontend (nginx + React)
    participant BE as Backend (FastAPI)
    participant DB as Supabase

    BR->>FE: POST /api/v1/auth/login
    FE->>BE: POST /api/v1/auth/login (proxied)
    BE->>DB: SELECT * FROM app_users WHERE email=...
    DB-->>BE: row
    BE->>BE: bcrypt.verify(password, hash)
    BE->>DB: UPDATE app_users SET last_login=NOW()
    BE-->>FE: {access_token, token_type}
    FE-->>BR: 200 + localStorage.access_token
```

### Pipeline run (FR-018)

```mermaid
sequenceDiagram
    participant BR as Browser
    participant BE as Backend
    participant DB as Supabase

    BR->>BE: POST /api/v1/pipeline/run {period_start, period_end}
    BE->>DB: read bronze_uploads for period
    BE->>BE: bronze → silver (parse + cross-reference)
    BE->>DB: upsert silver_*
    BE->>BE: silver → gold (aggregate + flag engine)
    BE->>DB: upsert gold_period_stats
    BE->>DB: upsert gold_employee_flags (keyed on emp_code, flag_type, period_start)
    BE-->>BR: {stages: {bronze: …, silver: …, gold: …}}
```

### Email send (FR-013, FR-014)

```mermaid
sequenceDiagram
    participant BR as Browser
    participant BE as Backend
    participant GR as Microsoft Graph
    participant DB as Supabase

    BR->>BE: POST /api/v1/email/send {flag_ids[], template_id, preview_only}
    alt preview_only=true
        BE-->>BR: rendered emails (no Graph call)
    else preview_only=false
        BE->>BE: check GRAPH_TENANT_ID/CLIENT_ID/CLIENT_SECRET non-empty
        alt any empty
            BE-->>BR: 503 {"detail": "Email service is not configured…"} (FR-014)
        else all set
            BE->>GR: POST /oauth2/v2.0/token
            GR-->>BE: access_token
            loop per recipient
                BE->>GR: POST /users/{sender}/sendMail
                GR-->>BE: 202 / 4xx
                BE->>DB: INSERT app_email_log (status=sent|failed, error_message)
            end
            BE->>DB: UPDATE gold_employee_flags SET email_sent=TRUE, email_sent_at=NOW()
            BE-->>BR: results per recipient
        end
    end
```

## Cross-cutting concerns

- **Auth.** JWT HS256, 24h. Every non-auth route depends on `get_current_user`. Frontend axios interceptor handles 401 → redirect.
- **Idempotency.** All silver/gold writes use `INSERT ... ON CONFLICT DO UPDATE` (or the SQLAlchemy ORM equivalent) keyed on the natural-key constraints listed in [data-model.md](data-model.md).
- **Errors.** API responses: `{"detail": "..."}` only — never a stack trace. Specific codes per [.claude/rules/api-design.md](../.claude/rules/api-design.md).
- **Observability.** Pipeline stage transitions log ISO timestamp + row counts to stdout (NFR-009). Failed uploads write the full error to `bronze_uploads.error_message`.

## Decision records

- [ADR-001 — No Alembic, no local DB container](decisions/ADR-001-no-alembic-and-no-local-db.md)

Add new ADRs as `docs/decisions/ADR-NNN-short-slug.md` and link them here.
