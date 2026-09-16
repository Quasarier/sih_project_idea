# sih_project_idea

Prototype for SIH 2026 Problem Statement.

# Coastal Watch

Oil-spill detection and vessel-attribution prototype for the Indian west coast.

## Run the vanilla frontend

From this directory:

```powershell
python -m http.server 4173
```

Open `http://localhost:4173/`. The root page redirects to `frontend/index.html`.

## Run the React build

Install Node.js 20 or newer, then run:

```powershell
cd frontend-react
npm install
npm run dev
```

## Repository layout

- `frontend/` - analyst dashboard and browser interactions
- `frontend-react/` - React/Vite version of the analyst dashboard
- `backend/` - API and orchestration services
- `ml/` - satellite segmentation and vessel-ranking models
- `data/` - INCOIS, ERA5, Sentinel-1, AIS connectors and schemas
- `simulation/` - backward hindcast and forward spill forecast workflows
- `docs/` - architecture and integration notes

The current demo AIS input is stored at `data/raw/ais_synthetic.csv`. It is intentionally generated data for development and demonstrations, not a record of real vessel activity.

## Run model tests

```powershell
python -m unittest discover -s tests -v
```

The suite contains three tests each for slick segmentation, drift reconstruction/forecast, and AIS vessel attribution.
