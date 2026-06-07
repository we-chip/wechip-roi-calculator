For this repo only.

## MANDATORY INITIALIZATION

Before answering any user question — on every new session or workspace load — you MUST:

1. Read `CLAUDE.md` (repo root)
2. Read `shared/knowledge/project-scope.md`

If either file is missing or unreadable, alert the user immediately and proceed in minimal safe mode (no architecture assumptions, no invented structure).

Only after completing this initialization step may you respond to user requests.

## Context Loading Order

After initialization, load additional context in this order when relevant:

1. Relevant knowledge from `../WECHIP-OS/shared/knowledge/` (umbrella repo - check first)
2. Relevant procedures from `../WECHIP-OS/shared/procedures/` (umbrella repo - check first)
3. Local overrides in `shared/procedures/` if they exist

## Planning Gate (mandatory for features)

If asked to draft an implementation prompt or scope a feature:
1. Load `../WECHIP-OS/shared/procedures/planning-to-execution.md` first
2. Stay in planning mode — no file edits in this chat
3. Output the final prompt inside a ```code box```
4. User opens a fresh execution chat with that prompt

## Execution Routing Gate (mandatory before building ANY feature, local mode)

This fires even when there is no planning phase — a direct "implement / build / apply /
add / wire up / refactor X", or applying a design handoff/spec:

1. Before writing code that touches >1 file or applies a design/handoff/spec, load
   `../WECHIP-OS/shared/procedures/local-vs-cloud-routing.md` and run its Rubric FIRST.
2. Default is cloud (Copilot) — `gh issue create … -a copilot`. Local is the exception
   (secrets, deploys, umbrella edits, exploration).
3. Doing feature-sized work inline in this chat because it's "just mechanical" is the
   anti-pattern the token-efficiency north star exists to kill.

## Rules

- keep answers short
- verify current repo state before claims
- do not invent architecture beyond this repo
- keep repo-specific knowledge here, not in WECHIP-OS
