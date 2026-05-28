# ROI Calculator — Rendement Growth Model + 15-Year Projection (Execution)

## What needs to change
Update the ROI Calculator financial model so the rendement curve grows smoothly year by year instead of jumping from 10% to 25% to 65%, then switches after breakeven into a stable exploitation mode at 85% rendement. Extend the full projection horizon from 10 years to 15 years everywhere visible in the UI.

## Target
- Repo: `wechip-roi-calculator`
- Main file: `WECHIP_Configurateur_Client.html`
- Do not modify unrelated repos.

## Why this matters
The current growth scenario is too abrupt for customer-facing financial storytelling. The new model should show a realistic ramp-up, then a stable operating/exploitation phase once the investment has paid back.

## Context to load first
- [ ] `CLAUDE.md`
- [ ] `shared/knowledge/project-scope.md`
- [ ] `../WECHIP-OS/shared/knowledge/repo-architecture.md`
- [ ] `../WECHIP-OS/shared/procedures/planning-to-execution.md`
- [ ] `WECHIP_Configurateur_Client.html`

## Existing relevant code
Current constants are near the financial model block:

```javascript
const HORIZON      = 10;
const START_YEAR   = new Date().getFullYear();

const ROT_GROWTH = [0, 0.10, 0.25, 0.65, 0.75, 0.80, 0.85, 0.85, 0.85, 0.85, 0.85];
const ROT_STEADY = [0, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85];
```

Current compute logic uses `rot[y]` directly in both breakeven detection and final year rows.

## Implementation details

### 1. Extend projection horizon to 15 years
- Change `HORIZON` from `10` to `15`.
- Ensure all arrays/functions that depend on horizon support years 1 through 15.
- Do not leave visible UI text saying `10 ans` for the projection or return metric.
- Update visible labels:
  - `Projection 10 ans` → `Projection 15 ans`
  - SVG `aria-label="Projection 10 ans..."` → `Projection 15 ans...`
  - `Rendement à 10 ans` → `Rendement à 15 ans`
  - comments may be updated if helpful.
- Internal DOM IDs like `kpiProfit10` / `kpiNPV10` may remain if that keeps the patch smaller, but calculation variables should be renamed to generic names like `cumHorizon` / `npvHorizon` where practical.

### 2. Replace hardcoded jump curve with a smoothed annual growth curve
Replace the hardcoded `ROT_GROWTH` values with a generated smooth curve.

Desired behavior for growth scenario before exploitation:
- Year 1 starts at `10%`.
- Year 6 reaches `85%`.
- Years after the ramp cap at `85%`.
- Curve should be smoother than the old `10%, 25%, 65%, 75%, 80%, 85%` jumps.
- Use a simple deterministic smoothstep curve, not a dependency.

Suggested implementation:

```javascript
const REND_START = 0.10;
const REND_CAP = 0.85;
const REND_RAMP_YEARS = 6;

const smoothstep = t => t * t * (3 - 2 * t);

function buildSmoothGrowthRendement(){
  const values = [0];
  for (let y = 1; y <= HORIZON; y++) {
    const t = Math.min(1, Math.max(0, (y - 1) / (REND_RAMP_YEARS - 1)));
    values[y] = REND_START + (REND_CAP - REND_START) * smoothstep(t);
  }
  return values;
}

function buildSteadyRendement(){
  return Array.from({ length: HORIZON + 1 }, (_, i) => i === 0 ? 0 : REND_CAP);
}

const ROT_GROWTH = buildSmoothGrowthRendement();
const ROT_STEADY = buildSteadyRendement();
```

Expected approximate growth scenario values with this formula:
- A1: 10%
- A2: 17.8%
- A3: 36.4%
- A4: 58.6%
- A5: 77.2%
- A6+: 85%

These exact values are acceptable; avoid reintroducing the old jump array.

### 3. Add post-breakeven exploitation rendement rule
Once nominal breakeven has occurred, all subsequent years should be treated as exploitation mode with stable rendement at `85%`.

