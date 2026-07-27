# ROI Calculator Project Scope

## Project Role

ROI Calculator is an interactive customer-facing configurator within the WECHIP product ecosystem. It provides:
- ROI calculation for WECHIP locker solutions
- Interactive configuration options
- Visual output for customer presentations

## Authority Boundary

ROI Calculator owns:
- Static HTML/CSS/JS calculator files
- Flask serving wrapper
- Deployment configuration (Azure App Service)

ROI Calculator defers to WECHIP-OS for:
- Shared architecture rules
- Cross-project procedures (planning, execution, smoke tests)
- Sub-project structure

## Key Live Check

https://wechip-roi-calculator.azurewebsites.net/ returns 200 and renders the calculator page.

## Main Caveat

The HTML/CSS/JS files (`WECHIP_Configurateur_Client.html`, `wechip-tokens.css`) are delivered assets — do not modify their content without explicit approval.

## Do not touch

- `roi_links.db`, `roi_links.local.db`, and any `*.db` / `*.db.*` data file
- `.env` or any secret material; auth/session secret or key material
- `.github/workflows/deploy.yml`, `startup.sh`
- anything that needs live credentials or network services
- `WECHIP_Configurateur_Client.html` and `wechip-tokens.css` are delivered assets — do not
  modify their content without explicit approval

## Tests

`python -m pytest tests/ -x -q`, green before opening a PR. `tests/conftest.py` injects auth env
via `monkeypatch` and a temp DB path, so the suite runs offline with no real secrets.
Do not add new top-level dependencies without justifying them in the PR body.
