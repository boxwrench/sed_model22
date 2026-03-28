from __future__ import annotations

import math
from pathlib import Path

from ..config import PlanViewScenarioConfig
from ..solver import HydraulicFieldData


def build_plan_view_streamline_svg(
    scenario: PlanViewScenarioConfig,
    fields: HydraulicFieldData,
) -> str:
    margin = 40
    basin_width_px = 960
    basin_height_px = max(240, int(basin_width_px * (scenario.geometry.width_m / scenario.geometry.length_m)))
    svg_width = basin_width_px + margin * 2
    svg_height = basin_height_px + margin * 2 + 80

    def sx(x_m: float) -> float:
        return margin + (x_m / scenario.geometry.length_m) * basin_width_px

    def sy(y_m: float) -> float:
        return margin + basin_height_px - (y_m / scenario.geometry.width_m) * basin_height_px

    max_speed = max(max(row) for row in fields.speed_m_s)
    if max_speed <= 0.0:
        max_speed = 1.0

    streamlines: list[str] = []
    for seed_index, (seed_x, seed_y) in enumerate(_streamline_seeds(scenario)):
        path = _trace_streamline(scenario, fields, seed_x, seed_y)
        if len(path) < 2:
            continue
        path_d = " ".join(
            f"{'M' if index == 0 else 'L'} {sx(x_m):.2f} {sy(y_m):.2f}"
            for index, (x_m, y_m, _speed) in enumerate(path)
        )
        mean_speed = sum(point[2] for point in path) / len(path)
        streamlines.append(
            f"  <path d='{path_d}' fill='none' stroke='{_speed_color(mean_speed / max_speed)}' stroke-width='2.2' stroke-linecap='round' opacity='0.92' />"
        )

    baffles = []
    for baffle in scenario.baffles:
        baffles.append(
            "  "
            f"<line x1='{sx(baffle.x1_m):.1f}' y1='{sy(baffle.y1_m):.1f}' "
            f"x2='{sx(baffle.x2_m):.1f}' y2='{sy(baffle.y2_m):.1f}' "
            "stroke='#0f172a' stroke-width='5' />"
        )

    inlet_lower = scenario.inlet.center_m - (scenario.inlet.span_m / 2.0)
    inlet_upper = scenario.inlet.center_m + (scenario.inlet.span_m / 2.0)
    outlet_lower = scenario.outlet.center_m - (scenario.outlet.span_m / 2.0)
    outlet_upper = scenario.outlet.center_m + (scenario.outlet.span_m / 2.0)

    return "\n".join(
        [
            f"<svg xmlns='http://www.w3.org/2000/svg' width='{svg_width}' height='{svg_height}' viewBox='0 0 {svg_width} {svg_height}'>",
            "  <rect width='100%' height='100%' fill='#f8fafc' />",
            f"  <text x='{margin}' y='24' font-family='monospace' font-size='20' fill='#0f172a'>{scenario.metadata.title} streamlines</text>",
            f"  <text x='{margin}' y='46' font-family='monospace' font-size='12' fill='#334155'>Deterministic streamlines from steady screening field</text>",
            f"  <rect x='{margin}' y='{margin}' width='{basin_width_px}' height='{basin_height_px}' fill='#e0f2fe' stroke='#0f172a' stroke-width='3' />",
            *streamlines,
            *baffles,
            f"  <line x1='{sx(0.0):.1f}' y1='{sy(inlet_lower):.1f}' x2='{sx(0.0):.1f}' y2='{sy(inlet_upper):.1f}' stroke='#16a34a' stroke-width='8' />",
            f"  <line x1='{sx(scenario.geometry.length_m):.1f}' y1='{sy(outlet_lower):.1f}' x2='{sx(scenario.geometry.length_m):.1f}' y2='{sy(outlet_upper):.1f}' stroke='#dc2626' stroke-width='8' />",
            f"  <text x='{margin}' y='{svg_height - 36}' font-family='monospace' font-size='12' fill='#334155'>Directional screening figure from a steady field. Not transient CFD.</text>",
            f"  <text x='{margin}' y='{svg_height - 18}' font-family='monospace' font-size='12' fill='#334155'>Cool colors are slower. Warm colors are faster.</text>",
            "</svg>",
        ]
    )


def write_plan_view_streamline_svg(
    scenario: PlanViewScenarioConfig,
    fields: HydraulicFieldData,
    output_path: str | Path,
) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(build_plan_view_streamline_svg(scenario, fields), encoding="utf-8")
    return destination


