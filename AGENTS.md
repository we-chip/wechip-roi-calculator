# AGENTS.md

Front door for Codex CLI here. `CLAUDE.md` is the other tool's and says the same; `shared/` outranks both.

Your role: review, debugging, maintenance, quality.

Before reading code, scoping, or saying what exists, check freshness — the local tree is not the
shipped state. Run it for this repo and for the umbrella:

```bash
git -C . fetch -q && git -C . status -sb | head -1
git -C ../WECHIP-OS fetch -q && git -C ../WECHIP-OS status -sb | head -1
```

Report both in plain language and ask before pulling. Why, and what to do when behind:
`../WECHIP-OS/shared/procedures/session-start.md`.

Then read `shared/knowledge/project-scope.md`, and nothing else until the task needs it.

On demand: `../WECHIP-OS/shared/knowledge/` and `../WECHIP-OS/shared/procedures/` are canonical —
including `execution-routing.md` (the gate before any feature-sized change),
`current-toolset.md` (which tools exist, one agent per project at a time),
`working-with-thomas.md` (how to explain and report), `external-constraints.md` (never touch).

Rules: keep this thin — routing only, no knowledge, no duplication; this repo is authoritative for
its own code and facts; invent no extra framework structure; no `.claude/skills`; treat historical
setup claims as unverified until confirmed from current repo files.
