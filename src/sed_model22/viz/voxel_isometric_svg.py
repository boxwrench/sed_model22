from __future__ import annotations

from pathlib import Path

from ..config import (
    LaunderZoneFeatureConfig,
    LongitudinalScenarioConfig,
    PerforatedBaffleFeatureConfig,
    PlateSettlerZoneFeatureConfig,
    SolidBaffleFeatureConfig,
)
from ..solver.longitudinal import LongitudinalFieldData


def build_longitudinal_voxel_isometric_svg(
    scenario: LongitudinalScenarioConfig,
    fields: LongitudinalFieldData,
) -> str:
    x_stride = max(1, len(fields.x_centers_m) // 18)
    z_stride = max(1, len(fields.z_centers_m) // 10)
    x_indices = list(range(0, len(fields.x_centers_m), x_stride))
    z_indices = list(range(0, len(fields.z_centers_m), z_stride))
    width_voxels = 5

    tile_width = 20.0
    tile_height = 11.0
    z_scale = 18.0
    origin_x = 300.0
    origin_y = 430.0
    svg_width = 1400
    svg_height = 900

    max_speed = max((max(row) for row in fields.speed_m_s), default=1.0)
    if max_speed <= 0.0:
        max_speed = 1.0

    voxel_shapes: list[tuple[float, str]] = []
    for x_position, i in enumerate(x_indices):
        for z_position, k in enumerate(z_indices):
            speed = fields.speed_m_s[i][k]
            color = _speed_band_color(speed / max_speed)
            z_base = len(z_indices) - z_position - 1
            for y_position in range(width_voxels):
                opacity = 0.28 if y_position not in (0, width_voxels - 1) else 0.36
                voxel_shapes.append(
                    (
                        x_position + y_position + z_base,
                        _voxel_cube_svg(
                            x_position,
                            y_position,
                            z_base,
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
    z_count = len(z_indices)

    layers = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{svg_width}' height='{svg_height}' viewBox='0 0 {svg_width} {svg_height}'>",
        "  <rect width='100%' height='100%' fill='#f7fafc' />",
        "  <rect x='42' y='34' width='1316' height='832' rx='22' fill='#ffffff' stroke='#d7e2ee' stroke-width='2' />",
        f"  <text x='70' y='82' font-family='monospace' font-size='28' font-weight='700' fill='#0f172a'>{scenario.metadata.title}</text>",
        "  <text x='70' y='112' font-family='monospace' font-size='16' fill='#334155'>Voxelized screening visualization | 2.5D isometric view | longitudinal x-z field extruded across basin width for display</text>",
        (
            "  <text x='70' y='142' font-family='monospace' font-size='14' fill='#475569'>"
            f"Case: {scenario.metadata.case_id} | Flow: {scenario.hydraulics.flow_rate_m3_s:.2f} m3/s | "
            f"Grid: {len(fields.x_centers_m)} x {len(fields.z_centers_m)} | Transparent water voxels are run-normalized speed bands, not literal 3D cells"
            "</text>"
        ),
        _basin_shell_svg(x_count, width_voxels, z_count, tile_width, tile_height, z_scale, origin_x, origin_y),
    ]

    for _, shape in sorted(voxel_shapes, key=lambda item: item[0]):
        layers.append(shape)

    layers.append(
        _feature_prisms_svg(
            scenario,
            x_count,
            width_voxels,
            z_count,
            tile_width,
            tile_height,
            z_scale,
            origin_x,
            origin_y,
        )
    )
    layers.extend(_annotation_svg(scenario, x_count, width_voxels, z_count, tile_width, tile_height, z_scale, origin_x, origin_y))
    layers.extend(_legend_svg(svg_width))
    layers.append("</svg>")
    return "\n".join(layers)


def write_longitudinal_voxel_isometric_svg(
    scenario: LongitudinalScenarioConfig,
    fields: LongitudinalFieldData,
    output_path: str | Path,
) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        build_longitudinal_voxel_isometric_svg(scenario, fields),
        encoding="utf-8",
    )
    return destination


def _basin_shell_svg(
    x_count: int,
    y_count: int,
    z_count: int,
    tile_width: float,
    tile_height: float,
    z_scale: float,
    origin_x: float,
    origin_y: float,
) -> str:
    top = _face_polygon(
        [
            (0.0, 0.0, float(z_count)),
            (float(x_count), 0.0, float(z_count)),
            (float(x_count), float(y_count), float(z_count)),
            (0.0, float(y_count), float(z_count)),
        ],
        tile_width,
        tile_height,
        z_scale,
        origin_x,
        origin_y,
    )
    right = _face_polygon(
        [
            (float(x_count), 0.0, 0.0),
            (float(x_count), float(y_count), 0.0),
            (float(x_count), float(y_count), float(z_count)),
            (float(x_count), 0.0, float(z_count)),
        ],
        tile_width,
        tile_height,
        z_scale,
        origin_x,
        origin_y,
    )
    left = _face_polygon(
        [
            (0.0, float(y_count), 0.0),
            (float(x_count), float(y_count), 0.0),
            (float(x_count), float(y_count), float(z_count)),
            (0.0, float(y_count), float(z_count)),
        ],
        tile_width,
        tile_height,
        z_scale,
        origin_x,
        origin_y,
    )
    return "\n".join(
        [
            f"  <polygon points='{top}' fill='#cfe9ff' fill-opacity='0.08' stroke='#93b9d7' stroke-width='1.2' />",
            f"  <polygon points='{right}' fill='#cfe9ff' fill-opacity='0.05' stroke='#93b9d7' stroke-width='1.2' />",
            f"  <polygon points='{left}' fill='#cfe9ff' fill-opacity='0.05' stroke='#93b9d7' stroke-width='1.2' />",
        ]
    )


def _feature_prisms_svg(
    scenario: LongitudinalScenarioConfig,
    x_count: int,
    y_count: int,
    z_count: int,
    tile_width: float,
    tile_height: float,
    z_scale: float,
    origin_x: float,
    origin_y: float,
) -> str:
    shapes: list[str] = []
    for feature in scenario.features:
        if isinstance(feature, (PerforatedBaffleFeatureConfig, SolidBaffleFeatureConfig)):
            x_position = (feature.x_m / scenario.geometry.basin_length_m) * x_count
            z_bottom = (feature.z_bottom_m / scenario.geometry.water_depth_m) * z_count
            z_top = (feature.z_top_m / scenario.geometry.water_depth_m) * z_count
            shapes.append(
                _prism_svg(
                    x_position,
                    min(x_position + 0.28, x_count),
                    0.0,
                    float(y_count),
                    z_bottom,
                    z_top,
                    tile_width,
                    tile_height,
                    z_scale,
                    origin_x,
                    origin_y,
                    "#d97706",
                    0.78,
                    "#8a4b00",
                )
            )
            continue

        if isinstance(feature, PlateSettlerZoneFeatureConfig):
            x_start = (feature.x_start_m / scenario.geometry.basin_length_m) * x_count
            x_end = (feature.x_end_m / scenario.geometry.basin_length_m) * x_count
            z_bottom = (feature.z_bottom_m / scenario.geometry.water_depth_m) * z_count
            z_top = (feature.z_top_m / scenario.geometry.water_depth_m) * z_count
            shapes.append(
                _prism_svg(
                    x_start,
                    x_end,
                    0.0,
                    float(y_count),
                    z_bottom,
                    z_top,
                    tile_width,
                    tile_height,
                    z_scale,
                    origin_x,
                    origin_y,
                    "#38bdf8",
                    0.22,
                    "#0284c7",
                )
            )
            continue

        if isinstance(feature, LaunderZoneFeatureConfig):
            x_start = (feature.x_start_m / scenario.geometry.basin_length_m) * x_count
            x_end = (feature.x_end_m / scenario.geometry.basin_length_m) * x_count
            z_bottom = ((feature.z_m / scenario.geometry.water_depth_m) * z_count) - 0.22
            z_top = (feature.z_m / scenario.geometry.water_depth_m) * z_count
            shapes.append(
                _prism_svg(
                    x_start,
                    x_end,
                    0.0,
                    float(y_count),
                    max(0.0, z_bottom),
                    z_top,
                    tile_width,
                    tile_height,
                    z_scale,
                    origin_x,
                    origin_y,
                    "#ef4444",
                    0.75,
                    "#991b1b",
                )
            )
    return "\n".join(shapes)


def _annotation_svg(
    scenario: LongitudinalScenarioConfig,
    x_count: int,
    y_count: int,
    z_count: int,
    tile_width: float,
    tile_height: float,
    z_scale: float,
    origin_x: float,
    origin_y: float,
) -> list[str]:
    wall_label_title, wall_label_subtitle = _transition_wall_display_label(scenario)
    layers = [
        "  <text x='78' y='720' font-family='monospace' font-size='15' font-weight='700' fill='#0f172a'>Display Notes</text>",
        "  <text x='78' y='746' font-family='monospace' font-size='13' fill='#334155'>- This is a 2.5D presentation of the current longitudinal screening field.</text>",
        "  <text x='78' y='768' font-family='monospace' font-size='13' fill='#334155'>- Width is extruded uniformly for readability. This is not a full 3D solve.</text>",
        "  <text x='78' y='790' font-family='monospace' font-size='13' fill='#334155'>- The transition wall is rendered as a solid panel for readability, even though v0.2 still models it as a loss interface.</text>",
        "  <text x='78' y='812' font-family='monospace' font-size='13' fill='#334155'>- Relative speed bands are more honest here than absolute m/s because the present study still has large discharge-mismatch diagnostics.</text>",
    ]

    wall_feature = next(
        (
            feature
            for feature in scenario.features
            if feature.name == "transition_wall" and isinstance(feature, (PerforatedBaffleFeatureConfig, SolidBaffleFeatureConfig))
        ),
        None,
    )
    if wall_feature is not None:
        wall_point = _project_point(
            (wall_feature.x_m / scenario.geometry.basin_length_m) * x_count + 0.14,
            float(y_count),
            (wall_feature.z_top_m / scenario.geometry.water_depth_m) * z_count,
            tile_width,
            tile_height,
            z_scale,
            origin_x,
            origin_y,
        )
        layers.extend(
            [
                f"  <line x1='{wall_point[0]:.1f}' y1='{wall_point[1]:.1f}' x2='1128' y2='170' stroke='#946200' stroke-width='1.4' />",
                "  <rect x='1132' y='138' width='210' height='44' rx='8' fill='#fff7ed' stroke='#fdba74' stroke-width='1.5' />",
                f"  <text x='1144' y='158' font-family='monospace' font-size='13' font-weight='700' fill='#9a3412'>{wall_label_title}</text>",
                f"  <text x='1144' y='174' font-family='monospace' font-size='12' fill='#7c2d12'>{wall_label_subtitle}</text>",
            ]
        )

    plate_feature = next((feature for feature in scenario.features if isinstance(feature, PlateSettlerZoneFeatureConfig)), None)
    if plate_feature is not None:
        plate_point = _project_point(
            (plate_feature.x_start_m / scenario.geometry.basin_length_m) * x_count,
            float(y_count),
            (plate_feature.z_top_m / scenario.geometry.water_depth_m) * z_count,
            tile_width,
            tile_height,
            z_scale,
            origin_x,
            origin_y,
        )
        layers.extend(
            [
                f"  <line x1='{plate_point[0]:.1f}' y1='{plate_point[1]:.1f}' x2='1088' y2='282' stroke='#0284c7' stroke-width='1.4' />",
                "  <rect x='1092' y='252' width='224' height='44' rx='8' fill='#ecfeff' stroke='#67e8f9' stroke-width='1.5' />",
                "  <text x='1104' y='272' font-family='monospace' font-size='13' font-weight='700' fill='#155e75'>Plate settler proxy zone</text>",
                "  <text x='1104' y='288' font-family='monospace' font-size='12' fill='#155e75'>Upper porous block in v0.2</text>",
            ]
        )

    launder_feature = next((feature for feature in scenario.features if isinstance(feature, LaunderZoneFeatureConfig)), None)
    if launder_feature is not None:
        launder_point = _project_point(
            (launder_feature.x_end_m / scenario.geometry.basin_length_m) * x_count,
            0.0,
            (launder_feature.z_m / scenario.geometry.water_depth_m) * z_count,
            tile_width,
            tile_height,
            z_scale,
            origin_x,
            origin_y,
        )
        layers.extend(
            [
                f"  <line x1='{launder_point[0]:.1f}' y1='{launder_point[1]:.1f}' x2='1068' y2='392' stroke='#b91c1c' stroke-width='1.4' />",
                "  <rect x='1072' y='362' width='228' height='44' rx='8' fill='#fef2f2' stroke='#fca5a5' stroke-width='1.5' />",
                "  <text x='1084' y='382' font-family='monospace' font-size='13' font-weight='700' fill='#991b1b'>Launder collection zone</text>",
                "  <text x='1084' y='398' font-family='monospace' font-size='12' fill='#7f1d1d'>Top boundary outlet span</text>",
            ]
        )

    return layers


def _legend_svg(svg_width: int) -> list[str]:
    left = svg_width - 292
    top = 506
    colors = [
        ("Low relative speed", "#d8eff7"),
        ("Moderate relative speed", "#8bd3e6"),
        ("Elevated relative speed", "#4e99d3"),
        ("Highest relative speed", "#d26a3b"),
    ]
    layers = [
        f"  <rect x='{left}' y='{top}' width='228' height='150' rx='12' fill='#ffffff' stroke='#d7e2ee' stroke-width='1.5' />",
        f"  <text x='{left + 14}' y='{top + 24}' font-family='monospace' font-size='14' font-weight='700' fill='#0f172a'>Relative Speed Band</text>",
        f"  <text x='{left + 14}' y='{top + 42}' font-family='monospace' font-size='11' fill='#475569'>Run-normalized for this screening case</text>",
    ]
    for index, (label, color) in enumerate(colors):
        y = top + 58 + index * 22
        layers.append(f"  <rect x='{left + 14}' y='{y}' width='18' height='12' fill='{color}' stroke='#94a3b8' stroke-width='0.8' />")
        layers.append(f"  <text x='{left + 40}' y='{y + 10}' font-family='monospace' font-size='12' fill='#334155'>{label}</text>")
    layers.append(
        f"  <text x='{left + 14}' y='{top + 138}' font-family='monospace' font-size='11' fill='#475569'>Transparent water voxels show the display field only.</text>"
    )
    return layers


def _voxel_cube_svg(
    x: int,
    y: int,
    z: int,
    tile_width: float,
    tile_height: float,
    z_scale: float,
    origin_x: float,
    origin_y: float,
    color: str,
    opacity: float,
) -> str:
    top = _face_polygon(
        [
            (float(x), float(y), float(z + 1)),
            (float(x + 1), float(y), float(z + 1)),
            (float(x + 1), float(y + 1), float(z + 1)),
            (float(x), float(y + 1), float(z + 1)),
        ],
        tile_width,
        tile_height,
        z_scale,
        origin_x,
        origin_y,
    )
    right = _face_polygon(
        [
            (float(x + 1), float(y), float(z)),
            (float(x + 1), float(y + 1), float(z)),
            (float(x + 1), float(y + 1), float(z + 1)),
            (float(x + 1), float(y), float(z + 1)),
        ],
        tile_width,
        tile_height,
        z_scale,
        origin_x,
        origin_y,
    )
    left = _face_polygon(
        [
            (float(x), float(y + 1), float(z)),
            (float(x + 1), float(y + 1), float(z)),
            (float(x + 1), float(y + 1), float(z + 1)),
            (float(x), float(y + 1), float(z + 1)),
        ],
        tile_width,
        tile_height,
        z_scale,
        origin_x,
        origin_y,
    )
    return "\n".join(
        [
            f"  <polygon points='{left}' fill='{_shade(color, 0.82)}' fill-opacity='{opacity:.2f}' stroke='#7f94a8' stroke-opacity='0.18' stroke-width='0.6' />",
            f"  <polygon points='{right}' fill='{_shade(color, 0.64)}' fill-opacity='{opacity:.2f}' stroke='#7f94a8' stroke-opacity='0.18' stroke-width='0.6' />",
            f"  <polygon points='{top}' fill='{_shade(color, 1.12)}' fill-opacity='{opacity:.2f}' stroke='#7f94a8' stroke-opacity='0.18' stroke-width='0.6' />",
        ]
    )


def _prism_svg(
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    z0: float,
    z1: float,
    tile_width: float,
    tile_height: float,
    z_scale: float,
    origin_x: float,
    origin_y: float,
    color: str,
    opacity: float,
    stroke: str,
) -> str:
    top = _face_polygon(
        [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
        tile_width,
        tile_height,
        z_scale,
        origin_x,
        origin_y,
    )
    right = _face_polygon(
        [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
        tile_width,
        tile_height,
        z_scale,
        origin_x,
        origin_y,
    )
    left = _face_polygon(
        [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)],
        tile_width,
        tile_height,
        z_scale,
        origin_x,
        origin_y,
    )
    return "\n".join(
        [
            f"  <polygon points='{left}' fill='{_shade(color, 0.90)}' fill-opacity='{opacity:.2f}' stroke='{stroke}' stroke-width='0.9' />",
            f"  <polygon points='{right}' fill='{_shade(color, 0.72)}' fill-opacity='{opacity:.2f}' stroke='{stroke}' stroke-width='0.9' />",
            f"  <polygon points='{top}' fill='{_shade(color, 1.08)}' fill-opacity='{opacity:.2f}' stroke='{stroke}' stroke-width='0.9' />",
        ]
    )


def _face_polygon(
    vertices: list[tuple[float, float, float]],
    tile_width: float,
    tile_height: float,
    z_scale: float,
    origin_x: float,
    origin_y: float,
) -> str:
    return " ".join(
        f"{x:.2f},{y:.2f}"
        for x, y in (
            _project_point(px, py, pz, tile_width, tile_height, z_scale, origin_x, origin_y)
            for px, py, pz in vertices
        )
    )


def _project_point(
    x: float,
    y: float,
    z: float,
    tile_width: float,
    tile_height: float,
    z_scale: float,
    origin_x: float,
    origin_y: float,
) -> tuple[float, float]:
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
    return "#{:02x}{:02x}{:02x}".format(
        _clamp_color(red * factor),
        _clamp_color(green * factor),
        _clamp_color(blue * factor),
    )


def _clamp_color(value: float) -> int:
    return max(0, min(255, int(round(value))))


def _transition_wall_display_label(scenario: LongitudinalScenarioConfig) -> tuple[str, str]:
    for feature in scenario.features:
        if feature.name != "transition_wall" or not isinstance(feature, PerforatedBaffleFeatureConfig):
            continue
        if feature.open_area_fraction <= 0.005 or feature.loss_scale >= 4.0:
            return "Blocked transition wall", "Rendered solid for readability"
        return "Transition wall", "Shown as solid display geometry"
    return "Transition wall", "Shown as solid display geometry"
