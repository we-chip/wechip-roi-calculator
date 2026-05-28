# wechip-roi-calculator

WECHIP ROI configurator — interactive calculator for customers.

## Stack
- Static HTML/CSS/JS (`WECHIP_Configurateur_Client.html`, `wechip-tokens.css`)
- Thin Flask wrapper (`app.py`) with gunicorn
- SQLite (`db.py`) for per-lead trackable links + events
- Azure App Service (wechip-plan B1, West Europe)

## Local dev
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt   # for pytest
export BASIC_AUTH_USER=admin BASIC_AUTH_PASS=changeme
python app.py
```

Open http://127.0.0.1:5051/ for the calculator, http://127.0.0.1:5051/admin/links for the admin.

## Tests
```bash
python -m pytest tests/ -x -q
```

## Per-lead trackable links

Admins create a slug under `/admin/links/new` with pre-set economic assumptions.
Customers visit `/c/<slug>` and see the calculator with those values applied
(and `revPerColDay` locked). Every view, customer change, and print is logged.

### Environment variables

| Var | Purpose | Default |
|-----|---------|---------|
| `BASIC_AUTH_USER` | HTTP Basic auth username for `/admin/*` | (unset → 503) |
| `BASIC_AUTH_PASS` | HTTP Basic auth password for `/admin/*` | (unset → 503) |
| `LINKS_DB_PATH`   | SQLite DB path for links + events | `./roi_links.db` |
| `FLASK_SECRET_KEY`| Flask session key (CSRF) | random per process |
| `PORT`            | Local dev port | `5051` |

### Admin URL
`/admin/links` (Basic auth).

### Azure persistence
**Important:** on Azure App Service, set `LINKS_DB_PATH=/home/data/roi_links.db`
so the SQLite file lives on the persisted `/home` volume and survives redeploys.
Also set `FLASK_SECRET_KEY` and `BASIC_AUTH_USER` / `BASIC_AUTH_PASS` as app
settings.

## Deployment
Push to `main` → GitHub Actions OIDC deploy to Azure App Service.
