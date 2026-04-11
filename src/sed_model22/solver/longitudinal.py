from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import math

from pydantic import BaseModel, ConfigDict, Field

from ..config import (
    LaunderZoneFeatureConfig,
    LongitudinalScenarioConfig,
    PerforatedBaffleFeatureConfig,
    PlateSettlerZoneFeatureConfig,
    SolidBaffleFeatureConfig,
)
from ..mesh.longitudinal import LongitudinalMeshSummary


@dataclass(frozen=True)
class _BoundaryMasks:
    inlet_row_scale: list[float]
    launder_col_scale: list[float]


class LongitudinalSolutionSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    solver_name: str
    solver_status: str
    solver_model: str
    iterations: int
    converged: bool
    max_head_delta: float
    inlet_discharge_m3_s: float
    outlet_discharge_m3_s: float
    mass_balance_error: float
    max_velocity_m_s: float
    max_upward_velocity_m_s: float
    blocked_face_count: int
    low_conductance_face_count: int
    supported_scope: list[str]
    notes: list[str]


class LongitudinalFieldData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x_centers_m: list[float]
    z_centers_m: list[float]
    head: list[list[float]]
    velocity_u_m_s: list[list[float]]
    velocity_w_m_s: list[list[float]]
    speed_m_s: list[list[float]]
    cell_divergence_1_per_s: list[list[float]]


class LongitudinalTracerSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    time_points_s: list[float]
    outlet_concentration_history: list[float]
    t10_s: float
    t50_s: float
    t90_s: float
    final_time_s: float
    final_outlet_concentration: float
    converged: bool
    termination_reason: str
    step_count: int
    proxy_model: str = "steady_rtd_proxy_v1"
    notes: list[str] = Field(default_factory=list)


def solve_steady_longitudinal_screening_flow(
    scenario: LongitudinalScenarioConfig,
    mesh: LongitudinalMeshSummary,
) -> tuple[LongitudinalSolutionSummary, LongitudinalFieldData]:
    x_face_conductance, z_face_conductance, boundary_masks = _build_face_conductances(scenario, mesh)
    head = _initial_head_guess(mesh)

    iterations, converged, max_delta = _solve_head_field(
        scenario,
        mesh,
        head,
        x_face_conductance,
        z_face_conductance,
        boundary_masks,
    )

    q_2d = scenario.hydraulics.flow_rate_m3_s / scenario.geometry.basin_width_m
    raw_inflow_per_width = _boundary_discharge_per_width(
        mesh,
        head,
        x_face_conductance,
        z_face_conductance,
        boundary_masks,
        side="west",
    )
    raw_outflow_per_width = _boundary_discharge_per_width(
        mesh,
        head,
        x_face_conductance,
        z_face_conductance,
        boundary_masks,
        side="north",
    )
    if raw_inflow_per_width <= 0.0:
        raise ValueError("solver produced a non-positive inlet flux; cannot scale the longitudinal field")

    raw_velocity_u: list[list[float]] = []
    raw_velocity_w: list[list[float]] = []
    raw_speed: list[list[float]] = []
    raw_divergence: list[list[float]] = []

    for i in range(mesh.nx):
        u_row: list[float] = []
        w_row: list[float] = []
        speed_row: list[float] = []
        divergence_row: list[float] = []

        for k in range(mesh.nz):
            q_w, q_e, q_s, q_n = _cell_face_fluxes(
                mesh,
                head,
                x_face_conductance,
                z_face_conductance,
                boundary_masks,
                i,
                k,
            )
            u = 0.5 * (q_w + q_e)
            w = 0.5 * (q_s + q_n)
            div = ((q_e - q_w) / mesh.dx_m) + ((q_n - q_s) / mesh.dz_m)
            magnitude = math.sqrt((u * u) + (w * w))

            u_row.append(u)
            w_row.append(w)
            speed_row.append(magnitude)
            divergence_row.append(div)

        raw_velocity_u.append(u_row)
        raw_velocity_w.append(w_row)
        raw_speed.append(speed_row)
        raw_divergence.append(divergence_row)

    scale_factor = q_2d / raw_inflow_per_width

    velocity_u: list[list[float]] = []
    velocity_w: list[list[float]] = []
    speed: list[list[float]] = []
    divergence: list[list[float]] = []

    max_velocity = 0.0
    max_upward_velocity = 0.0

    for i in range(mesh.nx):
        u_row: list[float] = []
        w_row: list[float] = []
        speed_row: list[float] = []
        divergence_row: list[float] = []

        for k in range(mesh.nz):
            u = raw_velocity_u[i][k] * scale_factor
            w = raw_velocity_w[i][k] * scale_factor
            div = raw_divergence[i][k] * scale_factor
            magnitude = math.sqrt((u * u) + (w * w))

            u_row.append(u)
            w_row.append(w)
            speed_row.append(magnitude)
            divergence_row.append(div)

            if magnitude > max_velocity:
                max_velocity = magnitude
            if w > max_upward_velocity:
                max_upward_velocity = w

        velocity_u.append(u_row)
        velocity_w.append(w_row)
        speed.append(speed_row)
        divergence.append(divergence_row)

    inlet_discharge_m3_s = raw_inflow_per_width * scale_factor * scenario.geometry.basin_width_m
    outlet_discharge_m3_s = raw_outflow_per_width * scale_factor * scenario.geometry.basin_width_m
    mass_balance_error = abs(inlet_discharge_m3_s - outlet_discharge_m3_s) / max(abs(inlet_discharge_m3_s), 1.0e-12)

    blocked_face_count, low_conductance_face_count = _count_face_conductance_regimes(
        x_face_conductance,
        z_face_conductance,
    )

    summary = LongitudinalSolutionSummary(
        solver_name="v0.2_steady_screening_longitudinal",
        solver_status="solved_longitudinal_screening_flow",
        solver_model=scenario.numerics.solver_model,
        iterations=iterations,
        converged=converged,
        max_head_delta=max_delta,
        inlet_discharge_m3_s=inlet_discharge_m3_s,
        outlet_discharge_m3_s=outlet_discharge_m3_s,
        mass_balance_error=mass_balance_error,
        max_velocity_m_s=max_velocity,
        max_upward_velocity_m_s=max_upward_velocity,
        blocked_face_count=blocked_face_count,
        low_conductance_face_count=low_conductance_face_count,
        supported_scope=[
            "longitudinal screening-flow comparison",
            "transition wall headloss screening",
            "plate settler and launder proxy evaluation",
            "field and artifact generation",
        ],
        notes=[
            "Implemented as a deterministic steady screening solve on a structured x-z grid.",
            "The upstream inlet loss and barrier effects are represented as conductance modifiers.",
            "The field is scaled to match the requested inlet discharge after the screening solve.",
            "Reported mass balance error is a screening-flow discharge mismatch diagnostic, not a strict conservation guarantee.",
            "RTD proxy outputs are generated from a deterministic curve derived from the steady field, not from transient transport.",
            "The model is a screening tool only and does not resolve full CFD, solids transport, or mixer blades.",
            f"Mesh sized at {mesh.nx} x {mesh.nz} cells.",
        ],
    )

    fields = LongitudinalFieldData(
        x_centers_m=[(index + 0.5) * mesh.dx_m for index in range(mesh.nx)],
        z_centers_m=[(index + 0.5) * mesh.dz_m for index in range(mesh.nz)],
        head=head,
        velocity_u_m_s=velocity_u,
        velocity_w_m_s=velocity_w,
        speed_m_s=speed,
        cell_divergence_1_per_s=divergence,
    )
    return summary, fields


