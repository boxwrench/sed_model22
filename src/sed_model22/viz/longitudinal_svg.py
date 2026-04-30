from __future__ import annotations

from pathlib import Path

from ..config import (
    BypassOpeningFeatureConfig,
    LaunderZoneFeatureConfig,
    LongitudinalScenarioConfig,
    PerforatedBaffleFeatureConfig,
    PlateSettlerZoneFeatureConfig,
    SolidBaffleFeatureConfig,
)
from ..solver.longitudinal import LongitudinalFieldData, LongitudinalTracerSummary


def build_longitudinal_layout_svg(scenario: LongitudinalScenarioConfig) -> str:
    margin = 40
    basin_width_px = 980
    basin_height_px = 320
    svg_width = basin_width_px + margin * 2
    svg_height = basin_height_px + margin * 2 + 80

    def sx(x_m: float) -> float:
        return margin + (x_m / scenario.geometry.basin_length_m) * basin_width_px

    def sz(z_m: float) -> float:
        return margin + basin_height_px - (z_m / scenario.geometry.water_depth_m) * basin_height_px

    layers = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{svg_width}' height='{svg_height}' viewBox='0 0 {svg_width} {svg_height}'>",
        "  <rect width='100%' height='100%' fill='#f8fafc' />",
        f"  <text x='{margin}' y='24' font-family='monospace' font-size='20' fill='#0f172a'>{scenario.metadata.title} longitudinal section</text>",
        f"  <text x='{margin}' y='46' font-family='monospace' font-size='12' fill='#334155'>Case: {scenario.metadata.case_id} | Length: {scenario.geometry.basin_length_m:.2f} m | Width: {scenario.geometry.basin_width_m:.2f} m | Depth: {scenario.geometry.water_depth_m:.2f} m</text>",
        f"  <rect x='{margin}' y='{margin}' width='{basin_width_px}' height='{basin_height_px}' fill='#dbeafe' stroke='#0f172a' stroke-width='3' />",
        f"  <rect x='{margin}' y='{sz(_inlet_zone_top(scenario)):.2f}' width='8' height='{(sz(_inlet_zone_bottom(scenario)) - sz(_inlet_zone_top(scenario))):.2f}' fill='#16a34a' opacity='0.45' />",
    ]

    for station in scenario.evaluation_stations:
        x = sx(station.x_m)
        layers.append(
            f"  <line x1='{x:.2f}' y1='{margin}' x2='{x:.2f}' y2='{margin + basin_height_px}' stroke='#475569' stroke-dasharray='6 6' stroke-width='1.5' />"
        )
        layers.append(
            f"  <text x='{x + 4:.1f}' y='{margin + basin_height_px + 16}' font-family='monospace' font-size='11' fill='#334155'>{station.name}</text>"
        )

    for feature in scenario.features:
        if isinstance(feature, (PerforatedBaffleFeatureConfig, SolidBaffleFeatureConfig)):
            x = sx(feature.x_m)
            color = "#1f2937" if isinstance(feature, SolidBaffleFeatureConfig) else "#ea580c"
            dash = " stroke-dasharray='8 6'" if isinstance(feature, PerforatedBaffleFeatureConfig) else ""
            layers.append(
                f"  <line x1='{x:.2f}' y1='{sz(feature.z_bottom_m):.2f}' x2='{x:.2f}' y2='{sz(feature.z_top_m):.2f}' stroke='{color}' stroke-width='5'{dash} />"
            )
            layers.append(
                f"  <text x='{x + 6:.1f}' y='{sz(feature.z_top_m) - 4:.1f}' font-family='monospace' font-size='11' fill='{color}'>{feature.name}</text>"
            )
            continue

        if isinstance(feature, BypassOpeningFeatureConfig):
            x = sx(feature.x_m) - 6.0
            y = sz(feature.z_top_m)
            height = sz(feature.z_bottom_m) - sz(feature.z_top_m)
            layers.append(
                f"  <rect x='{x:.2f}' y='{y:.2f}' width='12' height='{height:.2f}' fill='#22c55e' opacity='0.65' stroke='#15803d' stroke-width='2' />"
            )
            layers.append(
                f"  <text x='{x + 14:.1f}' y='{y + 12:.1f}' font-family='monospace' font-size='11' fill='#166534'>{feature.name}</text>"
            )
            continue

        if isinstance(feature, PlateSettlerZoneFeatureConfig):
            x = sx(feature.x_start_m)
            width = sx(feature.x_end_m) - sx(feature.x_start_m)
            y = sz(feature.z_top_m)
            height = sz(feature.z_bottom_m) - sz(feature.z_top_m)
            layers.append(
                f"  <rect x='{x:.2f}' y='{y:.2f}' width='{width:.2f}' height='{height:.2f}' fill='#38bdf8' opacity='0.18' stroke='#0284c7' stroke-width='2' />"
            )
            layers.append(
                f"  <text x='{x + 4:.1f}' y='{y + 16:.1f}' font-family='monospace' font-size='11' fill='#075985'>{feature.name}</text>"
            )
            continue

        if isinstance(feature, LaunderZoneFeatureConfig):
            x = sx(feature.x_start_m)
            width = sx(feature.x_end_m) - sx(feature.x_start_m)
            y = sz(scenario.geometry.water_depth_m)
            layers.append(
                f"  <rect x='{x:.2f}' y='{y - 8:.2f}' width='{width:.2f}' height='8' fill='#ef4444' opacity='0.8' />"
            )
            layers.append(
                f"  <text x='{x + 2:.1f}' y='{y - 12:.1f}' font-family='monospace' font-size='11' fill='#b91c1c'>{feature.name}</text>"
            )

    layers.append(
        f"  <text x='{margin}' y='{svg_height - 18}' font-family='monospace' font-size='12' fill='#334155'>Vertical axis is elevation z. The left boundary is the inlet zone and the top boundary carries the launder collection zone.</text>"
    )
    layers.append("</svg>")
    return "\n".join(layers)


