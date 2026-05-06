# WECHIP ROI Calculator — Pre-Delivery Audit

**Scope:** `WECHIP_Configurateur_Client.html`, `app.py`, `wechip-tokens.css`, `requirements.txt`
**Date:** 2026-05-05
**Method:** Static code inspection of files at HEAD. No live browser test or POC executed in this audit (those are flagged where required and listed under *Outstanding validation*).
**Target endpoint:** https://wechip-roi-calculator.azurewebsites.net/

---

## Executive Summary

The financial model is **structurally sound and arithmetically defensive**: inputs are clamped, `fmt()` rejects `NaN`/`Infinity`, division-by-zero is guarded, and no user-controlled string ever reaches `.innerHTML`. However, the Flask wrapper has **one HIGH-severity issue** that must be fixed before client delivery: the catch-all static route exposes the entire repo, including `app.py`, `CLAUDE.md`, `shared/knowledge/project-scope.md`, and any other repo file. Two MEDIUM items (unpinned dependencies, missing security headers) and one financial-modelling question (post-breakeven yield jump) also warrant attention.

**Recommendation:** Do **not** share with client until the HIGH finding is fixed and the post-breakeven rendement question is confirmed with the business owner.

---

## Findings by severity

### 🔴 HIGH

#### H-1 — Public catch-all route exposes entire repo (path-disclosure / source leak)

