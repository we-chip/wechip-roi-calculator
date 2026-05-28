# ROI Calculator — Rendement UI Refactor (Execution)

## Context
Update the ROI Calculator configurator to rename "Taux d'exploitation" to "Taux de rendement" throughout the UI, with supporting legend and note updates to clarify the relationship to rotation rates.

**Target file:** `/Users/thomas/Documents/GitHub/wechip-roi-calculator/WECHIP_Configurateur_Client.html`

**Delivered assets constraint:** Do NOT modify the core HTML/CSS business logic in `WECHIP_Configurateur_Client.html` beyond the specific label and legend changes listed below.

---

## Scope of Changes

### 1. Panel label (line ~737)
**OLD:**
```html
<div class="section-label">Taux d'exploitation (% capacité)</div>
```

**NEW:**
```html
<div class="section-label">Taux de rendement (% capacité)</div>
<div class="note" style="margin-top:10px;font-size:12px;color:var(--wc-fg-2)">Le taux de rendement est lié au taux de rotation journalier des casiers, au regroupage de colis et aux usages alternatifs.</div>
```

### 2. Table row label (line ~1130)
**OLD:**
```javascript
rowNoTotal('Exploitation (%)', y=>y.rot*100)+
```

**NEW:**
```javascript
rowNoTotal('Rendement (%)', y=>y.rot*100)+
```

### 3. Chart legend (line ~752)
**OLD:**
```html
<div class="chart-legend" aria-label="Légende du graphique">
  <span><i style="background:var(--wc-ink-1000)"></i> Flux cumulé</span>
  <span><i style="background:var(--wc-success)"></i> Revenus</span>
  <span><i style="background:var(--wc-error)"></i> Coûts</span>
  <span><i class="dash" aria-hidden="true"></i> Breakeven</span>
</div>
```

**NEW:**
```html
<div class="chart-legend" aria-label="Légende du graphique">
  <span><i style="background:var(--wc-ink-1000)"></i> Flux cumulé</span>
  <span><i style="background:var(--wc-success)"></i> Revenus (taux de rendement croissant)</span>
  <span><i style="background:var(--wc-error)"></i> Coûts (incluant OPEX)</span>
  <span><i class="dash" aria-hidden="true"></i> Breakeven</span>
</div>
```

---

## Growth Curve
**Decision:** Keep current S-curve unchanged.
```javascript
const ROT_GROWTH = [0, 0.10, 0.25, 0.65, 0.75, 0.80, 0.85, 0.85, 0.85, 0.85, 0.85];
```
No changes to this array.

---

## Quality Gates

### Pre-commit check
- Verify all three label changes are applied correctly in `WECHIP_Configurateur_Client.html`.
- Check that the explanatory note renders without CSS issues in the browser.
- Ensure no JavaScript logic is altered—only strings and UI labels.

### Localhost verification
After changes:
1. Start the app locally: `python3 app.py` (or `flask run`)
2. Open http://localhost:5000 in a browser
3. Verify:
   - Panel label now shows "Taux de rendement" with the explanatory note below it
   - Table row header shows "Rendement (%)"
   - Chart legend shows updated text for Revenus and Coûts
   - Calculator still computes correctly (test with default inputs)
   - No console errors

### Deployment readiness
Once localhost verification passes:
- Stage and commit changes to `main` branch
- Follow `../WECHIP-OS/shared/procedures/azure-deploy-pattern.md` before any Azure deploy

---

## Files to Modify
- `WECHIP_Configurateur_Client.html` (3 changes, lines ~737, ~752, ~1130)

## No Test Suite Required
This repo is a static calculator with no automated tests; localhost verification is the quality gate.

---

## Success Criteria
✓ All three label replacements applied without syntax errors
✓ Explanatory note displays correctly in UI
✓ Calculator functionality unchanged
✓ Localhost verification passes
