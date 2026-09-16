# Coastal Watch Architecture

```text
Satellite SAR/EO + AIS + weather/ocean data
                  |
              data/connectors
                  |
              data/schemas
                  |
       backend/services/orchestrator
          /          |             \
 ml/segmentation  simulation/     ml/ranking
                  hindcast/forecast
          \          |             /
              backend/api
                  |
              frontend
```

## Responsibilities

- `data/connectors`: ingest Sentinel-1/EO imagery, AIS tracks, INCOIS currents, ERA5 winds, waves, and vessel metadata.
- `data/schemas`: versioned contracts for scenes, slick masks, trajectories, drift ensembles, and attribution evidence.
- `ml/segmentation`: pixel-level probable slick detection and look-alike classification.
- `simulation/hindcast`: backward drift ensembles that estimate origin region and time window.
- `simulation/forecast`: forward drift ensembles for likely movement over the forecast horizon.
- `ml/ranking`: calibrated vessel-candidate scoring using spatial, temporal, trajectory, and behavior features.
- `backend/services`: pipeline orchestration, uncertainty handling, and evidence aggregation.
- `backend/api`: endpoints consumed by the analyst dashboard.
- `frontend`: visual investigation workspace; current data is representative demo data.
