# sih_project_idea

Prototype for SIH 2026 Problem Statement.

# Coastal Watch

Oil-spill detection and vessel-attribution prototype for the Indian west coast.

## Overview

This repository contains a lightweight, demo-oriented prototype for identifying probable vessel sources from synthetic AIS and oil-spill inputs. The frontend presents a dashboard, while the backend API runs scoring logic from the ML modules and returns ranked vessel candidates.

## Local deployment

### 1) Install Python dependencies

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r ml/requirements.txt
```

### 2) Start the local API backend

Run the backend before opening the dashboard. Choose either the Docker deployment or the direct Python deployment.

#### Docker deployment (recommended)

From the project root:

```powershell
docker build -t coastal-watch-api .
docker run --rm --name coastal-watch-api -p 8001:8001 coastal-watch-api
```

#### Direct Python deployment

With the virtual environment activated:

```powershell
python backend\api\server.py
```

This starts the analysis API at:

```text
http://localhost:8001/health
```

The analysis endpoint is available at `http://localhost:8001/api/analyze?scenario=demo1`.

### 3) Serve the frontend

From the project root:

```powershell
python -m http.server 4173
```

Then open:

```text
http://localhost:4173/
```

The root page serves the static dashboard from `frontend/index.html`.

> Important: the frontend is static and relies on the backend API being running at `http://localhost:8001`.

## Demo walkthrough

Open the dashboard at `http://localhost:4173/` and use the intake buttons:

- **Use demo1 files** loads the Mumbai offshore scenario.
- **Use demo2 files** loads the Gujarat/Arabian Sea scenario.

Each button calls the matching API scenario and updates the map, incident details, candidate vessels, and attribution evidence. Candidate scores are investigative indicators calculated from AIS proximity, timing, vessel type, trajectory, and behavioral anomalies; they are not legal findings.

### 4) Optional React frontend

Make sure Node.js 20+ is installed first:

```powershell
cd frontend-react
npm install
npm run dev
```

## Demo scenarios

The prototype currently supports scenario-based analysis via `demo1` and `demo2`:

- `demo1` uses `data/raw/demo_ais_tracks.csv` and `data/raw/demo_oil_spill_mask.tif`
- `demo2` uses `data/raw/demo2_ais_tracks.csv` and `data/raw/demo2_oil_spill_mask.tif`

These are configured in `backend/api/server.py` and are intended as synthetic demo data for development and presentation.

The scenarios intentionally use different AIS tracks, origins, time windows, environmental conditions, and spill metadata. Their ranked vessel lists and posterior scores should therefore change when switching between the two demo buttons.

## Repository layout

- `frontend/` - analyst dashboard and browser interactions
- `frontend-react/` - React/Vite version of the analyst dashboard
- `backend/` - API and orchestration services
- `ml/` - satellite segmentation and vessel-ranking models
- `data/` - synthetic demo datasets, processed outputs, and schemas
- `simulation/` - backward hindcast and forward spill forecast workflows
- `docs/` - architecture and integration notes
- `tests/` - unit tests for segmentation, drift logic, and vessel ranking

## Run model tests

```powershell
python -m unittest discover -s tests -v
```

The suite covers segmentation behavior, drift reconstruction/forecast logic, and AIS vessel attribution scoring.
