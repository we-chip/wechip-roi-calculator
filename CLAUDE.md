# CLAUDE.md

Surface routing:
- If you are WECHIP Prompting Agent in this repo, your role is planning and prompt engineering. Read `cowork/instructions.md` before any shared docs.
- If you are Claude Code in this repo, your role is review, debugging, maintenance, and quality.

Canonical sources:
- project scope: `shared/knowledge/project-scope.md`
- shared knowledge: `../WECHIP-OS/shared/knowledge/`
- shared procedures: `../WECHIP-OS/shared/procedures/`

Read first for Claude Code:
1. `shared/knowledge/project-scope.md`
2. `../WECHIP-OS/shared/knowledge/repo-architecture.md`

Also use when relevant:
1. `../WECHIP-OS/shared/procedures/planning-to-execution.md`
2. `../WECHIP-OS/shared/procedures/smoke-tests.md`

## Planning gate (feature work)

For any prompt drafting or feature scoping, follow `../WECHIP-OS/shared/procedures/planning-to-execution.md`:
- planning chat: no file edits, draft prompt inside a ```code box``` only
- execution: open a fresh chat with that prompt

## Execution routing gate (before building any feature)

Even with no planning phase — a direct "implement/apply/build X" or a design handoff —
run `../WECHIP-OS/shared/procedures/local-vs-cloud-routing.md` BEFORE touching code if the
change spans >1 file or applies a design/spec. Default is cloud (Copilot); local is the
exception. Mechanical ≠ "do it in chat".

Rules:
- keep this file thin
- do not duplicate shared knowledge here
- do not invent extra framework structure
- do not create `.claude/skills`
- treat historical setup claims as unverified unless confirmed from current repo files
