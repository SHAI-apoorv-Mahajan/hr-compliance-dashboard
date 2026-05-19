---
name: new-feature
description: Use when the user says "I want to add …", "let's build a new feature for …", "can we ship …", or any phrasing that proposes new product scope not already in docs/PRD.md. Drives the requirements → story → plan handoff before any code is written.
---

# new-feature

## When to invoke
Any time the user proposes a capability not already covered by `docs/PRD.md` FR-001…FR-020.

## Steps
1. **Check the PRD first.** Read `docs/PRD.md` and search for the feature. If it already exists, redirect the user to the existing FR / story instead.
2. **Clarify scope.** Use `AskUserQuestion` to confirm: what is the user-visible outcome, what's explicitly out of scope, what existing entity does it touch.
3. **Dispatch to product-manager.** Have product-manager draft the new FR-NNN amendment to `docs/PRD.md` and a new `docs/stories/US-NNN-*.md`.
4. **Dispatch to data-modeler** if a new entity or column is needed. Update `docs/data-model.md` and the PRD §15 ERD before code.
5. **Dispatch to tech-lead** to sequence implementation across backend / frontend / qa / devops.
6. **Pause for user approval** of the new FR and story before any code is written.

## Hard rules
- Never write product code in this skill. The output is documentation only.
- Never amend an existing FR's text without an explicit "yes, change FR-NNN" from the user — propose the change, wait for approval.
