# AGENTS.md

Local agent front door. `CLAUDE.md` is its peer; project scope and umbrella `shared/` sources outrank both.

Before reading code, scoping, or saying what exists, check freshness:
```bash
git -C . fetch -q && git -C . status -sb | head -1
git -C ../WECHIP-OS fetch -q && git -C ../WECHIP-OS status -sb | head -1
```
Report stale branches and ask before pulling. Why: `../WECHIP-OS/shared/procedures/session-start.md`.

Then read `shared/knowledge/project-scope.md`, and nothing else until the task needs it.

On demand, use `../WECHIP-OS/shared/knowledge/` and `../WECHIP-OS/shared/procedures/`, including `execution-routing.md`, `current-toolset.md`, `working-with-thomas.md`, and `external-constraints.md`. Local procedure overrides apply only when explicitly documented with a reason.

Rules: keep this thin; duplicate no shared knowledge; treat this repo as authoritative for its code; create no `.claude/skills`; treat historical claims as unverified until confirmed.
