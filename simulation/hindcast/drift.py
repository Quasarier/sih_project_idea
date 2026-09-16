"""Small deterministic drift utilities for the MVP.

These functions are placeholders for OpenDrift/INCOIS integrations. They keep
coordinates in latitude/longitude and are intentionally easy to replace.
"""

from __future__ import annotations


def backtrack(point: tuple[float, float], current: tuple[float, float], hours: int) -> list[tuple[float, float]]:
    """Return hourly positions backward from the observed point."""
    latitude, longitude = point
    latitude_step, longitude_step = current
    return [(round(latitude - latitude_step * hour, 6), round(longitude - longitude_step * hour, 6)) for hour in range(hours + 1)]


def forecast(point: tuple[float, float], current: tuple[float, float], hours: int) -> list[tuple[float, float]]:
    """Return hourly positions forward from the observed point."""
    latitude, longitude = point
    latitude_step, longitude_step = current
    return [(round(latitude + latitude_step * hour, 6), round(longitude + longitude_step * hour, 6)) for hour in range(hours + 1)]


def origin_window(point: tuple[float, float], current: tuple[float, float], hours: int) -> dict:
    """Return the first/last point of a simple backward origin estimate."""
    path = backtrack(point, current, hours)
    return {"start": path[-1], "end": path[0], "hours": hours, "path": path}