def simulate_longitudinal_tracer(
    scenario: LongitudinalScenarioConfig,
    mesh: LongitudinalMeshSummary,
    fields: LongitudinalFieldData,
) -> LongitudinalTracerSummary:
    """Compute a deterministic RTD proxy from the steady longitudinal screening field.

    This is NOT a transient tracer transport simulation. It generates a synthetic
    logistic CDF breakthrough curve parameterized by field-derived quantities
    (effective travel time, velocity uniformity, dead zone fraction, headloss,
    launder upwelling). The result is a screening proxy for comparison purposes only.

    The weighting coefficients below are empirically tuned to produce RTD curves
    that are directionally consistent with the expected behavior of rectangular
    sedimentation basins under the Camp-Dobbins screening model framework
    (ref: Camp 1955, Water & Sewage Works; Tchobanoglous et al., Wastewater Engineering,
    4th ed., Table 5-5). They have not been calibrated against tracer field data for
    this specific plant and should be treated as directional proxies, not calibrated
    predictions.
    """
    theoretical_detention_time_s = (
        scenario.geometry.basin_length_m * scenario.geometry.basin_width_m * scenario.geometry.water_depth_m
    ) / scenario.hydraulics.flow_rate_m3_s
    max_time_s = scenario.performance_proxies.tracer_max_time_factor * theoretical_detention_time_s

    positive_floor = 1.0e-9
    mean_column_speeds = _column_mean_speeds(fields.velocity_u_m_s)
    effective_travel_time_s = sum(
        mesh.dx_m / max(speed, positive_floor)
        for speed in mean_column_speeds
    )
    mean_column_uniformity = _mean(
        _uniformity_index(column)
        for column in fields.velocity_u_m_s
    )
    basin_mean_speed = _mean(speed for row in fields.speed_m_s for speed in row)
    dead_zone_threshold = scenario.performance_proxies.dead_zone_velocity_fraction * basin_mean_speed
    dead_zone_fraction = _fraction_below_threshold(fields.speed_m_s, dead_zone_threshold)
    transition_headloss_m = _transition_headloss_m(scenario, mesh, fields)
    launder_peak_upward_velocity_m_s = _launder_peak_upward_velocity(scenario, mesh, fields)
    max_speed_u = max((max((abs(value) for value in row), default=0.0) for row in fields.velocity_u_m_s), default=0.0)
    max_speed_w = max((max((abs(value) for value in row), default=0.0) for row in fields.velocity_w_m_s), default=0.0)
    max_speed = max(max_speed_u, max_speed_w)
    headloss_factor = max(0.0, transition_headloss_m / max(scenario.geometry.water_depth_m, positive_floor))
    upward_factor = launder_peak_upward_velocity_m_s / max(max_speed, positive_floor)

    # t50 floor: basin cannot short-circuit to t50 below 25% of theoretical detention
    # time regardless of field conditions. Headloss factor adds delay proportional to
    # transition wall resistance (0.12 is empirically tuned; see function docstring).
    nominal_t50_s = max(
        0.25 * theoretical_detention_time_s,
        effective_travel_time_s * (1.0 + (0.12 * headloss_factor)),
    )
    # Spread fraction controls RTD curve width (higher = broader, more dispersed curve).
    # Each term contributes a field-derived penalty:
    #   0.10  — base spread: minimum turbulent dispersion in any real basin
    #   0.30  — velocity non-uniformity penalty (column-to-column speed variation)
    #   0.22  — dead zone penalty (stagnant volume fraction)
    #   0.08  — transition headloss penalty (wall resistance forcing bypass redistribution)
    #   0.05  — launder upwelling penalty (high upward velocity implies concentrated exit)
    # Weights are empirically tuned proxies; see function docstring for basis.
    spread_fraction = (
        0.10
        + (0.30 * (1.0 - mean_column_uniformity))
        + (0.22 * dead_zone_fraction)
        + (0.08 * headloss_factor)
        + (0.05 * upward_factor)
    )
    # Clamp spread fraction: 0.08 prevents an unrealistically sharp curve even in
    # near-ideal basins; 0.40 caps dispersion to avoid non-physical flat RTDs.
    spread_fraction = max(0.08, min(0.40, spread_fraction))

    sample_count = max(101, min(241, scenario.numerics.nx * 2))
    if max_time_s <= 0.0:
        raise ValueError("computed tracer time horizon must be positive")

    time_points = [
        (index / (sample_count - 1)) * max_time_s
        for index in range(sample_count)
    ]
    t50_fraction = nominal_t50_s / max_time_s
    # Clamp t50 position within the time window: 0.20–0.80 keeps the logistic CDF
    # inflection point well inside the sampled interval so t10/t50/t90 are all
    # resolvable from the generated curve.
    t50_fraction = max(0.20, min(0.80, t50_fraction))
    center_s = t50_fraction * max_time_s
    # Steepness controls the slope of the logistic CDF at the inflection point.
    # Base value 5.0 gives a moderately broad curve; the spread-fraction term
    # (range 0–6.0) sharpens the curve as spread_fraction decreases toward 0.08.
    # Empirically tuned; see function docstring.
    steepness = 5.0 + (6.0 * (1.0 - spread_fraction))
    outlet_history = _normalized_sigmoid_history(time_points, center_s, max_time_s, steepness)
    monotonic_history = _cumulative_max(outlet_history)
    t10_s = _crossing_time(time_points, monotonic_history, 0.10)
    t50_s = _crossing_time(time_points, monotonic_history, 0.50)
    t90_s = _crossing_time(time_points, monotonic_history, 0.90)
    final_outlet_concentration = outlet_history[-1]
    terminated_by_target = final_outlet_concentration >= scenario.performance_proxies.tracer_target_fraction

    return LongitudinalTracerSummary(
        time_points_s=time_points,
        outlet_concentration_history=outlet_history,
        t10_s=t10_s,
        t50_s=t50_s,
        t90_s=t90_s,
        final_time_s=time_points[-1],
        final_outlet_concentration=final_outlet_concentration,
        converged=terminated_by_target,
        termination_reason="rtd_proxy_target_fraction_reached" if terminated_by_target else "rtd_proxy_time_horizon_reached",
        step_count=len(time_points) - 1,
        notes=[
            "Deterministic RTD proxy generated from the steady longitudinal screening field.",
            "The breakthrough curve is a synthetic logistic CDF parameterized by field-derived travel time and spread.",
            "This output is for screening comparisons only and is not a transient transport solve.",
        ],
    )