def _streamline_seeds(scenario: PlanViewScenarioConfig) -> list[tuple[float, float]]:
    inlet_lower = scenario.inlet.center_m - (scenario.inlet.span_m / 2.0)
    inlet_upper = scenario.inlet.center_m + (scenario.inlet.span_m / 2.0)
    seed_count = 18
    x_seed = max(1.0e-4, 0.012 * scenario.geometry.length_m)
    seeds = []
    for index in range(seed_count):
        fraction = index / max(seed_count - 1, 1)
        y_seed = inlet_lower + fraction * (inlet_upper - inlet_lower)
        seeds.append((x_seed, y_seed))
    return seeds


def _trace_streamline(
    scenario: PlanViewScenarioConfig,
    fields: HydraulicFieldData,
    seed_x: float,
    seed_y: float,
) -> list[tuple[float, float, float]]:
    points: list[tuple[float, float, float]] = []
    x_m = seed_x
    y_m = seed_y
    dt_s = _stable_time_step_s(scenario, fields)

    for _ in range(260):
        u_m_s, v_m_s = _sample_velocity(fields, scenario, x_m, y_m)
        speed_m_s = math.sqrt((u_m_s * u_m_s) + (v_m_s * v_m_s))
        if speed_m_s <= 1.0e-9:
            break
        points.append((x_m, y_m, speed_m_s))
        next_x = x_m + (dt_s * u_m_s)
        next_y = y_m + (dt_s * v_m_s)
        if not (0.0 <= next_x <= scenario.geometry.length_m and 0.0 <= next_y <= scenario.geometry.width_m):
            break
        if _hits_baffle(scenario, next_x, next_y):
            break
        x_m = next_x
        y_m = next_y
    return points


def _stable_time_step_s(scenario: PlanViewScenarioConfig, fields: HydraulicFieldData) -> float:
    nx = max(1, len(fields.x_centers_m))
    ny = max(1, len(fields.y_centers_m))
    dx_m = scenario.geometry.length_m / nx
    dy_m = scenario.geometry.width_m / ny
    max_speed = max(max(row) for row in fields.speed_m_s)
    if max_speed <= 1.0e-9:
        return 0.5
    return max(0.05, min(0.75, 0.75 * min(dx_m, dy_m) / max_speed))


def _sample_velocity(
    fields: HydraulicFieldData,
    scenario: PlanViewScenarioConfig,
    x_m: float,
    y_m: float,
) -> tuple[float, float]:
    nx = len(fields.x_centers_m)
    ny = len(fields.y_centers_m)
    if nx <= 0 or ny <= 0:
        return 0.0, 0.0

    dx_m = scenario.geometry.length_m / nx
    dy_m = scenario.geometry.width_m / ny
    x_scaled = (x_m / dx_m) - 0.5
    y_scaled = (y_m / dy_m) - 0.5
    i0 = max(0, min(nx - 1, int(math.floor(x_scaled))))
    j0 = max(0, min(ny - 1, int(math.floor(y_scaled))))
    i1 = max(0, min(nx - 1, i0 + 1))
    j1 = max(0, min(ny - 1, j0 + 1))
    tx = max(0.0, min(1.0, x_scaled - i0))
    ty = max(0.0, min(1.0, y_scaled - j0))

    u00 = fields.velocity_u_m_s[i0][j0]
    u10 = fields.velocity_u_m_s[i1][j0]
    u01 = fields.velocity_u_m_s[i0][j1]
    u11 = fields.velocity_u_m_s[i1][j1]
    v00 = fields.velocity_v_m_s[i0][j0]
    v10 = fields.velocity_v_m_s[i1][j0]
    v01 = fields.velocity_v_m_s[i0][j1]
    v11 = fields.velocity_v_m_s[i1][j1]

    u0 = u00 * (1.0 - tx) + u10 * tx
    u1 = u01 * (1.0 - tx) + u11 * tx
    v0 = v00 * (1.0 - tx) + v10 * tx
    v1 = v01 * (1.0 - tx) + v11 * tx
    return u0 * (1.0 - ty) + u1 * ty, v0 * (1.0 - ty) + v1 * ty


def _hits_baffle(scenario: PlanViewScenarioConfig, x_m: float, y_m: float) -> bool:
    for baffle in scenario.baffles:
        if baffle.x1_m == baffle.x2_m:
            if abs(x_m - baffle.x1_m) <= 0.12 and min(baffle.y1_m, baffle.y2_m) <= y_m <= max(baffle.y1_m, baffle.y2_m):
                return True
        elif abs(y_m - baffle.y1_m) <= 0.12 and min(baffle.x1_m, baffle.x2_m) <= x_m <= max(baffle.x1_m, baffle.x2_m):
            return True
    return False


def _speed_color(normalized_speed: float) -> str:
    value = max(0.0, min(1.0, normalized_speed))
    red = int(44 + (183 * value))
    green = int(103 + (82 * (1.0 - value)))
    blue = int(242 - (165 * value))
    return f"#{red:02x}{green:02x}{blue:02x}"
