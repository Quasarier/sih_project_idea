"""Rank AIS vessels against a probable oil-spill origin.

This MVP model is intentionally explainable. It uses Bayesian odds and does not
claim legal attribution. Replace the priors and likelihood ratios with values
learned from reviewed historical incidents when labels become available.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

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


def likelihood_ratio(distance: float, time_offset_hours: float, ship_type: str, heading_delta: float) -> dict[str, float]:
    proximity = 8.0 if distance <= 5 else 4.0 if distance <= 15 else 1.6 if distance <= 35 else 0.55
    timing = 6.0 if time_offset_hours <= 1 else 3.0 if time_offset_hours <= 3 else 1.2 if time_offset_hours <= 8 else 0.45
    cargo = 2.5 if ship_type in {"tanker", "oil_tanker", "product_tanker"} else 0.75
    trajectory = 3.0 if heading_delta <= 35 else 1.6 if heading_delta <= 80 else 0.7
    return {"proximity": proximity, "timing": timing, "vessel_type": cargo, "trajectory": trajectory}


def posterior(prior: float, ratios: dict[str, float]) -> float:
    prior_odds = prior / (1 - prior)
    evidence_odds = prior_odds
    for ratio in ratios.values():
        evidence_odds *= ratio
    return evidence_odds / (1 + evidence_odds)


def behavioral_anomaly_score(points: list[dict]) -> int:
    """Estimate unusual movement from AIS reporting gaps and motion changes."""
    gaps = [(later["timestamp"] - earlier["timestamp"]).total_seconds() / 60 for earlier, later in zip(points, points[1:])]
    max_gap = max(gaps, default=0)
    heading_changes = [angle_difference(later["heading_deg"], earlier["heading_deg"]) for earlier, later in zip(points, points[1:])]
    speed_changes = [abs(later["speed_knots"] - earlier["speed_knots"]) for earlier, later in zip(points, points[1:])]
    score = 15 + max(0, max_gap - 60) / 6 + sum(heading_changes) / 2 + sum(speed_changes) * 5
    return min(100, round(score))


def trajectory_match_score(heading_delta: float) -> int:
    """Convert heading compatibility into a bounded evidence score."""
    return 90 if heading_delta <= 35 else 65 if heading_delta <= 80 else 25


def rank_vessels(csv_path: Path, origin_lat: float, origin_lon: float, window_start: datetime, window_end: datetime) -> list[dict]:
    tracks = defaultdict(list)
    with csv_path.open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            row["latitude"] = float(row["latitude"])
            row["longitude"] = float(row["longitude"])
            row["speed_knots"] = float(row["speed_knots"])
            row["heading_deg"] = float(row["heading_deg"])
            row["timestamp"] = parse_time(row["timestamp"])
            tracks[row["mmsi"]].append(row)

    ranked = []
    for points in tracks.values():
        points.sort(key=lambda point: point["timestamp"])
        closest = min(points, key=lambda point: distance_km(point["latitude"], point["longitude"], origin_lat, origin_lon))
        distance = distance_km(closest["latitude"], closest["longitude"], origin_lat, origin_lon)
        if closest["timestamp"] < window_start:
            time_offset = (window_start - closest["timestamp"]).total_seconds() / 3600
        elif closest["timestamp"] > window_end:
            time_offset = (closest["timestamp"] - window_end).total_seconds() / 3600
        else:
            time_offset = 0
        heading_delta = angle_difference(closest["heading_deg"], 247.0)
        prior = 0.08 if closest["ship_type"] in {"tanker", "oil_tanker", "product_tanker"} else 0.03
        anomaly_score = behavioral_anomaly_score(points)
        ratios = likelihood_ratio(distance, time_offset, closest["ship_type"], heading_delta)
        ratios["behavioral_anomaly"] = 1 + anomaly_score / 20
        probability = posterior(prior, ratios)
        trajectory_score = trajectory_match_score(heading_delta)
        ranked.append({
            "mmsi": closest["mmsi"], "imo": closest["imo"], "vessel_name": closest["vessel_name"],
            "ship_type": closest["ship_type"], "distance_km": round(distance, 2),
            "time_offset_hours": round(time_offset, 2), "posterior": round(probability * 100, 1),
            "prior": prior, "likelihood_ratios": ratios,
            "evidence": {"origin_proximity": distance <= 15, "inside_time_window": time_offset == 0, "tanker_profile": prior > 0.03, "heading_delta_deg": round(heading_delta, 1), "trajectory_match": trajectory_score, "behavioral_anomaly": anomaly_score},
        })
    return sorted(ranked, key=lambda item: item["posterior"], reverse=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank AIS vessels for an oil-spill origin hypothesis")
    parser.add_argument("--ais", type=Path, required=True)
    parser.add_argument("--origin-lat", type=float, default=18.72)
    parser.add_argument("--origin-lon", type=float, default=72.10)
    parser.add_argument("--start", default="2024-06-17T22:10:00Z")
    parser.add_argument("--end", default="2024-06-18T01:40:00Z")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = rank_vessels(args.ais, args.origin_lat, args.origin_lon, parse_time(args.start), parse_time(args.end))
    payload = json.dumps({"origin": [args.origin_lat, args.origin_lon], "candidates": result}, indent=2)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)


if __name__ == "__main__":
    main()
