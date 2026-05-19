# Epics

Stories grouped into epics. Foundation must be completed before any feature epic begins. Within feature epics, dependencies are noted in the story files themselves.

> See also: [architecture.md](architecture.md) for runtime topology and per-request lifecycles. [ADR-001](decisions/ADR-001-no-alembic-and-no-local-db.md) records the no-Alembic / no-local-DB decision.

---

## Epic 1 — Foundation (must ship first)
Repo, DB, auth, and a smoke test that proves the foundation works end to end. No feature story may be started before this epic is complete.

| Story | Title | Estimate | FR | Notes |
|---|---|---|---|---|
| [US-001](stories/US-001-repo-tooling-scaffold.md) | Repo + tooling scaffold | M | — | Docker Compose, Dockerfiles, nginx, env wiring |
| [US-002](stories/US-002-db-schema-create-all.md) | DB schema via create_all + seed | L | FR-017 | 13 tables, idempotent seed |
| [US-003](stories/US-003-auth-scaffold.md) | JWT auth scaffold | M | FR-001 | HS256, bcrypt, AuthContext, axios interceptor |
| [US-004](stories/US-004-smoke-test.md) | End-to-end smoke test | S | — | Guard rail for the foundation |

---

## Epic 2 — Ingestion
Three Excel parsers, the Upload UI, and the duplicate-upload guard.

| Story | Title | Estimate | FR |
|---|---|---|---|
| [US-005](stories/US-005-greythr-parser-and-upload.md) | GreytHR parser + endpoint | M | FR-002 |
| [US-006](stories/US-006-biometric-parser-and-upload.md) | Biometric block parser + endpoint | L | FR-003 |
| [US-007](stories/US-007-roster-parser-and-upload.md) | Roster parser + silver_employees upsert | M | FR-004 |
| [US-008](stories/US-008-duplicate-upload-rejection.md) | Duplicate-period upload rejection | S | FR-005 |
| [US-022](stories/US-022-upload-page-ui.md) | Upload page UI (three cards + history) | M | FR-002/3/4/5 (UI side) |

---

## Epic 3 — Pipeline
Bronze → Silver → Gold transitions, the 9-flag engine, and the user-facing pipeline trigger.

| Story | Title | Estimate | FR |
|---|---|---|---|
| [US-009](stories/US-009-silver-leave-cross-reference.md) | Silver: leave cross-reference + permanent-WFH skip | L | FR-006, FR-007 |
| [US-010](stories/US-010-gold-period-stats.md) | Gold: gold_period_stats aggregation | L | FR-008 |
| [US-011](stories/US-011-flag-engine.md) | Gold: 9-flag evaluation engine | XL | FR-009 |
| [US-012](stories/US-012-pipeline-trigger-endpoint.md) | Pipeline trigger endpoint + UI button | M | FR-018 |

---

## Epic 4 — Analytics UI
Dashboard overview plus the attendance and leave analysis pages.

| Story | Title | Estimate | FR |
|---|---|---|---|
| [US-013](stories/US-013-dashboard-overview.md) | Dashboard overview (cards + 3 charts) | M | FR-010 |
| [US-014](stories/US-014-attendance-page-and-heatmap.md) | Attendance page + calendar heatmap | M | FR-011 |
| [US-023](stories/US-023-leave-analysis-page.md) | Leave analysis page | S | — (supports FR-008/11) |

---

## Epic 5 — Compliance UI
Flags page with filter, resolve, and bulk-select.

| Story | Title | Estimate | FR |
|---|---|---|---|
| [US-015](stories/US-015-flags-page.md) | Flagged employees page | M | FR-012 |

---

## Epic 6 — Email
Send flow, graceful degradation, template CRUD, audit log.

| Story | Title | Estimate | FR |
|---|---|---|---|
| [US-018](stories/US-018-email-template-crud.md) | Template CRUD with soft-delete | M | FR-015 |
| [US-017](stories/US-017-email-graceful-degradation.md) | Graceful 503 + config-status banner | S | FR-014 |
| [US-016](stories/US-016-email-send-flow.md) | Send flow + preview + Graph API | L | FR-013 |
| [US-020](stories/US-020-email-history.md) | Email history audit view | S | FR-019 |

---

## Epic 7 — Settings + Employee Directory

| Story | Title | Estimate | FR |
|---|---|---|---|
| [US-019](stories/US-019-threshold-settings.md) | Editable flag thresholds | S | FR-016 |
| [US-021](stories/US-021-employee-directory-inline-email-edit.md) | Employee directory + inline email edit | M | FR-020 |

---

## Recommended vertical slice (first pull)

Goal: prove end-to-end value with the smallest viable set of stories before broadening to all features.

```
Foundation:    US-001 → US-002 → US-003 → US-004
Then slice:    US-005 + US-006 + US-007 + US-022   (upload all three files)
            →  US-008                              (duplicate guard, so re-runs are safe)
            →  US-009 → US-010 → US-011 → US-012   (pipeline + flags)
            →  US-013                              (one visible analytics surface)
            →  US-018 → US-017 → US-016 → US-020   (email path with graceful degradation first)
Tail:          US-014, US-015, US-019, US-021, US-023   (parallelizable after slice lands)
```

This sequence ships a usable monthly workflow (upload → pipeline → dashboard → send + history) before the polish surfaces (heatmap, leave analysis, inline email edit, threshold tuning) are tackled.

---

## FR coverage matrix (sanity check)

| FR | Story |
|---|---|
| FR-001 | US-003 |
| FR-002 | US-005 |
| FR-003 | US-006 |
| FR-004 | US-007 |
| FR-005 | US-008 |
| FR-006 | US-009 |
| FR-007 | US-009 (+ reinforced in US-011) |
| FR-008 | US-010 |
| FR-009 | US-011 |
| FR-010 | US-013 |
| FR-011 | US-014 |
| FR-012 | US-015 |
| FR-013 | US-016 |
| FR-014 | US-017 |
| FR-015 | US-018 |
| FR-016 | US-019 |
| FR-017 | US-002 |
| FR-018 | US-012 |
| FR-019 | US-020 |
| FR-020 | US-021 |

Every FR is owned by exactly one story (FR-007 reinforced in US-011 for the flag-engine path).
