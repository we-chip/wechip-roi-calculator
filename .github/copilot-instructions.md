## Local mode

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

## Cloud agent (self-contained)

This section is for the GitHub Copilot coding agent running on an ephemeral
cloud VM. That VM has ONLY this repo: no `../WECHIP-OS/` umbrella, no
`~/.wechip/` credentials, no Azure CLI, no `.env`, no secrets, no production
database. Ignore every instruction in "Local mode" above that points outside
this repo — none of those paths exist on the cloud VM.

- Stack: Flask 3 + gunicorn, Python 3.11, pytest. SQLite for storage; tests
  use a temp DB via the `create_app(db_path=...)` factory and `tmp_path`.
- Setup: `pip install -r requirements.txt -r requirements-dev.txt`
  (already run by `.github/workflows/copilot-setup-steps.yml`).
- Tests: `python -m pytest tests/ -x -q`. Must be green before you open the PR.
  `tests/conftest.py` injects auth env via `monkeypatch` and a temp DB path, so
  the suite runs offline with no real secrets.
- DO NOT touch: `roi_links.db`, `roi_links.local.db`, and any `*.db` / `*.db.*`
  data files; `.env` or any secret material; auth/session secret or key material;
  `.github/workflows/deploy.yml`; `startup.sh`; and anything that needs live
  credentials or network services.
- DO NOT add new top-level dependencies without justifying them in the PR body.
- Keep changes scoped to the issue. No drive-by refactors. Match the existing
  style of the files you touch (imports, naming, route patterns).
- If the issue is ambiguous or needs a design decision not spelled out in the
  prompt: STOP, open the PR as draft, and comment on the PR instead of guessing.
