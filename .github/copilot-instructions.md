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

## Rules

- keep answers short
- verify current repo state before claims
- do not invent architecture beyond this repo
- keep repo-specific knowledge here, not in WECHIP-OS
