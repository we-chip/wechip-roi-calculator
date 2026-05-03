# wechip-roi-calculator

WECHIP ROI configurator — interactive calculator for customers.

## Stack
- Static HTML/CSS/JS (`WECHIP_Configurateur_Client.html`, `wechip-tokens.css`)
- Thin Flask wrapper (`app.py`) with gunicorn
- Azure App Service (wechip-plan B1, West Europe)

## Local dev
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Deployment
Push to `main` → GitHub Actions OIDC deploy to Azure App Service.
