---
name: refactor
description: Use when the user wants to refactor existing code without changing behavior — extracting a helper, renaming, splitting a module, simplifying. Trigger phrases: "refactor …", "clean up …", "extract …", "simplify …", "split this module".
effort: xhigh
---

# refactor

## Steps
1. **Capture the baseline.** Run the full test suite and confirm it's green. If anything is red, fix that first — never refactor on a red baseline.
2. **Identify the smallest safe step.** A refactor is one change at a time: rename, extract, inline, split.
3. **Make the change.** No behavior change, no new features, no fixes-in-passing.
4. **Re-run tests.** Must be green again — same set, same outcomes. If a test name changed, prove it covers the same behavior.
5. **Repeat** from step 2 until the agreed scope is done.

## Hard rules
- Never combine a refactor with a feature or fix. They go in separate commits, separate PRs if possible.
- Never delete tests "because they're hard to keep working" — fix them, or the refactor is wrong.
- Public APIs (routers, exported components, models) are versioned changes. Renaming a router path is a breaking change, not a refactor.
- If a refactor exposes a bug, stop. Open a separate story for the bug; do not fix it in this commit.