def write_longitudinal_layout_svg(
    scenario: LongitudinalScenarioConfig,
    output_path: str | Path,
) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(build_longitudinal_layout_svg(scenario), encoding="utf-8")
    return destination


def build_longitudinal_velocity_heatmap_svg(
    scenario: LongitudinalScenarioConfig,
    fields: LongitudinalFieldData,
    *,
    shared_vmax: float | None = None,
) -> str:
    margin = 40
    basin_width_px = 980
    basin_height_px = 320
    svg_width = basin_width_px + margin * 2
    svg_height = basin_height_px + margin * 2 + 80

    def sx(x_m: float) -> float:
        return margin + (x_m / scenario.geometry.basin_length_m) * basin_width_px

    def sz(z_m: float) -> float:
        return margin + basin_height_px - (z_m / scenario.geometry.water_depth_m) * basin_height_px

    if shared_vmax is not None and shared_vmax > 0.0:
        max_speed = shared_vmax
        scale_note = f"Shared scale: {shared_vmax:.4f} m/s max"
    else:
        max_speed = max((max(row) for row in fields.speed_m_s), default=0.0)
        if max_speed <= 0.0:
            max_speed = 1.0
        scale_note = f"Peak speed: {max_speed:.4f} m/s"

    dx_px = basin_width_px / len(fields.x_centers_m)
    dz_px = basin_height_px / len(fields.z_centers_m)

    rects: list[str] = []
    for i, x_center in enumerate(fields.x_centers_m):
        for k, z_center in enumerate(fields.z_centers_m):
            speed = fields.speed_m_s[i][k]
            color = _speed_color(speed / max_speed)
            x = sx(x_center) - (dx_px / 2.0)
            y = sz(z_center) - (dz_px / 2.0)
            rects.append(
                f"  <rect x='{x:.2f}' y='{y:.2f}' width='{dx_px:.2f}' height='{dz_px:.2f}' fill='{color}' stroke='none' />"
            )

    layers = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{svg_width}' height='{svg_height}' viewBox='0 0 {svg_width} {svg_height}'>",
        "  <rect width='100%' height='100%' fill='#f8fafc' />",
        f"  <text x='{margin}' y='24' font-family='monospace' font-size='20' fill='#0f172a'>{scenario.metadata.title} velocity magnitude</text>",
        f"  <text x='{margin}' y='46' font-family='monospace' font-size='12' fill='#334155'>{scale_note}</text>",
        f"  <rect x='{margin}' y='{margin}' width='{basin_width_px}' height='{basin_height_px}' fill='#e2e8f0' stroke='#0f172a' stroke-width='3' />",
        *rects,
        f"  <text x='{margin}' y='{svg_height - 18}' font-family='monospace' font-size='12' fill='#334155'>Blue is lower speed. Red is higher speed.</text>",
        "</svg>",
    ]
    return "\n".join(layers)


def write_longitudinal_velocity_heatmap_svg(
    scenario: LongitudinalScenarioConfig,
    fields: LongitudinalFieldData,
    output_path: str | Path,
    *,
    shared_vmax: float | None = None,
) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(build_longitudinal_velocity_heatmap_svg(scenario, fields, shared_vmax=shared_vmax), encoding="utf-8")
    return destination


