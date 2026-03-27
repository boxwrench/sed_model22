from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ..config import (
    LaunderZoneFeatureConfig,
    LongitudinalScenarioConfig,
    PerforatedBaffleFeatureConfig,
    PlateSettlerZoneFeatureConfig,
    SolidBaffleFeatureConfig,
)
from ..mesh.longitudinal import LongitudinalMeshSummary
from ..solver.longitudinal import LongitudinalFieldData, LongitudinalTracerSummary


class LongitudinalMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    basin_area_m2: float
    basin_volume_m3: float
    theoretical_detention_time_s: float
    surface_overflow_rate_m_per_d: float
    transition_headloss_m: float
    post_transition_velocity_uniformity_index: float
    jet_redistribution_length_m: float
    plate_inlet_mean_velocity_m_s: float
    plate_inlet_max_velocity_m_s: float
    plate_inlet_upward_velocity_m_s: float
    launder_mean_upward_velocity_m_s: float
    launder_peak_upward_velocity_m_s: float
    dead_zone_fraction: float
    short_circuiting_index: float
    t10_s: float
    t50_s: float
    t90_s: float
    morrill_index: float
    settling_exceedance_fraction_by_threshold: dict[str, float]
    notes: list[str] = Field(default_factory=list)


def compute_longitudinal_metrics(
    scenario: LongitudinalScenarioConfig,
    mesh: LongitudinalMeshSummary,
    fields: LongitudinalFieldData,
    tracer: LongitudinalTracerSummary,
) -> LongitudinalMetrics:
    basin_area_m2 = scenario.geometry.basin_length_m * scenario.geometry.basin_width_m
    basin_volume_m3 = basin_area_m2 * scenario.geometry.water_depth_m
    theoretical_detention_time_s = basin_volume_m3 / scenario.hydraulics.flow_rate_m3_s
    surface_overflow_rate_m_per_d = (
        scenario.hydraulics.flow_rate_m3_s / basin_area_m2
    ) * 86400.0

    post_transition_index = _station_index(scenario, mesh, "post_transition")
    plate_inlet_index = _station_index(scenario, mesh, "plate_inlet")

    transition_headloss_m = _transition_headloss_m(scenario, mesh, fields)
    post_transition_velocity_uniformity_index = _uniformity_index(fields.velocity_u_m_s[post_transition_index])
    jet_redistribution_length_m = _jet_redistribution_length_m(scenario, fields.velocity_u_m_s)
    plate_inlet_mean_velocity_m_s = _mean_abs(fields.velocity_u_m_s[plate_inlet_index])
    plate_inlet_max_velocity_m_s = _max_abs(fields.velocity_u_m_s[plate_inlet_index])
    plate_inlet_upward_velocity_m_s = _mean_positive(fields.velocity_w_m_s[plate_inlet_index])

    launder_columns = _launder_columns(scenario, mesh)
    launder_upward_values = [
        max(0.0, fields.velocity_w_m_s[i][-1])
        for i in launder_columns
    ]
    launder_mean_upward_velocity_m_s = _mean(launder_upward_values)
    launder_peak_upward_velocity_m_s = max(launder_upward_values, default=0.0)

    basin_mean_speed = _mean([value for row in fields.speed_m_s for value in row])
    speed_threshold = scenario.performance_proxies.dead_zone_velocity_fraction * basin_mean_speed
    dead_zone_count = sum(1 for row in fields.speed_m_s for value in row if value < speed_threshold)
    dead_zone_fraction = dead_zone_count / max(mesh.cell_count, 1)

    settling_exceedance_fraction_by_threshold: dict[str, float] = {}
    launder_threshold_values = launder_upward_values
    for threshold in scenario.performance_proxies.settling_velocity_thresholds_m_per_s:
        key = _threshold_key(threshold)
        if launder_threshold_values:
            exceedance = sum(1 for value in launder_threshold_values if value > threshold) / len(launder_threshold_values)
        else:
            exceedance = 0.0
        settling_exceedance_fraction_by_threshold[key] = exceedance

    short_circuiting_index = tracer.t10_s / theoretical_detention_time_s
    morrill_index = tracer.t90_s / max(tracer.t10_s, 1.0e-12)

    return LongitudinalMetrics(
        basin_area_m2=basin_area_m2,
        basin_volume_m3=basin_volume_m3,
        theoretical_detention_time_s=theoretical_detention_time_s,
        surface_overflow_rate_m_per_d=surface_overflow_rate_m_per_d,
        transition_headloss_m=transition_headloss_m,
        post_transition_velocity_uniformity_index=post_transition_velocity_uniformity_index,
        jet_redistribution_length_m=jet_redistribution_length_m,
        plate_inlet_mean_velocity_m_s=plate_inlet_mean_velocity_m_s,
        plate_inlet_max_velocity_m_s=plate_inlet_max_velocity_m_s,
        plate_inlet_upward_velocity_m_s=plate_inlet_upward_velocity_m_s,
        launder_mean_upward_velocity_m_s=launder_mean_upward_velocity_m_s,
        launder_peak_upward_velocity_m_s=launder_peak_upward_velocity_m_s,
        dead_zone_fraction=dead_zone_fraction,
        short_circuiting_index=short_circuiting_index,
        t10_s=tracer.t10_s,
        t50_s=tracer.t50_s,
        t90_s=tracer.t90_s,
        morrill_index=morrill_index,
        settling_exceedance_fraction_by_threshold=settling_exceedance_fraction_by_threshold,
        notes=[
            "t10, t50, and t90 are RTD proxy thresholds derived from the deterministic breakthrough curve.",
            "Settling and launder proxy metrics are still computed directly from the steady longitudinal velocity field.",
        ],
    )


