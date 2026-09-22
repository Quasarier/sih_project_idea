"""Small deterministic drift utilities for the MVP.

These functions are placeholders for OpenDrift/INCOIS integrations. They keep
coordinates in latitude/longitude and are intentionally easy to replace.
"""

from __future__ import annotations

import math

def _curved_offset(current: tuple[float, float], hour: int, hours: int, curve_strength: float) -> tuple[float, float]:
    if not curve_strength or hours <= 0:
        return 0.0, 0.0
    current_lat, current_lon = current
    magnitude = math.hypot(current_lat, current_lon) or 1.0
    curve = curve_strength * math.sin(math.pi * hour / hours)
    return -current_lon / magnitude * curve, current_lat / magnitude * curve


def backtrack(point: tuple[float, float], current: tuple[float, float], hours: int, curve_strength: float = 0.0) -> list[tuple[float, float]]:
    """Return hourly positions backward from the observed point."""
    latitude, longitude = point
    latitude_step, longitude_step = current
    return [
        (
            round(latitude - latitude_step * hour - _curved_offset(current, hour, hours, curve_strength)[0], 6),
            round(longitude - longitude_step * hour - _curved_offset(current, hour, hours, curve_strength)[1], 6),
        )
        for hour in range(hours + 1)
    ]


def forecast(point: tuple[float, float], current: tuple[float, float], hours: int, curve_strength: float = 0.0) -> list[tuple[float, float]]:
    """Return hourly positions forward from the observed point."""
    latitude, longitude = point
    latitude_step, longitude_step = current
    return [
        (
            round(latitude + latitude_step * hour + _curved_offset(current, hour, hours, curve_strength)[0], 6),
            round(longitude + longitude_step * hour + _curved_offset(current, hour, hours, curve_strength)[1], 6),
        )
        for hour in range(hours + 1)
    ]


def origin_window(point: tuple[float, float], current: tuple[float, float], hours: int, curve_strength: float = 0.0) -> dict:
    """Return the first/last point of a simple backward origin estimate."""
    path = backtrack(point, current, hours, curve_strength)
    return {"start": path[-1], "end": path[0], "hours": hours, "path": path}
