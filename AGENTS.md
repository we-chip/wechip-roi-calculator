# AGENTS.md

Local agent front door. `CLAUDE.md` is its peer. WECHIP-OS shared policy outranks both.

Before reading code or scoping:
```bash
git -C . fetch -q && git -C . status -sb | head -1
git -C ../WECHIP-OS fetch -q && git -C ../WECHIP-OS status -sb | head -1
```
Follow `../WECHIP-OS/shared/procedures/session-start.md`. After its freshness/update decision,
read `shared/knowledge/project-scope.md`.

Keep this routing-only; project facts stay local and general workflow policy stays in WECHIP-OS.