def _build_face_conductances(
    scenario: LongitudinalScenarioConfig,
    mesh: LongitudinalMeshSummary,
) -> tuple[list[list[float]], list[list[float]], _BoundaryMasks]:
    x_face_conductance = [[1.0 for _ in range(mesh.nz)] for _ in range(mesh.nx + 1)]
    z_face_conductance = [[1.0 for _ in range(mesh.nz + 1)] for _ in range(mesh.nx)]
    boundary_masks = _build_boundary_masks(scenario, mesh)

    for k in range(mesh.nz):
        x_face_conductance[0][k] = boundary_masks.inlet_row_scale[k]
        x_face_conductance[mesh.nx][k] = 0.0

    for i in range(mesh.nx):
        z_face_conductance[i][0] = 0.0
        z_face_conductance[i][mesh.nz] = boundary_masks.launder_col_scale[i]

    _apply_upstream_taper(scenario, mesh, x_face_conductance)
    _apply_feature_conductance_modifiers(scenario, mesh, x_face_conductance, z_face_conductance)

    return x_face_conductance, z_face_conductance, boundary_masks


def _build_boundary_masks(
    scenario: LongitudinalScenarioConfig,
    mesh: LongitudinalMeshSummary,
) -> _BoundaryMasks:
    inlet_lower = scenario.upstream.inlet_zone_center_elevation_m - (scenario.upstream.inlet_zone_height_m / 2.0)
    inlet_upper = scenario.upstream.inlet_zone_center_elevation_m + (scenario.upstream.inlet_zone_height_m / 2.0)
    active_rows = max(1.0, scenario.upstream.inlet_zone_height_m / mesh.dz_m)
    inlet_scale = min(1.0, scenario.upstream.inlet_orifice_count / active_rows) / (1.0 + scenario.upstream.inlet_loss_coefficient)

    inlet_row_scale = []
    for k in range(mesh.nz):
        cell_lower = k * mesh.dz_m
        cell_upper = (k + 1) * mesh.dz_m
        overlap = _interval_overlap_fraction(cell_lower, cell_upper, inlet_lower, inlet_upper)
        inlet_row_scale.append(max(0.0, overlap * inlet_scale))

    launder_col_scale = [0.0 for _ in range(mesh.nx)]
    for feature in scenario.features:
        if isinstance(feature, LaunderZoneFeatureConfig):
            for i in range(mesh.nx):
                cell_lower = i * mesh.dx_m
                cell_upper = (i + 1) * mesh.dx_m
                overlap = _interval_overlap_fraction(cell_lower, cell_upper, feature.x_start_m, feature.x_end_m)
                launder_col_scale[i] = max(launder_col_scale[i], overlap * feature.sink_weight)

    return _BoundaryMasks(inlet_row_scale=inlet_row_scale, launder_col_scale=launder_col_scale)


