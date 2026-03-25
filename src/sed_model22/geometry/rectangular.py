from __future__ import annotations

from ..config import GeometryConfig


def basin_area_m2(geometry: GeometryConfig) -> float:
    return geometry.length_m * geometry.width_m


def basin_volume_m3(geometry: GeometryConfig) -> float:
    return basin_area_m2(geometry) * geometry.water_depth_m