Important details:
- Breakeven year itself remains marked `Breakeven`.
- Years after breakeven (`y > beNominal`) use `REND_CAP` for revenue calculations.
- Years before or equal to breakeven use the base scenario rendement.
- For the `steady` scenario this changes little because it is already 85% from year 1.
- Store the effective rendement in the yearly row object as `rot` so the table/chart reflect the post-breakeven exploitation value.
- If useful, store `baseRot` too, but do not show it unless needed.

Suggested shape in `compute(p)`:

```javascript
const baseRot = getRotation();
// first pass: use baseRot[y] to find nominal breakeven
// second pass:
const post = beNominal > 0 && y > beNominal;
const effectiveRot = post ? REND_CAP : baseRot[y];
const revGross = p.cols * p.revPerColDay * effectiveRot * DAYS;
// push { ..., rot: effectiveRot, post, isBE: y === beNominal }
```

Do not let array length issues produce `undefined` rendement after year 10.

### 4. Rename post-breakeven status from Partage to Exploitation
In the year-by-year table status row:
- Keep `Breakeven` for the breakeven year.
- Change post-breakeven label from `Partage` to `Exploitation`.
- Keep pre-breakeven label as `Frais fixes` unless a better local label already exists.

### 5. Update scenario description
Update the growth scenario description from:

```html
Montée progressive du taux de rotation sur 5 ans
```

to something like:

```html
Montée progressive du rendement, puis exploitation stable à 85 % après breakeven
```

Also update any JS that rewrites `scenarioDesc` on scenario toggle, if present, so the description stays consistent after switching scenarios.

### 6. Preserve existing first prompt changes
The previous execution already changed visible labels from exploitation to rendement in selected spots. Keep these unless they directly conflict:
- `Taux de rendement (% capacité)`
- `Rendement (%)`
- explanatory note under rendement
- chart legend labels mentioning rendement/OPEX

## Out of scope
- Do not deploy to Azure.
- Do not commit unless explicitly asked.
- Do not redesign the UI.
- Do not change pricing, OPEX, replacement year, WECHIP share, days/year, or discount rate unless necessary for this task.
- Do not modify `wechip-tokens.css` unless a visual break requires a tiny fix.

## Acceptance criteria
- [ ] Projection horizon is 15 years everywhere visible in the UI.
- [ ] Table has columns A1 through A15.
- [ ] Graph displays 15 years without broken spacing, missing labels, or JS errors.
- [ ] Growth scenario no longer uses the old hardcoded jump array.
- [ ] Growth scenario rendement follows a smooth annual curve from 10% in A1 to 85% in A6.
- [ ] After nominal breakeven, subsequent years use 85% rendement and table status shows `Exploitation`.
- [ ] The breakeven year still shows `Breakeven`.
- [ ] Steady/exploitation scenario remains stable at 85% across the full 15 years.
- [ ] No visible `10 ans` text remains unless intentionally part of historical copy, which should not be the case here.
- [ ] Calculator still renders and computes with default inputs.

## Validation
There is no automated test suite for this static calculator. Use manual/local validation:

1. Start the app locally from repo root:
   ```bash
   .venv/bin/flask --app app run --port 5051
   ```
2. Open `http://127.0.0.1:5051/`.
3. Verify default render has no console errors.
4. Confirm the projection header and hero metric say 15 years.
5. Confirm the table contains A1 through A15.
6. Confirm the rendement row starts around 10%, ramps smoothly, reaches 85% by A6, and remains 85% after exploitation/breakeven.
7. Change inputs enough to move breakeven earlier/later and verify years after breakeven show `Exploitation` and 85% rendement.
8. Confirm local endpoint returns HTTP 200.

Before committing, run the full test suite (`python -m pytest tests/ -x -q` or equivalent) and fix all failures. If no tests exist, explicitly state that no test suite exists and document the local verification performed. Never commit with failing tests.

## Output format
Implement the changes in `WECHIP_Configurateur_Client.html`, verify locally, and report:
- changed files
- key behavior changes
- validation performed
- any uncommitted unrelated files found and left untouched
