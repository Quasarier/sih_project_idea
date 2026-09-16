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

Run the backend before opening the dashboard, because the frontend requests analysis data from the local API:

```powershell
python backend\api\server.py
```

This starts the analysis API at:

```text
http://localhost:8001/api/analyze
```

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

### 4) Optional React frontend

If you want to run the React version instead, make sure Node.js 20+ is installed first:

If you want to run the React version instead:

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