def _apply_upstream_taper(
    scenario: LongitudinalScenarioConfig,
    mesh: LongitudinalMeshSummary,
    x_face_conductance: list[list[float]],
) -> None:
    mixing_length = scenario.upstream.mixing_zone_length_m
    if mixing_length <= 0.0:
        return

    for i in range(1, mesh.nx):
        x_position = i * mesh.dx_m
        if x_position > mixing_length:
            continue
        relative = max(0.0, 1.0 - (x_position / mixing_length))
        taper = 1.0 / (1.0 + (scenario.upstream.mixing_intensity_factor * relative))
        for k in range(mesh.nz):
            x_face_conductance[i][k] *= taper


def _apply_feature_conductance_modifiers(
    scenario: LongitudinalScenarioConfig,
    mesh: LongitudinalMeshSummary,
    x_face_conductance: list[list[float]],
    z_face_conductance: list[list[float]],
) -> None:
    for feature in scenario.features:
        if isinstance(feature, PerforatedBaffleFeatureConfig):
            feature_conductance = _perforated_baffle_conductance(feature.open_area_fraction, feature.loss_scale)
            face_index = _nearest_internal_x_face(feature.x_m, mesh.dx_m, mesh.nx)
            for k in range(mesh.nz):
                row_lower = k * mesh.dz_m
                row_upper = (k + 1) * mesh.dz_m
                overlap = _interval_overlap_fraction(row_lower, row_upper, feature.z_bottom_m, feature.z_top_m)
                if overlap <= 0.0:
                    continue
                modifier = (1.0 - overlap) + (overlap * feature_conductance)
                x_face_conductance[face_index][k] *= modifier
            continue

        if isinstance(feature, SolidBaffleFeatureConfig):
            face_index = _nearest_internal_x_face(feature.x_m, mesh.dx_m, mesh.nx)
            for k in range(mesh.nz):
                row_lower = k * mesh.dz_m
                row_upper = (k + 1) * mesh.dz_m
                overlap = _interval_overlap_fraction(row_lower, row_upper, feature.z_bottom_m, feature.z_top_m)
                if overlap <= 0.0:
                    continue
                modifier = 1.0 - overlap
                x_face_conductance[face_index][k] *= modifier
            continue

        if isinstance(feature, PlateSettlerZoneFeatureConfig):
            void_fraction = feature.plate_spacing_m / (feature.plate_spacing_m + feature.plate_thickness_m)
            # Conductance floors prevent zero-conductance cells that stall the
            # Gauss-Seidel solve. 0.02 (parallel) and 0.005 (perpendicular) are
            # practical minimums empirically chosen to keep the solver convergent
            # for high-resistance plate configurations; they are not physically
            # derived from plate geometry.
            k_parallel = max(0.02, void_fraction / feature.resistance_scale)
            k_perp = max(0.005, k_parallel * feature.cross_flow_factor)
            theta = math.radians(feature.plate_angle_deg)
            cos_theta = math.cos(theta)
            sin_theta = math.sin(theta)
            kx = (k_parallel * cos_theta * cos_theta) + (k_perp * sin_theta * sin_theta)
            kz = (k_parallel * sin_theta * sin_theta) + (k_perp * cos_theta * cos_theta)

            for i in range(1, mesh.nx):
                x_position = i * mesh.dx_m
                if not (feature.x_start_m <= x_position <= feature.x_end_m):
                    continue
                x_fraction = _interval_overlap_fraction(
                    (i - 1) * mesh.dx_m,
                    i * mesh.dx_m,
                    feature.x_start_m,
                    feature.x_end_m,
                )
                for k in range(mesh.nz):
                    row_lower = k * mesh.dz_m
                    row_upper = (k + 1) * mesh.dz_m
                    z_fraction = _interval_overlap_fraction(row_lower, row_upper, feature.z_bottom_m, feature.z_top_m)
                    overlap = min(x_fraction, z_fraction)
                    if overlap <= 0.0:
                        continue
                    x_modifier = (1.0 - overlap) + (overlap * kx)
                    x_face_conductance[i][k] *= x_modifier

            for i in range(mesh.nx):
                cell_lower = i * mesh.dx_m
                cell_upper = (i + 1) * mesh.dx_m
                x_fraction = _interval_overlap_fraction(cell_lower, cell_upper, feature.x_start_m, feature.x_end_m)
                if x_fraction <= 0.0:
                    continue
                for k in range(1, mesh.nz):
                    face_lower = k * mesh.dz_m
                    face_upper = (k + 1) * mesh.dz_m
                    z_fraction = _interval_overlap_fraction(face_lower, face_upper, feature.z_bottom_m, feature.z_top_m)
                    overlap = min(x_fraction, z_fraction)
                    if overlap <= 0.0:
                        continue
                    z_modifier = (1.0 - overlap) + (overlap * kz)
                    z_face_conductance[i][k] *= z_modifier


