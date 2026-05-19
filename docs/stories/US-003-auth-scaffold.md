# US-003 — JWT auth scaffold

**Epic:** Foundation

## Story
- **As an** HR admin
- **I want** to log in with email and password and receive a JWT
- **So that** all subsequent API calls and UI pages are authenticated against my single HR account.

## Acceptance criteria
- **Given** the default seeded HR user, **when** I `POST /api/v1/auth/login` with `{"email":"hr@shorthills.ai","password":"HR@ShortHills2024"}`, **then** I receive HTTP 200 with `{"access_token": "...", "token_type": "bearer"}` where the JWT is HS256-signed with `SECRET_KEY` and expires in 24h (FR-001).
- **Given** wrong credentials, **when** I post to `/auth/login`, **then** I receive HTTP 401 with `{"detail": "Invalid email or password"}` and `app_users.last_login` is **not** updated.
- **Given** a successful login, **when** the user record is updated, **then** `last_login` is set to the current timestamp.
- **Given** any non-auth endpoint, **when** I call it without `Authorization: Bearer <token>` or with an expired/invalid token, **then** I receive HTTP 401 (`get_current_user` dependency).
- **Given** a valid token, **when** I `GET /api/v1/auth/me`, **then** I receive the user's `email`, `full_name`, `role`, and `last_login`.
- **Given** the frontend, **when** the login form submits successfully, **then** the JWT is stored in `localStorage` as `access_token`, an Axios interceptor injects it on all subsequent requests, and a 401 response triggers redirect to `/login` + localStorage clear.

## Dependencies
- US-001
- US-002 (seeded HR user)

## Estimate
**M** — Standard JWT flow but covers backend dependency wiring, axios interceptor, and AuthContext on the React side.

## Linked FR-IDs
- FR-001 (JWT auth)

## Linked entities
- `app_users`

## Infrastructure dependencies
- `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_HOURS` env vars.
- `python-jose[cryptography]`, `passlib[bcrypt]`.