**File:** [app.py](../app.py#L13-L15)

```python
@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(BASE, filename)
```

`BASE` is the repo root, so any file under it is downloadable:

- `GET /app.py` → server source
- `GET /requirements.txt` → dependency list
- `GET /CLAUDE.md`, `/README.md` → internal docs
- `GET /shared/knowledge/project-scope.md` → internal scope doc
- `GET /docs/PROMPT-rendement-refactor.md` → internal prompts
- `GET /wechip_os_path.py` → path-resolution helper
- `GET /startup.sh` → deploy script

`send_from_directory` *does* block `..` traversal (Flask normalises and rejects), so `/etc/passwd`-style attacks fail — but every legitimate file in the repo is still publicly served. This leaks business assumptions, internal commentary, and the financial model's source far more aggressively than the HTML alone would.

**Severity rationale:** explicitly named in the prompt's threat model ("expose business logic to reverse engineering", "leak sensitive configuration values"). All constants the prompt flags as potentially sensitive (`WECHIP_SHARE = 0.60`, base prices `19000`/`22000`) are in the HTML anyway, but `CLAUDE.md` + `shared/` should not be public.

**Reproduction:**
```bash
curl -sI https://wechip-roi-calculator.azurewebsites.net/app.py
curl -s  https://wechip-roi-calculator.azurewebsites.net/CLAUDE.md | head
```

**Recommended fix:** explicit allowlist.

```python
from flask import Flask, send_from_directory, abort
import os

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))

ALLOWED_FILES = {"WECHIP_Configurateur_Client.html", "wechip-tokens.css"}
ALLOWED_DIRS  = ("assets/", "fonts/")

@app.route("/")
def index():
    return send_from_directory(BASE, "WECHIP_Configurateur_Client.html")

@app.route("/<path:filename>")
def static_files(filename):
    if filename in ALLOWED_FILES or filename.startswith(ALLOWED_DIRS):
        return send_from_directory(BASE, filename)
    abort(404)
```

(Or move static assets under a dedicated `static/` directory and use Flask's built-in `/static` route.)

---

### 🟠 MEDIUM

#### M-1 — Post-breakeven rendement jumps to cap (business-logic confirmation needed)

**File:** [WECHIP_Configurateur_Client.html](../WECHIP_Configurateur_Client.html#L1004-L1006)

```js
const post = beNominal > 0 && y > beNominal;
const effectiveRot = post ? REND_CAP : baseRot[y];
const revGross = p.cols * p.revPerColDay * effectiveRot * DAYS;
```

If breakeven occurs *before* year 6 (e.g. very high CHF/col/day input), the very next year jumps from the ramp value (e.g. 0.60 in year 3) to `REND_CAP = 0.85`. This produces a discontinuous revenue step that the client may notice in the year-by-year table.

The acceptance criteria require: *"`revenueGross[year] = columns * revPerColDay * rendement[year] * 303`"* with `rendement` following the published ramp, capped at 0.85. The current code overrides the ramp post-breakeven. Two interpretations:

- **Intentional:** WECHIP optimisation kicks in once it takes a 60% share — assumed maturity.
- **Bug:** rendement should continue following the published ramp regardless of breakeven status.

**Action:** confirm with business owner. Document the chosen behaviour in the README and add an inline comment.

#### M-2 — `requirements.txt` unpinned (supply-chain / reproducibility)

**File:** [requirements.txt](../requirements.txt#L1-L2)

```
flask
gunicorn
```

Risks: a future Flask 4 / gunicorn 23 with breaking changes would land on next deploy. Also blocks CVE auditing (no version → no SBOM).

**Recommended fix:**
```
Flask==3.0.3
gunicorn==23.0.0
```
(Pin to current latest stable, refresh quarterly.)

#### M-3 — No security headers

**File:** [app.py](../app.py)

The Flask app sets no `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`/`frame-ancestors`, or `Referrer-Policy`. Because the calculator URL will be shared with prospects, basic hardening is appropriate.

The HTML uses inline `<style>` and a single inline `<script>`, so a strict CSP must include `'unsafe-inline'` for both — that's still a meaningful improvement over no CSP because it locks down external script sources.

**Recommended fix (after_request hook):**
```python
@app.after_request
def add_security_headers(resp):
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'"
    )
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return resp
```

---

### 🟡 LOW

#### L-1 — `gunicorn` started with no `--workers` / `--timeout`

**File:** [startup.sh](../startup.sh#L5)

```sh
exec gunicorn --bind=0.0.0.0:${PORT:-8000} app:app
```

Defaults to 1 worker + 30s timeout. For a static-asset-serving Flask app on Azure App Service Linux this is acceptable, but explicit values aid debuggability:

```sh
exec gunicorn --bind=0.0.0.0:${PORT:-8000} --workers=2 --timeout=60 app:app
```

#### L-2 — `pip install` runs on every cold start

**File:** [startup.sh](../startup.sh#L4)

`pip install … -r requirements.txt` on every startup adds latency and risks an outage if PyPI is unreachable. Azure App Service Oryx normally handles this at build time; calling pip again at runtime is redundant. Verify whether this is needed; if not, drop the line.

#### L-3 — `parseFloat` accepts trailing garbage

**File:** [WECHIP_Configurateur_Client.html](../WECHIP_Configurateur_Client.html#L971)

```js
let v = parseFloat(el.value);
```

`parseFloat("5abc")` → `5`. Because the inputs are `type="number"` (browser strips garbage) and the result is then range-clamped, this is functionally safe — but `Number()` would be stricter (and reject `"5abc"` → `NaN` → fallback). Cosmetic.

#### L-4 — Rounded `p.investTotal` displayed in KPI but raw value used in compute

**File:** [WECHIP_Configurateur_Client.html](../WECHIP_Configurateur_Client.html#L1042)

`kpiInvest` shows `Math.round(p.investTotal)`; `compute()` uses the unrounded `netTotal`. Sub-CHF differences are invisible at fmt(d=0) but it's a tiny inconsistency. Consider rounding once in `read()`.

#### L-5 — `revPerColDay` is a hidden input

**File:** [WECHIP_Configurateur_Client.html](../WECHIP_Configurateur_Client.html#L693)

```html
<input type="hidden" id="revPerColDay" value="5">
```

It's the only knob that meaningfully changes the breakeven year (along with discount and modules), but the user can't change it via UI — only via URL param `?rev=`. Confirm this is the intended UX (probably a sales-only knob).

---

### 🔵 INFORMATIONAL

#### I-1 — DOM-XSS audit: clean

All `.innerHTML` write sites were enumerated and traced:

| Line | Sink | Source | Verdict |
|------|------|--------|---------|
| ~1057 | `kpiInvest` | `fmt(Math.round(p.investTotal))` + literal | ✅ numeric only |
| ~1077 | `paybackDetail` | `m.beNominal` (computed int), literals | ✅ numeric only |
| ~1080 | `kpiProfit10` | `fmt(...)` + literal | ✅ |
| ~1186 | tooltip | `i+1`, `START_YEAR`, `fmt(Math.round(...))` | ✅ |
| ~1289 | `yearTable` | computed `m.years` numbers via `fmt()` | ✅ |
| ~1364 | `costBreakdown` | constants + `fmt()` numbers | ✅ |
| ~1467 | `rotationDetail` | constants + percentages | ✅ |

URL parameters (`mod`, `rev`, `rabais`, `modele`) are written to `input.value` (which doesn't HTML-parse) or compared against a strict allowlist (`'filaire' | 'solaire'`), then read back via `parseFloat` + `clampInput`. **No path from URL/user input to `innerHTML`.** XSS payloads in `?mod=<img src=x onerror=alert(1)>` are coerced to `NaN` and replaced by the fallback.

#### I-2 — Arithmetic safety: clean

- `fmt()` early-returns `'—'` for non-finite values ([line ~954](../WECHIP_Configurateur_Client.html#L954)).
- `Math.pow(1 + NPV_RATE, y)` ≥ 1 — no division by zero.
- ROI guarded: `p.investTotal > 0 ? pct(...) : '—'`.
- `pricingFromModules(0)` is unreachable because `clampInput('modulesInput', 2, 8, 2, 1)` forces `m ≥ 2`.

#### I-3 — `compute()` two-pass design is correct

First pass uses pure 100%-client economics to determine `beNominal`; second pass applies the 60% WECHIP share and stops OPEX/replacement only *after* `beNominal`. Year-1 OPEX is folded into `investTotal` and explicitly excluded from the year-1 OPEX line — verified no double-count.

#### I-4 — No persistence / tracking

No `localStorage`, `sessionStorage`, `cookie`, `fetch()`, or `XMLHttpRequest` in the HTML. Only `navigator.clipboard.writeText` + `document.execCommand('copy')` fallback for the Share button. Privacy-safe.

#### I-5 — `discount` clamped, but step quirk

`clampInput('discountPct', 0, 80, 0)` is called without `step` ([line ~975](../WECHIP_Configurateur_Client.html#L975)) so a URL like `?rabais=37.5` stays at 37.5 even though the input declares `step="5"`. Cosmetic; not a bug — clamping bounds work.

#### I-6 — Browser compatibility

Features used: `Intl.NumberFormat('fr-CH', …)`, `URLSearchParams`, `navigator.clipboard`, optional-catch (`catch {}`), template literals, arrow functions, `Map`. All are supported in Chrome 66+, Firefox 63+, Safari 11.1+, Edge 79+ — comfortably exceeds the prompt's targets (Chrome 90+ / Firefox 88+ / Safari 14+ / Edge 90+).

#### I-7 — Accessibility

Solid: `aria-pressed` on toggles, `aria-live="polite"` on hero, `scope="row"`/`scope="col"` on the table, `<button>` semantics for collapse toggles, `:focus-visible` outline, keyboard activation on phase cards (Enter/Space). No findings.

#### I-8 — `wechip-tokens.css`

Reviewed. Contains only design tokens (colours, radii, font stacks, motion). No secrets, no comments revealing strategy, no remote URLs.

---

## Risk assessment

| State | Overall risk |
|---|---|
| **Before fixes** | **HIGH** — repo source/internal docs publicly readable via H-1 |
| **After H-1 + M-2 + M-3** | **LOW** — calculator is safe, model is mathematically correct, only the M-1 business question remains |

---

## Prioritised fix list

1. **(blocker)** Fix **H-1** — allowlist static files in `app.py`.
2. **(blocker)** Confirm or fix **M-1** — post-breakeven rendement jump to `REND_CAP`. Document the decision.
3. Pin **M-2** — Flask + gunicorn versions in `requirements.txt`.
4. Add **M-3** — security headers (CSP / X-CTO / Referrer-Policy).
5. Polish **L-1 → L-5** — gunicorn flags, `pip install` at runtime, micro-rounding consistency, hidden-input UX confirmation.

---

## Outstanding validation (not done in this audit)

The following items in the prompt require **runtime evidence** that wasn't collected here. Run before the client-handoff gate:

- [ ] Live `curl` against `wechip-roi-calculator.azurewebsites.net/app.py` to confirm H-1 reproduces in production
- [ ] Manual scenarios A / B / C (4 modules @ 5 CHF; 2 modules @ 0.5 CHF + 80% rabais; 6 modules @ 3 CHF + 50% rabais) — capture KPI screenshots
- [ ] Browser test in Chrome / Firefox / Safari at 375px viewport
- [ ] DevTools throttling (mid-tier Android) — verify <100 ms re-render
- [ ] DevTools console: `document.getElementById('revPerColDay').value = 'NaN'; document.getElementById('revPerColDay').dispatchEvent(new Event('input'))` — verify `'—'` fallbacks render

---

## Client-handoff gate

Per the prompt this report **cannot yet** carry the explicit "safe and accurate for client presentation" sign-off because:

1. H-1 is unfixed at HEAD.
2. M-1 (post-breakeven rendement) needs a business decision before the model can be declared "accurate".
3. The runtime validation checklist above is unrun.

Once H-1 is patched, M-1 is decided, and the runtime checklist is green, this report can be re-issued with the sign-off.