def _solve_head_field(
    scenario: LongitudinalScenarioConfig,
    mesh: LongitudinalMeshSummary,
    head: list[list[float]],
    x_face_conductance: list[list[float]],
    z_face_conductance: list[list[float]],
    boundary_masks: _BoundaryMasks,
) -> tuple[int, bool, float]:
    max_delta = 0.0
    converged = False
    iterations = 0

    for iteration in range(1, scenario.numerics.max_iterations + 1):
        max_delta = 0.0

        for i in range(mesh.nx):
            for k in range(mesh.nz):
                total_coef = 0.0
                rhs = 0.0

                total_coef, rhs = _accumulate_x_contribution(
                    scenario,
                    mesh,
                    head,
                    x_face_conductance,
                    boundary_masks,
                    i,
                    k,
                    side="west",
                    total_coef=total_coef,
                    rhs=rhs,
                )
                total_coef, rhs = _accumulate_x_contribution(
                    scenario,
                    mesh,
                    head,
                    x_face_conductance,
                    boundary_masks,
                    i,
                    k,
                    side="east",
                    total_coef=total_coef,
                    rhs=rhs,
                )
                total_coef, rhs = _accumulate_z_contribution(
                    scenario,
                    mesh,
                    head,
                    z_face_conductance,
                    boundary_masks,
                    i,
                    k,
                    side="south",
                    total_coef=total_coef,
                    rhs=rhs,
                )
                total_coef, rhs = _accumulate_z_contribution(
                    scenario,
                    mesh,
                    head,
                    z_face_conductance,
                    boundary_masks,
                    i,
                    k,
                    side="north",
                    total_coef=total_coef,
                    rhs=rhs,
                )

                if total_coef <= 0.0:
                    continue

                candidate = rhs / total_coef
                updated = ((1.0 - scenario.numerics.relaxation_factor) * head[i][k]) + (
                    scenario.numerics.relaxation_factor * candidate
                )
                delta = abs(updated - head[i][k])
                head[i][k] = updated
                if delta > max_delta:
                    max_delta = delta

        iterations = iteration
        if max_delta <= scenario.numerics.tolerance:
            converged = True
            break

    return iterations, converged, max_delta


