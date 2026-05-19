---
name: post-mortem
description: Use after a production incident or significant failure to write a structured post-mortem. Trigger phrases: "write a post-mortem", "incident review", "what went wrong with …", "RCA for …".
---

# post-mortem

## Steps
1. **Gather the timeline.** Ask the user for: when the incident started, how it was detected, when it was resolved, what action restored service.
2. **Identify the root cause.** Not the symptom — the underlying defect, missing guard, or process gap. Use the 5 whys.
3. **Write the post-mortem** to `docs/post-mortems/YYYY-MM-DD-short-slug.md` with sections:
   - **Summary** — one paragraph: what broke, who was affected, how long.
   - **Timeline** — events in UTC.
   - **Root cause** — the underlying defect.
   - **Detection & response** — how we found out, how we responded.
   - **Impact** — users affected, data lost, financial cost.
   - **What went well** — at least two items.
   - **What went poorly** — at least two items.
   - **Action items** — concrete, assigned, dated. Each linked to a story or ADR if non-trivial.
4. **Surface action items to product-manager** to create stories.

## Hard rules
- Blameless tone. No names attached to mistakes. "We deployed an untested migration" not "Alice deployed an untested migration."
- Every action item must be concrete and trackable. "Be more careful" is not an action item.
- Never publish a post-mortem with open root-cause questions — say "investigating" explicitly.