def build_tracer_breakthrough_svg(
    scenario: LongitudinalScenarioConfig,
    tracer: LongitudinalTracerSummary,
) -> str:
    margin = 48
    plot_width = 920
    plot_height = 300
    svg_width = plot_width + margin * 2
    svg_height = plot_height + margin * 2 + 60

    max_time = max(max(tracer.time_points_s, default=1.0), 1.0e-9)
    max_concentration = max(max(tracer.outlet_concentration_history, default=1.0), 1.0)

    def px(time_s: float) -> float:
        return margin + (time_s / max_time) * plot_width

    def py(concentration: float) -> float:
        normalized = concentration / max_concentration
        return margin + plot_height - (normalized * plot_height)

    points = " ".join(f"{px(t):.2f},{py(c):.2f}" for t, c in zip(tracer.time_points_s, tracer.outlet_concentration_history))
    markers = [
        (tracer.t10_s, "#0f766e"),
        (tracer.t50_s, "#7c3aed"),
        (tracer.t90_s, "#dc2626"),
    ]

    layers = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{svg_width}' height='{svg_height}' viewBox='0 0 {svg_width} {svg_height}'>",
        "  <rect width='100%' height='100%' fill='#f8fafc' />",
        f"  <text x='{margin}' y='24' font-family='monospace' font-size='20' fill='#0f172a'>{scenario.metadata.title} RTD proxy breakthrough</text>",
        f"  <text x='{margin}' y='46' font-family='monospace' font-size='12' fill='#334155'>Model: {tracer.proxy_model} | t10: {tracer.t10_s:.1f} s | t50: {tracer.t50_s:.1f} s | t90: {tracer.t90_s:.1f} s | Final concentration: {tracer.final_outlet_concentration:.3f}</text>",
        f"  <rect x='{margin}' y='{margin}' width='{plot_width}' height='{plot_height}' fill='#fff' stroke='#0f172a' stroke-width='2' />",
        f"  <line x1='{margin}' y1='{py(0.0):.2f}' x2='{margin + plot_width}' y2='{py(0.0):.2f}' stroke='#cbd5e1' stroke-width='1' />",
        f"  <line x1='{margin}' y1='{py(0.5):.2f}' x2='{margin + plot_width}' y2='{py(0.5):.2f}' stroke='#cbd5e1' stroke-width='1' stroke-dasharray='4 4' />",
        f"  <line x1='{margin}' y1='{py(1.0):.2f}' x2='{margin + plot_width}' y2='{py(1.0):.2f}' stroke='#cbd5e1' stroke-width='1' />",
        f"  <polyline fill='none' stroke='#0f172a' stroke-width='2.5' points='{points}' />",
    ]

    for time_s, color in markers:
        x = px(time_s)
        layers.append(
            f"  <line x1='{x:.2f}' y1='{margin}' x2='{x:.2f}' y2='{margin + plot_height}' stroke='{color}' stroke-width='1.5' stroke-dasharray='5 5' />"
        )

    layers.append(
        f"  <text x='{margin}' y='{svg_height - 18}' font-family='monospace' font-size='12' fill='#334155'>Outlet concentration is the deterministic RTD proxy averaged over the launder boundary cells.</text>"
    )
    layers.append("</svg>")
    return "\n".join(layers)


def write_tracer_breakthrough_svg(
    scenario: LongitudinalScenarioConfig,
    tracer: LongitudinalTracerSummary,
    output_path: str | Path,
) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(build_tracer_breakthrough_svg(scenario, tracer), encoding="utf-8")
    return destination


def write_longitudinal_tracer_breakthrough_svg(
    scenario: LongitudinalScenarioConfig,
    tracer: LongitudinalTracerSummary,
    output_path: str | Path,
) -> Path:
    return write_tracer_breakthrough_svg(scenario, tracer, output_path)


def _inlet_zone_bottom(scenario: LongitudinalScenarioConfig) -> float:
    return scenario.upstream.inlet_zone_center_elevation_m - (scenario.upstream.inlet_zone_height_m / 2.0)


def _inlet_zone_top(scenario: LongitudinalScenarioConfig) -> float:
    return scenario.upstream.inlet_zone_center_elevation_m + (scenario.upstream.inlet_zone_height_m / 2.0)


def _speed_color(normalized_speed: float) -> str:
    value = max(0.0, min(1.0, normalized_speed))
    red = int(20 + (220 * value))
    green = int(90 + (110 * (1.0 - value)))
    blue = int(235 - (180 * value))
    return f"#{red:02x}{green:02x}{blue:02x}"
