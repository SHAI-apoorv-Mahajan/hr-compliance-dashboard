---
name: release
description: Use when the user wants to cut a release of the HR Compliance Dashboard. Takes major / minor / patch as $ARGUMENTS. NEVER auto-invoked.
disable-model-invocation: true
---

# release

`$ARGUMENTS` — `major` | `minor` | `patch`.

## Steps
1. **Confirm clean state.** `git status` must be clean. Working tree dirty → stop.
2. **Tests green.** Run `pytest -q` and `npm test`. Either failing → stop.
3. **Bump version.** Update version strings in `backend/main.py` (if present) and `frontend/package.json` per `$ARGUMENTS`.
4. **Update CHANGELOG.md.** One section per release with: date, version, list of stories closed since the last release.
5. **Commit + tag.** `git commit -m "chore(release): v<x.y.z>"` then `git tag v<x.y.z>`.
6. **Build images.** `docker compose build` to confirm both images build cleanly with the new version.
7. **Surface next steps** to the user — pushing the tag, deploying, etc. Do **not** push automatically.

## Hard rules
- Never run during a refactor or mid-feature. Cut from green main only.
- Never bump major without the user explicitly saying "major" — semver is intentional, not implied.
- Never push tags automatically. The user pushes; you prepare.
