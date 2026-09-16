"""
Rank AIS vessels against a probable oil-spill origin.

This MVP model is intentionally explainable. It uses Bayesian odds and does not
claim legal attribution. Replace the priors and likelihood ratios with values
learned from reviewed historical incidents when labels become available.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import configuration
try:
    from .config import RankingConfig
except ImportError:
    # Fallback for direct execution
    from config import RankingConfig

EARTH_RADIUS_KM = 6371.0


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def distance_km(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
    lat_a, lat_b = math.radians(lat_a), math.radians(lat_b)
    delta_lat = lat_b - lat_a
    delta_lon = math.radians(lon_b - lon_a)
    value = math.sin(delta_lat / 2) ** 2 + math.cos(lat_a) * math.cos(lat_b) * math.sin(delta_lon / 2) ** 2
    return EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def angle_difference(first: float, second: float) -> float:
    return abs((first - second + 180) % 360 - 180)


# Configuration for likelihood ratios
LIKELIHOOD_CONFIG = {
    "proximity": {
        "close": {"threshold": 5, "ratio": 8.0},
        "medium": {"threshold": 15, "ratio": 4.0},
        "far": {"threshold": 35, "ratio": 1.6},
        "distant": {"ratio": 0.55}
    },
    "timing": {
        "immediate": {"threshold": 1, "ratio": 6.0},
        "recent": {"threshold": 3, "ratio": 3.0},
        "delayed": {"threshold": 8, "ratio": 1.2},
        "late": {"ratio": 0.45}
    },
    "vessel_type": {
        "tanker": {"types": ["tanker", "oil_tanker", "product_tanker"], "ratio": 2.5},
        "other": {"ratio": 0.75}
    },
    "trajectory": {
        "strong": {"threshold": 35, "ratio": 3.0},
        "moderate": {"threshold": 80, "ratio": 1.6},
        "weak": {"ratio": 0.7}
    }
}

def likelihood_ratio(distance: float, time_offset_hours: float, ship_type: str, heading_delta: float, config: RankingConfig | None = None) -> dict[str, float]:
    """Calculate likelihood ratios based on configurable thresholds."""
    settings = config or RankingConfig.get_instance()
    proximity = (
        settings.likelihood_proximity_close if distance <= settings.proximity_close else
        settings.likelihood_proximity_medium if distance <= settings.proximity_medium else
        settings.likelihood_proximity_far if distance <= settings.proximity_far else
        settings.likelihood_proximity_distant
    )
    timing = (
        settings.likelihood_timing_immediate if time_offset_hours <= settings.timing_immediate else
        settings.likelihood_timing_recent if time_offset_hours <= settings.timing_recent else
        settings.likelihood_timing_delayed if time_offset_hours <= settings.timing_delayed else
        settings.likelihood_timing_late
    )
    cargo = settings.likelihood_vessel_type_tanker if ship_type.lower() in {"tanker", "oil_tanker", "product_tanker"} else settings.likelihood_vessel_type_other
    trajectory = (
        settings.likelihood_trajectory_strong if heading_delta <= settings.trajectory_strong else
        settings.likelihood_trajectory_moderate if heading_delta <= settings.trajectory_moderate else
        settings.likelihood_trajectory_weak
    )
    return {
        "proximity": proximity, 
        "timing": timing, 
        "vessel_type": cargo, 
        "trajectory": trajectory
    }


def posterior(prior: float, ratios: dict[str, float]) -> float:
    prior_odds = prior / (1 - prior)
    evidence_odds = prior_odds
    for ratio in ratios.values():
        evidence_odds *= ratio
    return evidence_odds / (1 + evidence_odds)


def behavioral_anomaly_score(points: list[dict], config: RankingConfig | None = None) -> int:
    """Estimate unusual movement from AIS reporting gaps and motion changes."""
    settings = config or RankingConfig.get_instance()
    gaps = [(later["timestamp"] - earlier["timestamp"]).total_seconds() / 60 for earlier, later in zip(points, points[1:])]
    max_gap = max(gaps, default=0)
    heading_changes = [angle_difference(later["heading_deg"], earlier["heading_deg"]) for earlier, later in zip(points, points[1:])]
    speed_changes = [abs(later["speed_knots"] - earlier["speed_knots"]) for earlier, later in zip(points, points[1:])]
    score = 15 + max(0, max_gap - settings.behavioral_anomaly_max_gap) / 6 + sum(heading_changes) * settings.behavioral_anomaly_heading_weight + sum(speed_changes) * settings.behavioral_anomaly_speed_weight
    return min(100, round(score))


def trajectory_match_score(heading_delta: float, config: RankingConfig | None = None) -> int:
    """Convert heading compatibility into a bounded evidence score."""
    settings = config or RankingConfig.get_instance()
    return 90 if heading_delta <= settings.trajectory_strong else 65 if heading_delta <= settings.trajectory_moderate else 25


def rank_vessels(csv_path: Path, origin_lat: float, origin_lon: float, window_start: datetime, window_end: datetime) -> list[dict]:
    """Rank AIS vessels based on proximity to oil-spill origin and other factors."""
    
    logger.info(f"Starting vessel ranking for {csv_path} at ({origin_lat}, {origin_lon})")
    
    # Get configuration
    config = RankingConfig.get_instance()
    
    # Load and parse AIS data
    tracks = defaultdict(list)
    try:
        with csv_path.open(newline="", encoding="utf-8") as source:
            reader = csv.DictReader(source)
            required_columns = ["mmsi", "imo", "vessel_name", "latitude", "longitude", 
                              "speed_knots", "heading_deg", "timestamp", "ship_type"]
            
            for row in reader:
                # Validate required columns
                missing_cols = [col for col in required_columns if col not in row]
                if missing_cols:
                    logger.warning(f"Missing columns {missing_cols} in row {row.get('mmsi', 'unknown')}")
                    continue
                
                # Parse and validate data
                try:
                    row["latitude"] = float(row["latitude"])
                    row["longitude"] = float(row["longitude"])
                    row["speed_knots"] = float(row["speed_knots"])
                    row["heading_deg"] = float(row["heading_deg"])
                    if not -90 <= row["latitude"] <= 90 or not -180 <= row["longitude"] <= 180:
                        raise ValueError("coordinates outside valid geographic ranges")
                    if row["speed_knots"] < 0 or not 0 <= row["heading_deg"] <= 360:
                        raise ValueError("speed or heading outside valid AIS ranges")
                    row["timestamp"] = parse_time(row["timestamp"])
                    tracks[row["mmsi"]].append(row)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid data in row {row}: {e}")
                    continue
                    
        logger.info(f"Loaded {len(tracks)} vessel tracks")
        
    except FileNotFoundError:
        logger.error(f"AIS file not found: {csv_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading AIS data: {e}")
        raise
    
    # Rank vessels
    ranked = []
    for mmsi, points in tracks.items():
        try:
            # Sort points by timestamp
            points.sort(key=lambda point: point["timestamp"])
            
            # Find closest point to origin
            closest = min(points, key=lambda point: distance_km(point["latitude"], point["longitude"], origin_lat, origin_lon))
            distance = distance_km(closest["latitude"], closest["longitude"], origin_lat, origin_lon)
            
            # Calculate time offset
            if closest["timestamp"] < window_start:
                time_offset = (window_start - closest["timestamp"]).total_seconds() / 3600
            elif closest["timestamp"] > window_end:
                time_offset = (closest["timestamp"] - window_end).total_seconds() / 3600
            else:
                time_offset = 0
            
            # Calculate heading difference
            heading_delta = angle_difference(closest["heading_deg"], 247.0)
            
            # Determine prior probability based on vessel type
            is_tanker = closest["ship_type"] in {"tanker", "oil_tanker", "product_tanker"}
            prior = config.prior_tanker if is_tanker else config.prior_other
            
            # Calculate behavioral anomaly score
            anomaly_score = behavioral_anomaly_score(points, config)
            
            # Calculate likelihood ratios
            ratios = likelihood_ratio(distance, time_offset, closest["ship_type"], heading_delta, config)
            ratios["behavioral_anomaly"] = 1 + anomaly_score / 20
            
            # Calculate posterior probability
            probability = posterior(prior, ratios)
            
            # Calculate trajectory match score
            trajectory_score = trajectory_match_score(heading_delta, config)
            
            # Create result entry
            result_entry = {
                "mmsi": closest["mmsi"], 
                "imo": closest["imo"], 
                "vessel_name": closest["vessel_name"],
                "ship_type": closest["ship_type"], 
                "distance_km": round(distance, 2),
                "time_offset_hours": round(time_offset, 2), 
                "posterior": round(probability * 100, 1),
                "prior": prior, 
                "likelihood_ratios": ratios,
                "evidence": {
                    "origin_proximity": distance <= config.proximity_medium,
                    "inside_time_window": time_offset == 0, 
                    "tanker_profile": is_tanker,
                    "heading_delta_deg": round(heading_delta, 1), 
                    "trajectory_match": trajectory_score, 
                    "behavioral_anomaly": anomaly_score
                },
            }
            
            ranked.append(result_entry)
            
        except Exception as e:
            logger.error(f"Error processing vessel {mmsi}: {e}")
            continue
    
    # Sort by posterior probability
    ranked = sorted(ranked, key=lambda item: item["posterior"], reverse=True)
    logger.info(f"Ranked {len(ranked)} vessels")
    
    return ranked


def main() -> None:
    """Command-line interface for vessel ranking."""
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Rank AIS vessels for an oil-spill origin hypothesis")
    parser.add_argument("--ais", type=Path, required=True, help="Path to AIS CSV file")
    parser.add_argument("--origin-lat", type=float, default=18.72, help="Latitude of oil-spill origin")
    parser.add_argument("--origin-lon", type=float, default=72.10, help="Longitude of oil-spill origin")
    parser.add_argument("--start", default="2024-06-17T22:10:00Z", help="Start of time window")
    parser.add_argument("--end", default="2024-06-18T01:40:00Z", help="End of time window")
    parser.add_argument("--output", type=Path, help="Output file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Parse time arguments
        start_time = parse_time(args.start)
        end_time = parse_time(args.end)
        
        # Run ranking
        result = rank_vessels(args.ais, args.origin_lat, args.origin_lon, start_time, end_time)
        
        # Create output payload
        payload = json.dumps({
            "origin": [args.origin_lat, args.origin_lon], 
            "candidates": result
        }, indent=2)
        
        # Output result
        if args.output:
            args.output.write_text(payload + "\n", encoding="utf-8")
            logger.info(f"Results written to {args.output}")
        else:
            print(payload)
            
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    main()