def _accumulate_x_contribution(
    scenario: LongitudinalScenarioConfig,
    mesh: LongitudinalMeshSummary,
    head: list[list[float]],
    x_face_conductance: list[list[float]],
    boundary_masks: _BoundaryMasks,
    i: int,
    k: int,
    *,
    side: str,
    total_coef: float,
    rhs: float,
) -> tuple[float, float]:
    if side == "west":
        if i > 0:
            conductance = x_face_conductance[i][k]
            coef = conductance / mesh.dx_m
            return total_coef + coef, rhs + (coef * head[i - 1][k])
        if boundary_masks.inlet_row_scale[k] > 0.0:
            conductance = x_face_conductance[0][k]
            coef = (2.0 * conductance) / mesh.dx_m
            return total_coef + coef, rhs + coef * 1.0
        return total_coef, rhs

    if i < mesh.nx - 1:
        conductance = x_face_conductance[i + 1][k]
        coef = conductance / mesh.dx_m
        return total_coef + coef, rhs + (coef * head[i + 1][k])
    return total_coef, rhs


def _accumulate_z_contribution(
    scenario: LongitudinalScenarioConfig,
    mesh: LongitudinalMeshSummary,
    head: list[list[float]],
    z_face_conductance: list[list[float]],
    boundary_masks: _BoundaryMasks,
    i: int,
    k: int,
    *,
    side: str,
    total_coef: float,
    rhs: float,
) -> tuple[float, float]:
    if side == "south":
        if k > 0:
            conductance = z_face_conductance[i][k]
            coef = conductance / mesh.dz_m
            return total_coef + coef, rhs + (coef * head[i][k - 1])
        return total_coef, rhs

    if k < mesh.nz - 1:
        conductance = z_face_conductance[i][k + 1]
        coef = conductance / mesh.dz_m
        return total_coef + coef, rhs + (coef * head[i][k + 1])

    if boundary_masks.launder_col_scale[i] > 0.0:
        conductance = z_face_conductance[i][mesh.nz]
        coef = (2.0 * conductance) / mesh.dz_m
        return total_coef + coef, rhs + coef * 0.0
    return total_coef, rhs


def _boundary_discharge_per_width(
    mesh: LongitudinalMeshSummary,
    head: list[list[float]],
    x_face_conductance: list[list[float]],
    z_face_conductance: list[list[float]],
    boundary_masks: _BoundaryMasks,
    *,
    side: str,
) -> float:
    total = 0.0
    if side == "west":
        for k in range(mesh.nz):
            if boundary_masks.inlet_row_scale[k] <= 0.0:
                continue
            conductance = x_face_conductance[0][k]
            flux = conductance * (1.0 - head[0][k]) / (0.5 * mesh.dx_m)
            total += flux * mesh.dz_m
        return total

    for i in range(mesh.nx):
        if boundary_masks.launder_col_scale[i] <= 0.0:
            continue
        conductance = z_face_conductance[i][mesh.nz]
        flux = conductance * (head[i][mesh.nz - 1] - 0.0) / (0.5 * mesh.dz_m)
        total += flux * mesh.dx_m
    return total


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


def _column_mean_speeds(velocity_u_m_s: list[list[float]]) -> list[float]:
    if not velocity_u_m_s:
        return []
    nx = len(velocity_u_m_s)
    nz = len(velocity_u_m_s[0]) if velocity_u_m_s[0] else 0
    if nz <= 0:
        return [0.0 for _ in range(nx)]
    return [
        sum(abs(value) for value in column) / len(column)
        for column in velocity_u_m_s
    ]


def _fraction_below_threshold(speed_field: list[list[float]], threshold: float) -> float:
    total_count = sum(len(row) for row in speed_field)
    if total_count <= 0:
        return 0.0
    below_count = sum(1 for row in speed_field for value in row if value < threshold)
    return below_count / total_count


def _launder_peak_upward_velocity(
    scenario: LongitudinalScenarioConfig,
    mesh: LongitudinalMeshSummary,
    fields: LongitudinalFieldData,
) -> float:
    values: list[float] = []
    for feature in scenario.features:
        if not isinstance(feature, LaunderZoneFeatureConfig):
            continue
        for i in range(mesh.nx):
            cell_lower = i * mesh.dx_m
            cell_upper = (i + 1) * mesh.dx_m
            overlap = _interval_overlap_fraction(cell_lower, cell_upper, feature.x_start_m, feature.x_end_m)
            if overlap <= 0.0:
                continue
            values.append(max(0.0, fields.velocity_w_m_s[i][-1]))
    return max(values, default=0.0)


