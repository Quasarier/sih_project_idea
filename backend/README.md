# Backend

`api/` will expose incident, map-layer, candidate-vessel, and evidence endpoints.

`services/` will orchestrate image inference, drift ensembles, AIS filtering, and attribution evidence aggregation.

## API configuration

The local API allows `http://localhost:4173` and `http://localhost:5173` by default.
Override the comma-separated origins with `COASTAL_WATCH_ALLOWED_ORIGINS`.

Set `COASTAL_WATCH_API_TOKEN` to require an `Authorization: Bearer <token>` header
for analysis requests. The `/health` endpoint remains available for local readiness checks.
