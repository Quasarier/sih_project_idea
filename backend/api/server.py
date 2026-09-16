"""Small local API that connects demo intake to the project MVP modules."""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from ml.ranking.rank_vessels import parse_time, rank_vessels

SCENARIOS = {
    "demo1": {
        "ais": ROOT / "data/raw/demo_ais_tracks.csv",
        "tiff": ROOT / "data/raw/demo_oil_spill_mask.tif",
        "origin": [18.72, 72.10],
        "hindcast_origin": [18.16, 71.30],
        "window_start": "2024-06-17T22:10:00Z",
        "window_end": "2024-06-18T01:40:00Z",
        "detection": "18 Jun 2024, 06:42 UTC",
        "area_km2": 12.8,
        "confidence": 87.4,
        "environment": {"wind": "SW · 18.6 km/h", "current": "WNW · 0.72 m/s", "sea_state": "Calm", "water_temperature": "28.4 °C", "current_vector": [0.14, 0.20]},
    },
    "demo2": {
        "ais": ROOT / "data/raw/demo2_ais_tracks.csv",
        "tiff": ROOT / "data/raw/demo2_oil_spill_mask.tif",
        "origin": [20.02, 69.52],
        "hindcast_origin": [19.06, 69.20],
        "window_start": "2024-08-22T04:00:00Z",
        "window_end": "2024-08-22T08:00:00Z",
        "detection": "22 Aug 2024, 12:15 UTC",
        "area_km2": 27.6,
        "confidence": 79.2,
        "environment": {"wind": "NE · 24.2 km/h", "current": "ENE · 1.08 m/s", "sea_state": "Moderate", "water_temperature": "30.1 °C", "current_vector": [0.24, 0.08]},
    },
}


def summarize_tiff(path: Path) -> dict:
    try:
        from PIL import Image
        import numpy as np

        pixels = np.asarray(Image.open(path).convert("L"))
        positive = int((pixels > 0).sum())
        return {"width": pixels.shape[1], "height": pixels.shape[0], "positive_pixels": positive, "positive_percent": round(positive / pixels.size * 100, 2)}
    except ImportError:
        return {"width": None, "height": None, "positive_pixels": None, "positive_percent": None}


def analyze(scenario_id: str) -> dict:
    scenario = SCENARIOS[scenario_id]
    candidates = rank_vessels(scenario["ais"], *scenario["hindcast_origin"], parse_time(scenario["window_start"]), parse_time(scenario["window_end"]))
    return {"scenario": scenario_id, "tiff": scenario["tiff"].name, "ais": scenario["ais"].name, "detection": scenario["detection"], "origin": scenario["origin"], "hindcast_origin": scenario["hindcast_origin"], "origin_window": [scenario["window_start"], scenario["window_end"]], "area_km2": scenario["area_km2"], "confidence": scenario["confidence"], "environment": scenario["environment"], "tiff_summary": summarize_tiff(scenario["tiff"]), "candidates": candidates}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        request = urlparse(self.path)
        if request.path != "/api/analyze":
            self.send_error(404)
            return
        scenario_id = parse_qs(request.query).get("scenario", ["demo1"])[0]
        if scenario_id not in SCENARIOS:
            self.send_error(400, "Unknown scenario")
            return
        payload = json.dumps(analyze(scenario_id)).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        return


if __name__ == "__main__":
    print("Coastal Watch API listening on http://localhost:8001")
    ThreadingHTTPServer(("localhost", 8001), Handler).serve_forever()