def _uniformity_index(column: list[float]) -> float:
    magnitudes = [abs(value) for value in column]
    max_magnitude = max(magnitudes, default=0.0)
    if max_magnitude <= 0.0:
        return 0.0
    return _mean(magnitudes) / max_magnitude


def _mean(values: Iterable[float]) -> float:
    total = 0.0
    count = 0
    for value in values:
        total += value
        count += 1
    return total / count if count > 0 else 0.0


def _logistic_cdf(time_s: float, center_s: float, scale_s: float) -> float:
    if scale_s <= 0.0:
        return 1.0 if time_s >= center_s else 0.0
    z = (time_s - center_s) / scale_s
    if z >= 60.0:
        return 1.0
    if z <= -60.0:
        return 0.0
    return 1.0 / (1.0 + math.exp(-z))


def _normalized_sigmoid_history(
    time_points_s: list[float],
    center_s: float,
    horizon_s: float,
    steepness: float,
) -> list[float]:
    if not time_points_s:
        return []
    if horizon_s <= 0.0:
        return [0.0 for _ in time_points_s]

    normalized_center = center_s / horizon_s
    raw_values = [
        _sigmoid(steepness * ((time_s / horizon_s) - normalized_center))
        for time_s in time_points_s
    ]
    start = raw_values[0]
    end = raw_values[-1]
    span = max(end - start, 1.0e-12)
    return [_clamp((value - start) / span, 0.0, 1.0) for value in raw_values]


def _sigmoid(x: float) -> float:
    if x >= 60.0:
        return 1.0
    if x <= -60.0:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


def _cell_face_fluxes(
    mesh: LongitudinalMeshSummary,
    head: list[list[float]],
    x_face_conductance: list[list[float]],
    z_face_conductance: list[list[float]],
    boundary_masks: _BoundaryMasks,
    i: int,
    k: int,
) -> tuple[float, float, float, float]:
    if i > 0:
        q_w = x_face_conductance[i][k] * (head[i - 1][k] - head[i][k]) / mesh.dx_m
    elif boundary_masks.inlet_row_scale[k] > 0.0:
        q_w = x_face_conductance[0][k] * (1.0 - head[0][k]) / (0.5 * mesh.dx_m)
    else:
        q_w = 0.0

    if i < mesh.nx - 1:
        q_e = x_face_conductance[i + 1][k] * (head[i][k] - head[i + 1][k]) / mesh.dx_m
    else:
        q_e = 0.0

    if k > 0:
        q_s = z_face_conductance[i][k] * (head[i][k - 1] - head[i][k]) / mesh.dz_m
    else:
        q_s = 0.0

    if k < mesh.nz - 1:
        q_n = z_face_conductance[i][k + 1] * (head[i][k] - head[i][k + 1]) / mesh.dz_m
    elif boundary_masks.launder_col_scale[i] > 0.0:
        q_n = z_face_conductance[i][mesh.nz] * (head[i][mesh.nz - 1] - 0.0) / (0.5 * mesh.dz_m)
    else:
        q_n = 0.0

    return q_w, q_e, q_s, q_n


def _advective_flux_x(
    fields: LongitudinalFieldData,
    concentration: list[list[float]],
    boundary_masks: _BoundaryMasks,
    mesh: LongitudinalMeshSummary,
    i: int,
    k: int,
    *,
    face: str,
) -> float:
    if face == "west":
        face_velocity = fields.velocity_u_m_s[i][k] if i == 0 else 0.5 * (fields.velocity_u_m_s[i - 1][k] + fields.velocity_u_m_s[i][k])
        if i == 0:
            if boundary_masks.inlet_row_scale[k] > 0.0 and face_velocity > 0.0:
                return face_velocity * 1.0
            return face_velocity * concentration[i][k]
        if face_velocity > 0.0:
            return face_velocity * concentration[i - 1][k]
        return face_velocity * concentration[i][k]

    if i == mesh.nx - 1:
        return 0.0

    face_velocity = 0.5 * (fields.velocity_u_m_s[i][k] + fields.velocity_u_m_s[i + 1][k])
    if face_velocity > 0.0:
        return face_velocity * concentration[i][k]
    return face_velocity * concentration[i + 1][k]


