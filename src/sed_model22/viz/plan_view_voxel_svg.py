from __future__ import annotations

from pathlib import Path

from ..config import PlanViewScenarioConfig
from ..solver import HydraulicFieldData


def build_plan_view_voxel_isometric_svg(
    scenario: PlanViewScenarioConfig,
    fields: HydraulicFieldData,
    *,
    shared_vmax: float | None = None,
) -> str:
    x_stride = max(1, len(fields.x_centers_m) // 18)
    y_stride = max(1, len(fields.y_centers_m) // 10)
    x_indices = list(range(0, len(fields.x_centers_m), x_stride))
    y_indices = list(range(0, len(fields.y_centers_m), y_stride))
    depth_voxels = 4

    tile_width = 20.0
    tile_height = 11.0
    z_scale = 20.0
    origin_x = 320.0
    origin_y = 470.0
    svg_width = 1400
    svg_height = 900

    if shared_vmax is not None and shared_vmax > 0.0:
        max_speed = shared_vmax
        scale_label = f"Shared scale: {shared_vmax:.4f} m/s max"
    else:
        max_speed = max((max(row) for row in fields.speed_m_s), default=1.0)
        if max_speed <= 0.0:
            max_speed = 1.0
        scale_label = "Run-normalized for this screening case"

    voxel_shapes: list[tuple[float, str]] = []
    for x_position, i in enumerate(x_indices):
        for y_position, j in enumerate(y_indices):
            speed = fields.speed_m_s[i][j]
            color = _speed_band_color(speed / max_speed)
            for z_position in range(depth_voxels):
                opacity = 0.22 if z_position not in (0, depth_voxels - 1) else 0.30
                voxel_shapes.append(
                    (
                        x_position + y_position + z_position,
                        _voxel_cube_svg(
                            x_position,
                            y_position,
                            z_position,
                            tile_width,
                            tile_height,
                            z_scale,
                            origin_x,
                            origin_y,
                            color,
                            opacity,
                        ),
                    )
                )

    x_count = len(x_indices)
    y_count = len(y_indices)
    layers = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{svg_width}' height='{svg_height}' viewBox='0 0 {svg_width} {svg_height}'>",
        "  <rect width='100%' height='100%' fill='#f7fafc' />",
        "  <rect x='42' y='34' width='1316' height='832' rx='22' fill='#ffffff' stroke='#d7e2ee' stroke-width='2' />",
        f"  <text x='70' y='82' font-family='monospace' font-size='28' font-weight='700' fill='#0f172a'>{scenario.metadata.title}</text>",
        "  <text x='70' y='112' font-family='monospace' font-size='16' fill='#334155'>Voxelized screening visualization | 2.5D isometric view | plan-view x-y field extruded through water depth for display</text>",
        (
            "  <text x='70' y='142' font-family='monospace' font-size='14' fill='#475569'>"
            f"Case: {scenario.metadata.case_id} | Flow: {scenario.hydraulics.flow_rate_m3_s:.2f} m3/s | "
            f"Grid: {len(fields.x_centers_m)} x {len(fields.y_centers_m)} | Transparent water voxels are run-normalized speed bands, not literal 3D cells"
            "</text>"
        ),
        _basin_shell_svg(x_count, y_count, depth_voxels, tile_width, tile_height, z_scale, origin_x, origin_y),
    ]

    for _, shape in sorted(voxel_shapes, key=lambda item: item[0]):
        layers.append(shape)

    layers.append(
        _baffle_prisms_svg(
            scenario,
            x_count,
            y_count,
            depth_voxels,
            tile_width,
            tile_height,
            z_scale,
            origin_x,
            origin_y,
        )
    )
    layers.extend(_legend_svg(svg_width, scale_label))
    layers.extend(_notes_svg(scenario))
    layers.append("</svg>")
    return "\n".join(layers)


def write_plan_view_voxel_isometric_svg(
    scenario: PlanViewScenarioConfig,
    fields: HydraulicFieldData,
    output_path: str | Path,
    *,
    shared_vmax: float | None = None,
) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(build_plan_view_voxel_isometric_svg(scenario, fields, shared_vmax=shared_vmax), encoding="utf-8")
    return destination


def _basin_shell_svg(x_count: int, y_count: int, z_count: int, tile_width: float, tile_height: float, z_scale: float, origin_x: float, origin_y: float) -> str:
    top = _face_polygon([(0.0, 0.0, float(z_count)), (float(x_count), 0.0, float(z_count)), (float(x_count), float(y_count), float(z_count)), (0.0, float(y_count), float(z_count))], tile_width, tile_height, z_scale, origin_x, origin_y)
    right = _face_polygon([(float(x_count), 0.0, 0.0), (float(x_count), float(y_count), 0.0), (float(x_count), float(y_count), float(z_count)), (float(x_count), 0.0, float(z_count))], tile_width, tile_height, z_scale, origin_x, origin_y)
    left = _face_polygon([(0.0, float(y_count), 0.0), (float(x_count), float(y_count), 0.0), (float(x_count), float(y_count), float(z_count)), (0.0, float(y_count), float(z_count))], tile_width, tile_height, z_scale, origin_x, origin_y)
    return "\n".join([
        f"  <polygon points='{top}' fill='#cfe9ff' fill-opacity='0.08' stroke='#93b9d7' stroke-width='1.2' />",
        f"  <polygon points='{right}' fill='#cfe9ff' fill-opacity='0.05' stroke='#93b9d7' stroke-width='1.2' />",
        f"  <polygon points='{left}' fill='#cfe9ff' fill-opacity='0.05' stroke='#93b9d7' stroke-width='1.2' />",
    ])


def _baffle_prisms_svg(scenario: PlanViewScenarioConfig, x_count: int, y_count: int, z_count: int, tile_width: float, tile_height: float, z_scale: float, origin_x: float, origin_y: float) -> str:
    shapes: list[str] = []
    for baffle in scenario.baffles:
        if baffle.kind != "full_depth_solid":
            continue
        x0 = (min(baffle.x1_m, baffle.x2_m) / scenario.geometry.length_m) * x_count
        x1 = (max(baffle.x1_m, baffle.x2_m) / scenario.geometry.length_m) * x_count
        y0 = (min(baffle.y1_m, baffle.y2_m) / scenario.geometry.width_m) * y_count
        y1 = (max(baffle.y1_m, baffle.y2_m) / scenario.geometry.width_m) * y_count
        if baffle.x1_m == baffle.x2_m:
            x1 = min(x_count, x0 + 0.28)
        if baffle.y1_m == baffle.y2_m:
            y1 = min(y_count, y0 + 0.28)
        shapes.append(_prism_svg(x0, max(x1, x0 + 0.18), y0, max(y1, y0 + 0.18), 0.0, float(z_count), tile_width, tile_height, z_scale, origin_x, origin_y, "#475569", 0.82, "#1e293b"))
    return "\n".join(shapes)


def _notes_svg(scenario: PlanViewScenarioConfig) -> list[str]:
    notes = [
        "  <text x='78' y='720' font-family='monospace' font-size='15' font-weight='700' fill='#0f172a'>Display Notes</text>",
        "  <text x='78' y='746' font-family='monospace' font-size='13' fill='#334155'>- This is a 2.5D presentation of the current plan-view screening field.</text>",
        "  <text x='78' y='768' font-family='monospace' font-size='13' fill='#334155'>- Water depth is shown as a uniform extrusion for readability. This is not a full 3D solve.</text>",
        "  <text x='78' y='790' font-family='monospace' font-size='13' fill='#334155'>- Solid gray prisms show full-depth solid baffles where present.</text>",
        "  <text x='78' y='812' font-family='monospace' font-size='13' fill='#334155'>- This is best used for comparing screening-flow pattern changes between v0.1 cases.</text>",
    ]
    if not scenario.baffles:
        notes.append("  <text x='78' y='834' font-family='monospace' font-size='13' fill='#475569'>- This case has no internal baffles, so it serves as a cleaner verification reference.</text>")
    return notes


def _legend_svg(svg_width: int, scale_label: str = "Run-normalized for this screening case") -> list[str]:
    left = svg_width - 292
    top = 506
    colors = [("Low relative speed", "#d8eff7"), ("Moderate relative speed", "#8bd3e6"), ("Elevated relative speed", "#4e99d3"), ("Highest relative speed", "#d26a3b")]
    layers = [
        f"  <rect x='{left}' y='{top}' width='228' height='150' rx='12' fill='#ffffff' stroke='#d7e2ee' stroke-width='1.5' />",
        f"  <text x='{left + 14}' y='{top + 24}' font-family='monospace' font-size='14' font-weight='700' fill='#0f172a'>Relative Speed Band</text>",
        f"  <text x='{left + 14}' y='{top + 42}' font-family='monospace' font-size='11' fill='#475569'>{scale_label}</text>",
    ]
    for index, (label, color) in enumerate(colors):
        y = top + 58 + index * 22
        layers.append(f"  <rect x='{left + 14}' y='{y}' width='18' height='12' fill='{color}' stroke='#94a3b8' stroke-width='0.8' />")
        layers.append(f"  <text x='{left + 40}' y='{y + 10}' font-family='monospace' font-size='12' fill='#334155'>{label}</text>")
    return layers


def _voxel_cube_svg(x: int, y: int, z: int, tile_width: float, tile_height: float, z_scale: float, origin_x: float, origin_y: float, color: str, opacity: float) -> str:
    top = _face_polygon([(float(x), float(y), float(z + 1)), (float(x + 1), float(y), float(z + 1)), (float(x + 1), float(y + 1), float(z + 1)), (float(x), float(y + 1), float(z + 1))], tile_width, tile_height, z_scale, origin_x, origin_y)
    right = _face_polygon([(float(x + 1), float(y), float(z)), (float(x + 1), float(y + 1), float(z)), (float(x + 1), float(y + 1), float(z + 1)), (float(x + 1), float(y), float(z + 1))], tile_width, tile_height, z_scale, origin_x, origin_y)
    left = _face_polygon([(float(x), float(y + 1), float(z)), (float(x + 1), float(y + 1), float(z)), (float(x + 1), float(y + 1), float(z + 1)), (float(x), float(y + 1), float(z + 1))], tile_width, tile_height, z_scale, origin_x, origin_y)
    return "\n".join([
        f"  <polygon points='{left}' fill='{_shade(color, 0.82)}' fill-opacity='{opacity:.2f}' stroke='#7f94a8' stroke-opacity='0.18' stroke-width='0.6' />",
        f"  <polygon points='{right}' fill='{_shade(color, 0.64)}' fill-opacity='{opacity:.2f}' stroke='#7f94a8' stroke-opacity='0.18' stroke-width='0.6' />",
        f"  <polygon points='{top}' fill='{_shade(color, 1.12)}' fill-opacity='{opacity:.2f}' stroke='#7f94a8' stroke-opacity='0.18' stroke-width='0.6' />",
    ])


def _prism_svg(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float, tile_width: float, tile_height: float, z_scale: float, origin_x: float, origin_y: float, color: str, opacity: float, stroke: str) -> str:
    top = _face_polygon([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], tile_width, tile_height, z_scale, origin_x, origin_y)
    right = _face_polygon([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], tile_width, tile_height, z_scale, origin_x, origin_y)
    left = _face_polygon([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], tile_width, tile_height, z_scale, origin_x, origin_y)
    return "\n".join([
        f"  <polygon points='{left}' fill='{_shade(color, 0.90)}' fill-opacity='{opacity:.2f}' stroke='{stroke}' stroke-width='0.9' />",
        f"  <polygon points='{right}' fill='{_shade(color, 0.72)}' fill-opacity='{opacity:.2f}' stroke='{stroke}' stroke-width='0.9' />",
        f"  <polygon points='{top}' fill='{_shade(color, 1.08)}' fill-opacity='{opacity:.2f}' stroke='{stroke}' stroke-width='0.9' />",
    ])


def _face_polygon(vertices: list[tuple[float, float, float]], tile_width: float, tile_height: float, z_scale: float, origin_x: float, origin_y: float) -> str:
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in (_project_point(px, py, pz, tile_width, tile_height, z_scale, origin_x, origin_y) for px, py, pz in vertices))


def _project_point(x: float, y: float, z: float, tile_width: float, tile_height: float, z_scale: float, origin_x: float, origin_y: float) -> tuple[float, float]:
    screen_x = origin_x + (x - y) * tile_width
    screen_y = origin_y + (x + y) * tile_height - z * z_scale
    return screen_x, screen_y


def _speed_band_color(normalized_speed: float) -> str:
    value = max(0.0, min(1.0, normalized_speed))
    if value <= 0.25:
        return "#d8eff7"
    if value <= 0.50:
        return "#8bd3e6"
    if value <= 0.75:
        return "#4e99d3"
    return "#d26a3b"


def _shade(color: str, factor: float) -> str:
    red = int(color[1:3], 16)
    green = int(color[3:5], 16)
    blue = int(color[5:7], 16)
    return "#{:02x}{:02x}{:02x}".format(_clamp_color(red * factor), _clamp_color(green * factor), _clamp_color(blue * factor))


def _clamp_color(value: float) -> int:
    return max(0, min(255, int(round(value))))
