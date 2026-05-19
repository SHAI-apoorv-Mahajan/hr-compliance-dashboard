---
name: implement-story
description: Use when the user wants to implement a specific user story by ID — e.g., "implement US-005", "build out US-011", "ship US-016". Takes the story ID as $ARGUMENTS and orchestrates the tech-lead + specialist agents to deliver it.
---

# implement-story

`$ARGUMENTS` — the story ID, e.g. `US-005`.

## Steps
1. **Read the story.** Open `docs/stories/$ARGUMENTS-*.md`. If multiple match, ask the user to disambiguate.
2. **Check dependencies.** Every story dependency listed must already be done (tests green for those stories). If a dependency is missing, surface it and stop.
3. **Read affected layer CLAUDE.md.** Based on linked entities + acceptance criteria, read the relevant `src/api/`, `src/persistence/`, `src/services/`, `src/ui/` CLAUDE.md files.
4. **Dispatch to tech-lead** with: the story file, the acceptance criteria, and any flagged PRD §27 quirks relevant to this story.
5. **Loop until acceptance criteria are green.** After each engineer change, run `pytest -q` (backend) and/or `npm test` (frontend). Do not declare done with red tests.
6. **Hand to code-reviewer** for a final pass.
7. **Hand to security-reviewer** if the story touches: auth (FR-001), file upload (FR-002/3/4/5), email send (FR-013/14), or env handling.
8. **Update story file** with a Done section: links to commits / files changed, test output excerpt, reviewer approvals.

## Hard rules
- Do not skip dependency checks even if it "feels safe".
- Never modify the acceptance criteria to make a test pass. If a criterion turns out to be wrong, surface it to product-manager — do not silently change it.
- Foundation stories (US-001…US-004) must be complete before any other story starts.
