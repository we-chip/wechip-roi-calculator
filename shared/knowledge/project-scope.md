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