def _station_index(scenario: LongitudinalScenarioConfig, mesh: LongitudinalMeshSummary, name: str) -> int:
    for station in scenario.evaluation_stations:
        if station.name == name:
            return _nearest_x_index(station.x_m, mesh.dx_m, mesh.nx)
    raise ValueError(f"scenario does not define an evaluation station named '{name}'")


def _nearest_x_index(x_m: float, dx_m: float, nx: int) -> int:
    index = int(round(x_m / dx_m - 0.5))
    return min(max(index, 0), nx - 1)


def _transition_headloss_m(
    scenario: LongitudinalScenarioConfig,
    mesh: LongitudinalMeshSummary,
    fields: LongitudinalFieldData,
) -> float:
    transition_feature = None
    for feature in scenario.features:
        if feature.name == "transition_wall" and isinstance(
            feature, (PerforatedBaffleFeatureConfig, SolidBaffleFeatureConfig)
        ):
            transition_feature = feature
            break
    if transition_feature is None:
        for feature in scenario.features:
            if isinstance(feature, (PerforatedBaffleFeatureConfig, SolidBaffleFeatureConfig)):
                transition_feature = feature
                break
    if transition_feature is None:
        return 0.0

    face_index = min(max(int(round(transition_feature.x_m / mesh.dx_m)), 1), mesh.nx - 1)
    upstream_values: list[float] = []
    downstream_values: list[float] = []

    for k in range(mesh.nz):
        row_lower = k * mesh.dz_m
        row_upper = (k + 1) * mesh.dz_m
        overlap = _interval_overlap_fraction(row_lower, row_upper, transition_feature.z_bottom_m, transition_feature.z_top_m)
        if overlap <= 0.0:
            continue
        upstream_values.append(fields.head[face_index - 1][k])
        downstream_values.append(fields.head[face_index][k])

    if not upstream_values:
        return 0.0
    return _mean(upstream_values) - _mean(downstream_values)


def _uniformity_index(column: list[float]) -> float:
    magnitudes = [abs(value) for value in column]
    max_magnitude = max(magnitudes, default=0.0)
    if max_magnitude <= 0.0:
        return 0.0
    return _mean(magnitudes) / max_magnitude


def _jet_redistribution_length_m(
    scenario: LongitudinalScenarioConfig,
    velocity_u_m_s: list[list[float]],
) -> float:
    vui_values: list[float] = []
    for i in range(scenario.numerics.nx):
        column = [velocity_u_m_s[i][k] for k in range(scenario.numerics.nz)]
        vui_values.append(_uniformity_index(column))

    for index in range(max(len(vui_values) - 2, 0)):
        if vui_values[index] >= 0.80 and vui_values[index + 1] >= 0.80 and vui_values[index + 2] >= 0.80:
            dx_m = scenario.geometry.basin_length_m / scenario.numerics.nx
            return (index + 0.5) * dx_m
    return scenario.geometry.basin_length_m


def _launder_columns(scenario: LongitudinalScenarioConfig, mesh: LongitudinalMeshSummary) -> list[int]:
    columns: list[int] = []
    for feature in scenario.features:
        if not isinstance(feature, LaunderZoneFeatureConfig):
            continue
        for i in range(mesh.nx):
            cell_lower = i * mesh.dx_m
            cell_upper = (i + 1) * mesh.dx_m
            if _interval_overlap_fraction(cell_lower, cell_upper, feature.x_start_m, feature.x_end_m) > 0.0:
                if i not in columns:
                    columns.append(i)
    return columns


def _mean_abs(values: list[float]) -> float:
    magnitudes = [abs(value) for value in values]
    return _mean(magnitudes)


def _max_abs(values: list[float]) -> float:
    return max((abs(value) for value in values), default=0.0)


def _mean_positive(values: list[float]) -> float:
    positives = [max(0.0, value) for value in values]
    return _mean(positives)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _interval_overlap_fraction(lower_a: float, upper_a: float, lower_b: float, upper_b: float) -> float:
    overlap = min(upper_a, upper_b) - max(lower_a, lower_b)
    if overlap <= 0.0:
        return 0.0
    width = upper_a - lower_a
    return overlap / width if width > 0.0 else 0.0


def _threshold_key(value: float) -> str:
    return format(value, "g")
