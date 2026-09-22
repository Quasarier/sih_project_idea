"""Small local API that connects demo intake to the project MVP modules."""

from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ALLOWED_ORIGINS = {
    origin.strip()
    for origin in os.getenv("COASTAL_WATCH_ALLOWED_ORIGINS", "http://localhost:4173,http://localhost:5173").split(",")
    if origin.strip()
}
API_TOKEN = os.getenv("COASTAL_WATCH_API_TOKEN")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from ml.ranking.rank_vessels import parse_time, rank_vessels
from ml.segmentation.segment_slick import segment_tiff
from simulation.hindcast.drift import forecast, origin_window

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
        "drift_curve_strength": 0.08,
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
        "drift_curve_strength": 0.12,
    },
}


def summarize_tiff(path: Path) -> dict:
    """Safely summarize TIFF file with comprehensive error handling."""
    try:
        from PIL import Image
        import numpy as np

        if not path.exists():
            return {"width": None, "height": None, "positive_pixels": None, "positive_percent": None, "error": f"File not found: {path}"}
            
        if not path.is_file():
            return {"width": None, "height": None, "positive_pixels": None, "positive_percent": None, "error": f"Path is not a file: {path}"}
            
        with Image.open(path) as img:
            pixels = np.asarray(img.convert("L"))
            
        if pixels.size == 0:
            return {"width": 0, "height": 0, "positive_pixels": 0, "positive_percent": 0.0}
            
        positive = int((pixels > 0).sum())
        return {
            "width": pixels.shape[1], 
            "height": pixels.shape[0], 
            "positive_pixels": positive, 
            "positive_percent": round(positive / pixels.size * 100, 2)
        }
    except ImportError as e:
        return {"width": None, "height": None, "positive_pixels": None, "positive_percent": None, "error": f"Missing dependency: {str(e)}"}
    except Exception as e:
        return {"width": None, "height": None, "positive_pixels": None, "positive_percent": None, "error": f"Error processing image: {str(e)}"}


def segment_scenario_tiff(path: Path) -> dict:
    """Run the real segmentation baseline without leaving a generated mask behind."""
    try:
        with tempfile.TemporaryDirectory(prefix="coastal-watch-") as directory:
            output_path = Path(directory) / "segmented-mask.tif"
            result = segment_tiff(path, output_path, threshold=15.0)
        result["status"] = "complete"
        return result
    except SystemExit as error:
        return {"status": "unavailable", "error": str(error)}
    except Exception as error:
        logger.warning("Segmentation failed for %s: %s", path, error)
        return {"status": "failed", "error": str(error)}


