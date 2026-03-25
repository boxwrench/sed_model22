from __future__ import annotations

from pathlib import Path

from ..config import OpeningConfig, ScenarioConfig
from ..solver import HydraulicFieldData


def build_layout_svg(scenario: ScenarioConfig) -> str:
    margin = 40
    basin_width_px = 960
    basin_height_px = max(240, int(basin_width_px * (scenario.geometry.width_m / scenario.geometry.length_m)))
    svg_width = basin_width_px + margin * 2
    svg_height = basin_height_px + margin * 2 + 60

    def sx(x_m: float) -> float:
        return margin + (x_m / scenario.geometry.length_m) * basin_width_px

    def sy(y_m: float) -> float:
        return margin + basin_height_px - (y_m / scenario.geometry.width_m) * basin_height_px

    return "\n".join(
        [
            f"<svg xmlns='http://www.w3.org/2000/svg' width='{svg_width}' height='{svg_height}' viewBox='0 0 {svg_width} {svg_height}'>",
            "  <rect width='100%' height='100%' fill='#f8fafc' />",
            f"  <text x='{margin}' y='24' font-family='monospace' font-size='20' fill='#0f172a'>{scenario.metadata.title}</text>",
            f"  <text x='{margin}' y='46' font-family='monospace' font-size='12' fill='#334155'>Case: {scenario.metadata.case_id}</text>",
            f"  <rect x='{margin}' y='{margin}' width='{basin_width_px}' height='{basin_height_px}' fill='#dbeafe' stroke='#0f172a' stroke-width='3' />",
            _opening_svg_line(scenario.inlet, scenario, sx, sy, stroke="#16a34a"),
            _opening_svg_line(scenario.outlet, scenario, sx, sy, stroke="#dc2626"),
            *_baffle_svg_lines(scenario, sx, sy),
            f"  <text x='{margin}' y='{svg_height - 18}' font-family='monospace' font-size='12' fill='#334155'>Basin: {scenario.geometry.length_m:.1f} m x {scenario.geometry.width_m:.1f} m x {scenario.geometry.water_depth_m:.1f} m</text>",
            "</svg>",
        ]
    )


def write_layout_svg(scenario: ScenarioConfig, output_path: str | Path) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(build_layout_svg(scenario), encoding="utf-8")
    return destination


def build_velocity_heatmap_svg(scenario: ScenarioConfig, fields: HydraulicFieldData) -> str:
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

    dx_px = basin_width_px / len(fields.x_centers_m)
    dy_px = basin_height_px / len(fields.y_centers_m)

    rects: list[str] = []
    for i, x_center in enumerate(fields.x_centers_m):
        for j, y_center in enumerate(fields.y_centers_m):
            speed = fields.speed_m_s[i][j]
            color = _speed_color(speed / max_speed)
            x = sx(x_center) - (dx_px / 2.0)
            y = sy(y_center) - (dy_px / 2.0)
            rects.append(
                f"  <rect x='{x:.2f}' y='{y:.2f}' width='{dx_px:.2f}' height='{dy_px:.2f}' fill='{color}' stroke='none' />"
            )

    return "\n".join(
        [
            f"<svg xmlns='http://www.w3.org/2000/svg' width='{svg_width}' height='{svg_height}' viewBox='0 0 {svg_width} {svg_height}'>",
            "  <rect width='100%' height='100%' fill='#f8fafc' />",
            f"  <text x='{margin}' y='24' font-family='monospace' font-size='20' fill='#0f172a'>{scenario.metadata.title} velocity magnitude</text>",
            f"  <text x='{margin}' y='46' font-family='monospace' font-size='12' fill='#334155'>Peak speed: {max_speed:.4f} m/s</text>",
            f"  <rect x='{margin}' y='{margin}' width='{basin_width_px}' height='{basin_height_px}' fill='#e2e8f0' stroke='#0f172a' stroke-width='3' />",
            *rects,
            _opening_svg_line(scenario.inlet, scenario, sx, sy, stroke="#16a34a"),
            _opening_svg_line(scenario.outlet, scenario, sx, sy, stroke="#dc2626"),
            *_baffle_svg_lines(scenario, sx, sy),
            f"  <text x='{margin}' y='{svg_height - 18}' font-family='monospace' font-size='12' fill='#334155'>Blue is lower speed. Red is higher speed.</text>",
            "</svg>",
        ]
    )


def write_velocity_heatmap_svg(
    scenario: ScenarioConfig,
    fields: HydraulicFieldData,
    output_path: str | Path,
) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(build_velocity_heatmap_svg(scenario, fields), encoding="utf-8")
    return destination


def _opening_svg_line(
    opening: OpeningConfig,
    scenario: ScenarioConfig,
    sx,
    sy,
    *,
    stroke: str,
) -> str:
    lower = opening.center_m - (opening.span_m / 2.0)
    upper = opening.center_m + (opening.span_m / 2.0)

    if opening.side == "west":
        return (
            f"  <line x1='{sx(0.0):.1f}' y1='{sy(lower):.1f}' x2='{sx(0.0):.1f}' y2='{sy(upper):.1f}' "
            f"stroke='{stroke}' stroke-width='8' />"
        )
    if opening.side == "east":
        return (
            f"  <line x1='{sx(scenario.geometry.length_m):.1f}' y1='{sy(lower):.1f}' "
            f"x2='{sx(scenario.geometry.length_m):.1f}' y2='{sy(upper):.1f}' stroke='{stroke}' stroke-width='8' />"
        )
    if opening.side == "south":
        return (
            f"  <line x1='{sx(lower):.1f}' y1='{sy(0.0):.1f}' x2='{sx(upper):.1f}' y2='{sy(0.0):.1f}' "
            f"stroke='{stroke}' stroke-width='8' />"
        )
    return (
        f"  <line x1='{sx(lower):.1f}' y1='{sy(scenario.geometry.width_m):.1f}' "
        f"x2='{sx(upper):.1f}' y2='{sy(scenario.geometry.width_m):.1f}' stroke='{stroke}' stroke-width='8' />"
    )


def _baffle_svg_lines(scenario: ScenarioConfig, sx, sy) -> list[str]:
    color_map = {
        "full_depth_solid": "#1f2937",
        "curtain_placeholder": "#2563eb",
        "porous_placeholder": "#ea580c",
    }
    lines: list[str] = []
    for baffle in scenario.baffles:
        stroke = color_map.get(baffle.kind, "#111827")
        dash = " stroke-dasharray='8 6'" if baffle.kind != "full_depth_solid" else ""
        lines.append(
            "  "
            f"<line x1='{sx(baffle.x1_m):.1f}' y1='{sy(baffle.y1_m):.1f}' "
            f"x2='{sx(baffle.x2_m):.1f}' y2='{sy(baffle.y2_m):.1f}' "
            f"stroke='{stroke}' stroke-width='5'{dash} />"
        )
    return lines


def _speed_color(normalized_speed: float) -> str:
    value = max(0.0, min(1.0, normalized_speed))
    red = int(20 + (220 * value))
    green = int(90 + (110 * (1.0 - value)))
    blue = int(235 - (180 * value))
    return f"#{red:02x}{green:02x}{blue:02x}"