def _advective_flux_z(
    fields: LongitudinalFieldData,
    concentration: list[list[float]],
    boundary_masks: _BoundaryMasks,
    mesh: LongitudinalMeshSummary,
    i: int,
    k: int,
    *,
    face: str,
) -> float:
    if face == "south":
        if k == 0:
            return 0.0
        face_velocity = 0.5 * (fields.velocity_w_m_s[i][k - 1] + fields.velocity_w_m_s[i][k])
        if face_velocity > 0.0:
            return face_velocity * concentration[i][k - 1]
        return face_velocity * concentration[i][k]

    if k == mesh.nz - 1:
        if boundary_masks.launder_col_scale[i] <= 0.0:
            return 0.0
        face_velocity = fields.velocity_w_m_s[i][k]
        if face_velocity > 0.0:
            return face_velocity * concentration[i][k]
        return face_velocity * 0.0

    face_velocity = 0.5 * (fields.velocity_w_m_s[i][k] + fields.velocity_w_m_s[i][k + 1])
    if face_velocity > 0.0:
        return face_velocity * concentration[i][k]
    return face_velocity * concentration[i][k + 1]


def _diffusion_x(concentration: list[list[float]], mesh: LongitudinalMeshSummary, i: int, k: int) -> float:
    current = concentration[i][k]
    left = concentration[i - 1][k] if i > 0 else current
    right = concentration[i + 1][k] if i < mesh.nx - 1 else current
    return (left - (2.0 * current) + right) / (mesh.dx_m * mesh.dx_m)


def _diffusion_z(concentration: list[list[float]], mesh: LongitudinalMeshSummary, i: int, k: int) -> float:
    current = concentration[i][k]
    lower = concentration[i][k - 1] if k > 0 else current
    upper = concentration[i][k + 1] if k < mesh.nz - 1 else current
    return (lower - (2.0 * current) + upper) / (mesh.dz_m * mesh.dz_m)


def _launder_outlet_concentration(
    concentration: list[list[float]],
    boundary_masks: _BoundaryMasks,
) -> float:
    total = 0.0
    count = 0
    for i, scale in enumerate(boundary_masks.launder_col_scale):
        if scale <= 0.0:
            continue
        total += concentration[i][-1]
        count += 1
    return total / count if count > 0 else 0.0


def _initial_head_guess(mesh: LongitudinalMeshSummary) -> list[list[float]]:
    head: list[list[float]] = []
    x_denominator = max(mesh.nx - 1, 1)
    z_denominator = max(mesh.nz - 1, 1)
    for i in range(mesh.nx):
        row: list[float] = []
        x_fraction = i / x_denominator
        for k in range(mesh.nz):
            z_fraction = k / z_denominator
            value = 1.0 - (0.75 * x_fraction) - (0.25 * z_fraction)
            row.append(_clamp(value, 0.0, 1.0))
        head.append(row)
    return head


def _perforated_baffle_conductance(open_area_fraction: float, loss_scale: float) -> float:
    phi = open_area_fraction
    # 0.707 is 1/sqrt(2), the classical vena contracta coefficient for sharp-edged orifices
    orifice_coefficient = 0.707
    k = ((orifice_coefficient * ((1.0 - phi) ** 0.375)) + 1.0 - (phi * phi)) ** 2 / (phi * phi)
    return max(1.0e-6, phi / (1.0 + (loss_scale * k)))


def _nearest_internal_x_face(x_m: float, dx_m: float, nx: int) -> int:
    face_index = int(round(x_m / dx_m))
    return min(max(face_index, 1), nx - 1)


def _interval_overlap_fraction(lower_a: float, upper_a: float, lower_b: float, upper_b: float) -> float:
    overlap = min(upper_a, upper_b) - max(lower_a, lower_b)
    if overlap <= 0.0:
        return 0.0
    width = upper_a - lower_a
    return overlap / width if width > 0.0 else 0.0


def _count_face_conductance_regimes(
    x_face_conductance: list[list[float]],
    z_face_conductance: list[list[float]],
) -> tuple[int, int]:
    blocked = 0
    low = 0
    for face_row in x_face_conductance[1:-1]:
        for value in face_row:
            if value <= 1.0e-6:
                blocked += 1
            if value < 0.2:
                low += 1
    for face_row in z_face_conductance:
        for value in face_row[1:-1]:
            if value <= 1.0e-6:
                blocked += 1
            if value < 0.2:
                low += 1
    return blocked, low


def _crossing_time(time_points: list[float], values: list[float], target: float) -> float:
    if not time_points:
        return 0.0
    if values[0] >= target:
        return time_points[0]
    for index in range(1, len(values)):
        previous_value = values[index - 1]
        current_value = values[index]
        if current_value < target:
            continue
        previous_time = time_points[index - 1]
        current_time = time_points[index]
        if current_value == previous_value:
            return current_time
        fraction = (target - previous_value) / (current_value - previous_value)
        return previous_time + fraction * (current_time - previous_time)
    return time_points[-1]


def _cumulative_max(values: list[float]) -> list[float]:
    result: list[float] = []
    current = float("-inf")
    for value in values:
        current = max(current, value)
        result.append(current)
    return result


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
