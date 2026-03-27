from __future__ import annotations

from pydantic import BaseModel

from ..config import PlanViewScenarioConfig
from ..geometry import basin_area_m2, basin_volume_m3


class ScenarioMetrics(BaseModel):
    basin_area_m2: float
    basin_volume_m3: float
    detention_time_s: float
    detention_time_h: float
    surface_overflow_rate_m_per_h: float
    surface_overflow_rate_m_per_d: float
    baffle_count: int


def compute_scenario_metrics(scenario: PlanViewScenarioConfig) -> ScenarioMetrics:
    area = basin_area_m2(scenario.geometry)
    volume = basin_volume_m3(scenario.geometry)
    detention_time_s = volume / scenario.hydraulics.flow_rate_m3_s
    overflow_rate_m_per_s = scenario.hydraulics.flow_rate_m3_s / area

    return ScenarioMetrics(
        basin_area_m2=area,
        basin_volume_m3=volume,
        detention_time_s=detention_time_s,
        detention_time_h=detention_time_s / 3600.0,
        surface_overflow_rate_m_per_h=overflow_rate_m_per_s * 3600.0,
        surface_overflow_rate_m_per_d=overflow_rate_m_per_s * 86400.0,
        baffle_count=len(scenario.baffles),
    )
