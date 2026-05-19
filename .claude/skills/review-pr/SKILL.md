---
name: review-pr
description: Use before merging — runs a multi-agent review of the current diff (code-reviewer + security-reviewer in parallel). Trigger phrases: "review this PR", "review the diff", "is this ready to merge", "pre-merge check".
---

# review-pr

## Steps
1. **Capture the diff.** `git diff main...HEAD` (or staged changes) — agents will read it directly.
2. **Identify the story.** Read the most recent commit message for a US-NNN reference, or ask the user.
3. **Dispatch in parallel:**
   - **code-reviewer** for style, story-AC coverage, idempotency, error-handling shape.
   - **security-reviewer** for the auth / upload / email / env-handling checklist.
4. **Run the test suite.** `pytest -q` for backend, `npm test` for frontend. Attach output to the review summary.
5. **Aggregate.** Single review summary: ✅ Approved / ⚠️ With comments / ❌ Changes requested, with comments grouped by reviewer.

## Hard rules
- Always run both reviewers — never just one.
- Tests must pass before approval. No "approved, just fix the test next".
- If security-reviewer reports any Critical or High, the aggregate result is ❌ regardless of code-reviewer's verdict.