def analyze(scenario_id: str) -> dict:
    """Analyze a scenario and return results."""
    
    logger.info(f"Analyzing scenario: {scenario_id}")
    
    try:
        scenario = SCENARIOS[scenario_id]
        
        # Validate scenario files exist
        if not scenario["ais"].exists():
            logger.error(f"AIS file not found: {scenario['ais']}")
            raise FileNotFoundError(f"AIS file not found: {scenario['ais']}")
            
        if not scenario["tiff"].exists():
            logger.error(f"TIFF file not found: {scenario['tiff']}")
            raise FileNotFoundError(f"TIFF file not found: {scenario['tiff']}")
        
        # Run vessel ranking
        candidates = rank_vessels(
            scenario["ais"], 
            *scenario["hindcast_origin"], 
            parse_time(scenario["window_start"]), 
            parse_time(scenario["window_end"])
        )
        
        # Summarize TIFF
        tiff_summary = summarize_tiff(scenario["tiff"])
        if "error" in tiff_summary:
            logger.warning(f"Error summarizing TIFF: {tiff_summary['error']}")
        segmentation = segment_scenario_tiff(scenario["tiff"])

        window_start = parse_time(scenario["window_start"])
        window_end = parse_time(scenario["window_end"])
        drift_hours = max(1, round((window_end - window_start).total_seconds() / 3600))
        current_vector = tuple(scenario["environment"]["current_vector"])
        observed_point = tuple(scenario["origin"])
        curve_strength = scenario["drift_curve_strength"]
        drift_origin = origin_window(observed_point, current_vector, drift_hours, curve_strength)
        drift_forecast = forecast(observed_point, current_vector, drift_hours, curve_strength)
        
        # Create result
        result = {
            "scenario": scenario_id, 
            "tiff": scenario["tiff"].name, 
            "ais": scenario["ais"].name, 
            "detection": scenario["detection"], 
            "origin": scenario["origin"], 
            "hindcast_origin": scenario["hindcast_origin"], 
            "origin_window": [scenario["window_start"], scenario["window_end"]], 
            "area_km2": scenario["area_km2"], 
            "confidence": scenario["confidence"], 
            "environment": scenario["environment"], 
            "tiff_summary": tiff_summary, 
            "segmentation": segmentation,
            "candidates": candidates,
            "drift": {
                "hours": drift_hours,
                "curve_strength": curve_strength,
                "hindcast": drift_origin["path"],
                "forecast": drift_forecast,
                "calculated_origin": drift_origin["start"],
            },
        }
        
        logger.info(f"Completed analysis for scenario {scenario_id} with {len(candidates)} candidates")
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing scenario {scenario_id}: {e}")
        raise


class Handler(BaseHTTPRequestHandler):
    """HTTP request handler for the Coastal Watch API."""
    
    def do_GET(self) -> None:
        """Handle GET requests."""
        
        started_at = time.perf_counter()
        request = urlparse(self.path)
        logger.info(f"GET {self.requestline} from {self.client_address}")

        if request.path == "/health":
            self.send_json(200, {"status": "ok"})
            return

        if request.path != "/api/analyze":
            self.send_json(404, {"error": "not_found", "message": "Endpoint not found"})
            return

        if API_TOKEN and self.headers.get("Authorization") != f"Bearer {API_TOKEN}":
            self.send_json(401, {"error": "unauthorized", "message": "Authentication required"})
            return
        
        # Parse and validate scenario parameter
        query_params = parse_qs(request.query)
        scenario_id = query_params.get("scenario", ["demo1"])[0]
        
        # Validate scenario parameter to prevent path traversal or injection attacks
        if not isinstance(scenario_id, str) or not scenario_id.isalnum():
            logger.warning(f"Invalid scenario parameter: {scenario_id}")
            self.send_json(400, {"error": "invalid_scenario", "message": "Invalid scenario parameter"})
            return
            
        if scenario_id not in SCENARIOS:
            logger.warning(f"Unknown scenario: {scenario_id}")
            self.send_json(400, {"error": "unknown_scenario", "message": "Unknown scenario"})
            return
        
        try:
            # Run analysis
            result = analyze(scenario_id)
            payload = json.dumps(result).encode("utf-8")
            
            # Send successful response
            self.send_json(200, result)
            
            logger.info("Successfully processed request for scenario %s in %.3fs", scenario_id, time.perf_counter() - started_at)
            
        except Exception as e:
            logger.error(f"Error processing request for {scenario_id}: {e}")
            self.send_json(500, {"error": "internal_error", "message": "Internal server error"})

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.add_cors_headers()
        self.end_headers()

    def add_cors_headers(self) -> None:
        origin = self.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")

    def send_json(self, status: int, body: dict) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.add_cors_headers()
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
    
    def log_message(self, format: str, *args: object) -> None:
        """Override to use our logger instead of the default."""
        logger.info(f"{self.address_string()} - {format % args}")


if __name__ == "__main__":
    host = os.getenv("COASTAL_WATCH_HOST", "0.0.0.0")
    port = int(os.getenv("COASTAL_WATCH_PORT", "8001"))
    print(f"Coastal Watch API listening on http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
