# Coastal Watch Local API

Start the demo analysis API from the repository root:

```powershell
python backend/api/server.py
```

The API listens on `http://localhost:8001`.

Available endpoint:

```text
GET /api/analyze?scenario=demo1
GET /api/analyze?scenario=demo2
```

The endpoint runs the AIS ranking MVP and summarizes the selected TIFF. The vanilla frontend calls it when either demo is selected.
