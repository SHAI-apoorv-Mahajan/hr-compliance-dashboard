# Security

## Secrets
- `.env` is **never** committed. `.env.example` is committed with empty values.
- `Read(./.env)` and `Read(./.env.*)` are denied in `settings.json`. The `block-secret-writes.sh` hook also blocks any write that targets those paths.
- Frontend never receives raw password hashes, JWT signing secrets, or any `GRAPH_*` credential. The Settings → System Config page shows only `Set ✓` / `Not Set ✗` (PRD §19 Page 9).

## Auth
- JWT HS256, 24h expiry (`ACCESS_TOKEN_EXPIRE_HOURS`).
- `SECRET_KEY` from env. Never default to a hard-coded string in code that ships to production.
- Bcrypt via `passlib`. Never store plaintext or unsalted hashes.
- All non-auth routes require the `get_current_user` dependency.

## Error handling
- No Python stack traces in API responses (NFR-005). All endpoint errors return `{"detail": "..."}` only.
- Missing Graph config returns HTTP 503 with the exact body from FR-014 — never HTTP 500.
- DB connection failures on startup → log + exit 1 (do not run with a broken DB).

## Input
- All Excel parsers validate column presence before any DB write. Missing column → HTTP 422.
- Duplicate-period upload check happens **before** any insert (FR-005).
- Email recipient validated as RFC-5322 before send.

## CORS
- `CORS_ORIGINS` env var, comma-separated. Default `http://localhost:3000`. Do not use `*` in production.

## Dependencies
- Pin every dependency in `requirements.txt` and `package.json` to an exact version.
- Run `pip audit` / `npm audit` before each release; fix CRITICAL and HIGH findings.
