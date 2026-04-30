from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path

from ..config import PlanViewScenarioConfig
from ..solver.hydraulics import HydraulicFieldData
from .ffmpeg import resolve_ffmpeg_path
from .render_animation import (
    _blank_canvas,
    _draw_line,
    _draw_text,
    _encode_ppm_sequence,
    _fill_rect,
    _stroke_rect,
    _vertical_gradient,
    _write_ppm,
)
from .runtime import detect_render_runtime


@dataclass(frozen=True)
class PathlinePreviewArtifacts:
    frames_dir: str
    manifest_path: str
    poster_path: str
    preview_video_path: str | None
    ffmpeg_path: str | None
    width: int
    height: int
    fps: int
    frame_count: int


@dataclass
class _Particle:
    release_frame: int
    x: float
    y: float
    active: bool
    trail: list[tuple[float, float]]
    speed_m_s: float


def materialize_plan_view_pathline_preview(
    *,
    scenario: PlanViewScenarioConfig,
    fields: HydraulicFieldData,
    media_dir: Path,
    width: int = 854,
    height: int = 480,
    fps: int = 24,
    frame_count: int = 144,
    particle_count: int = 220,
    trail_length: int = 16,
    model_time_shown_s: float | None = None,
) -> PathlinePreviewArtifacts:
    frames_dir = media_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg_path = resolve_ffmpeg_path()
    encoder: str | None = None
    video_args: tuple[str, ...] = ("-c:v", "libx264", "-preset", "veryfast", "-crf", "24")
    if ffmpeg_path:
        try:
            runtime = detect_render_runtime(ffmpeg_path=ffmpeg_path, workers=1)
            ffmpeg_path = runtime.ffmpeg_path
            encoder = runtime.encoder
            video_args = runtime.video_args
        except Exception:
            encoder = None
    manifest_path = media_dir / "pathline_manifest.json"
    poster_path = media_dir / "pathline_poster.ppm"

    base_dt_s = _stable_time_step_s(scenario, fields)
    model_time_shown_s = model_time_shown_s or _target_model_time_shown_s(scenario)
    frame_dt_s = model_time_shown_s / max(1, frame_count)
    substeps_per_frame = max(1, math.ceil(frame_dt_s / max(base_dt_s, 1.0e-9)))
    substep_dt_s = frame_dt_s / substeps_per_frame
    video_duration_s = frame_count / max(fps, 1)
    particles = [_seed_particle(scenario, index) for index in range(particle_count)]
    plot = _plot_rect(width, height)
    guide_paths = _build_guide_paths(
        scenario,
        fields,
        substep_dt_s=substep_dt_s,
        substeps_per_frame=substeps_per_frame,
        point_count=min(220, frame_count),
    )

    for frame_index in range(frame_count):
        image = _blank_canvas(width, height, (241, 245, 249))
        _render_background(
            image,
            width,
            height,
            scenario,
            plot,
            guide_paths,
            model_time_shown_s=model_time_shown_s,
            video_duration_s=video_duration_s,
        )
        for index, particle in enumerate(particles):
            _advance_particle(
                particle=particle,
                scenario=scenario,
                fields=fields,
                substep_dt_s=substep_dt_s,
                substeps_per_frame=substeps_per_frame,
                frame_index=frame_index,
                particle_index=index,
                trail_length=trail_length,
            )
            _render_particle(image, width, scenario, plot, particle)

        frame_path = frames_dir / f"frame_{frame_index:05d}.ppm"
        _write_ppm(frame_path, width, height, image)
        if frame_index == frame_count - 1:
            _write_ppm(poster_path, width, height, image)

    preview_video_path: Path | None = None
    preview_encode_error: str | None = None
    if ffmpeg_path:
        candidate_video_path = media_dir / "pathline_preview.mp4"
        try:
            _encode_ppm_sequence(
                ffmpeg_path=ffmpeg_path,
                frames_dir=frames_dir,
                output_path=candidate_video_path,
                fps=fps,
                video_args=video_args,
            )
            preview_video_path = candidate_video_path
        except RuntimeError as exc:
            preview_encode_error = str(exc)

    manifest = {
        "type": "plan_view_pathline_preview_v1",
        "width": width,
        "height": height,
        "fps": fps,
        "frame_count": frame_count,
        "particle_count": particle_count,
        "trail_length": trail_length,
        "base_time_step_s": base_dt_s,
        "frame_time_step_s": frame_dt_s,
        "substep_time_step_s": substep_dt_s,
        "substeps_per_frame": substeps_per_frame,
        "model_time_shown_s": model_time_shown_s,
        "frames_dir": str(frames_dir),
        "poster_path": str(poster_path),
        "preview_video_path": str(preview_video_path) if preview_video_path else None,
        "ffmpeg_path": ffmpeg_path,
        "encoder": encoder,
        "preview_encode_error": preview_encode_error,
        "notes": [
            "Particles follow deterministic pathlines through a steady screening field.",
            "Model time is compressed so basin routing is visible in a short preview.",
            "This preview is directional and comparative, not a transient CFD or turbulence animation.",
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    return PathlinePreviewArtifacts(
        frames_dir=str(frames_dir),
        manifest_path=str(manifest_path),
        poster_path=str(poster_path),
        preview_video_path=str(preview_video_path) if preview_video_path else None,
        ffmpeg_path=ffmpeg_path,
        width=width,
        height=height,
        fps=fps,
        frame_count=frame_count,
    )


def _advance_particle(
    *,
    particle: _Particle,
    scenario: PlanViewScenarioConfig,
    fields: HydraulicFieldData,
    substep_dt_s: float,
    substeps_per_frame: int,
    frame_index: int,
    particle_index: int,
    trail_length: int,
) -> None:
    if not particle.active:
        if frame_index >= particle.release_frame:
            seeded = _seed_particle(scenario, particle_index, release_frame=frame_index)
            particle.release_frame = seeded.release_frame
            particle.x = seeded.x
            particle.y = seeded.y
            particle.active = True
            particle.trail = seeded.trail
            particle.speed_m_s = seeded.speed_m_s
        else:
            return

    advanced = _advance_position_for_frame(
        scenario=scenario,
        fields=fields,
        x_m=particle.x,
        y_m=particle.y,
        substep_dt_s=substep_dt_s,
        substeps_per_frame=substeps_per_frame,
    )
    if advanced is None:
        particle.active = False
        particle.release_frame = frame_index + 6 + (particle_index % 11)
        particle.trail = []
        particle.speed_m_s = 0.0
        return

    next_x, next_y, speed_m_s = advanced
    particle.x = next_x
    particle.y = next_y
    particle.speed_m_s = speed_m_s
    particle.trail.append((next_x, next_y))
    if len(particle.trail) > trail_length:
        particle.trail = particle.trail[-trail_length:]


def _render_background(
    image: bytearray,
    width: int,
    height: int,
    scenario: PlanViewScenarioConfig,
    plot: tuple[int, int, int, int],
    guide_paths: list[list[tuple[float, float]]],
    model_time_shown_s: float,
    video_duration_s: float,
) -> None:
    _vertical_gradient(image, width, height, (237, 244, 248), (248, 244, 238))
    x0, y0, x1, y1 = plot
    _fill_rect(image, width, x0, y0, x1, y1, (10, 27, 43))
    _stroke_rect(image, width, x0, y0, x1, y1, (180, 203, 221), 2)
    _draw_text(image, width, 34, 24, scenario.metadata.title.upper(), scale=2, color=(15, 23, 42))
    _draw_text(image, width, 34, 50, "STEADY SCREENING PATHLINES", scale=1, color=(51, 65, 85))
    _draw_text(
        image,
        width,
        34,
        64,
        f"SHOWS {model_time_shown_s / 3600.0:.1f} H MODEL TIME IN {video_duration_s:.1f} S",
        scale=1,
        color=(71, 85, 105),
    )
    _draw_text(image, width, 34, height - 42, "DETERMINISTIC PATHLINES THROUGH A STEADY FIELD", scale=1, color=(51, 65, 85))
    _draw_text(image, width, 34, height - 24, "DIRECTIONAL SCREENING VIEW, NOT TRANSIENT CFD", scale=1, color=(51, 65, 85))

    for guide_path in guide_paths:
        for index in range(1, len(guide_path)):
            x_a, y_a = _project_point(plot, scenario, *guide_path[index - 1])
            x_b, y_b = _project_point(plot, scenario, *guide_path[index])
            _draw_line(image, width, x_a, y_a, x_b, y_b, (55, 86, 110), 1)

    for baffle in scenario.baffles:
        x_a, y_a = _project_point(plot, scenario, baffle.x1_m, baffle.y1_m)
        x_b, y_b = _project_point(plot, scenario, baffle.x2_m, baffle.y2_m)
        _draw_line(image, width, x_a, y_a, x_b, y_b, (226, 232, 240), 4)

    inlet_lower = scenario.inlet.center_m - (scenario.inlet.span_m / 2.0)
    inlet_upper = scenario.inlet.center_m + (scenario.inlet.span_m / 2.0)
    outlet_lower = scenario.outlet.center_m - (scenario.outlet.span_m / 2.0)
    outlet_upper = scenario.outlet.center_m + (scenario.outlet.span_m / 2.0)
    if scenario.inlet.side == "west":
        _, inlet_y0 = _project_point(plot, scenario, 0.0, inlet_lower)
        _, inlet_y1 = _project_point(plot, scenario, 0.0, inlet_upper)
        _draw_line(image, width, x0, inlet_y0, x0, inlet_y1, (34, 197, 94), 5)
    if scenario.outlet.side == "east":
        _, outlet_y0 = _project_point(plot, scenario, scenario.geometry.length_m, outlet_lower)
        _, outlet_y1 = _project_point(plot, scenario, scenario.geometry.length_m, outlet_upper)
        _draw_line(image, width, x1, outlet_y0, x1, outlet_y1, (239, 68, 68), 5)


def _render_particle(
    image: bytearray,
    width: int,
    scenario: PlanViewScenarioConfig,
    plot: tuple[int, int, int, int],
    particle: _Particle,
) -> None:
    if len(particle.trail) < 2:
        return

    color = _speed_color(particle.speed_m_s)
    for index in range(1, len(particle.trail)):
        x_a, y_a = _project_point(plot, scenario, *particle.trail[index - 1])
        x_b, y_b = _project_point(plot, scenario, *particle.trail[index])
        thickness = 1 if index < len(particle.trail) - 3 else 2
        _draw_line(image, width, x_a, y_a, x_b, y_b, color, thickness)

    x, y = _project_point(plot, scenario, particle.x, particle.y)
    _fill_rect(image, width, x - 2, y - 2, x + 3, y + 3, (255, 255, 255))


def _rk4_step(
    fields: HydraulicFieldData,
    scenario: PlanViewScenarioConfig,
    x_m: float,
    y_m: float,
    dt_s: float,
) -> tuple[float, float, float]:
    u1, v1 = _sample_velocity(fields, scenario, x_m, y_m)
    u2, v2 = _sample_velocity(fields, scenario, x_m + 0.5 * dt_s * u1, y_m + 0.5 * dt_s * v1)
    u3, v3 = _sample_velocity(fields, scenario, x_m + 0.5 * dt_s * u2, y_m + 0.5 * dt_s * v2)
    u4, v4 = _sample_velocity(fields, scenario, x_m + dt_s * u3, y_m + dt_s * v3)
    u = (u1 + (2.0 * u2) + (2.0 * u3) + u4) / 6.0
    v = (v1 + (2.0 * v2) + (2.0 * v3) + v4) / 6.0
    next_x = x_m + (dt_s * u)
    next_y = y_m + (dt_s * v)
    return next_x, next_y, math.sqrt((u * u) + (v * v))


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


def _seed_particle(
    scenario: PlanViewScenarioConfig,
    index: int,
    *,
    release_frame: int | None = None,
) -> _Particle:
    fraction = (((index * 37) % 997) % 200) / 199.0
    inlet_lower = scenario.inlet.center_m - (scenario.inlet.span_m / 2.0)
    inlet_upper = scenario.inlet.center_m + (scenario.inlet.span_m / 2.0)
    y = inlet_lower + fraction * (inlet_upper - inlet_lower)
    x = min(scenario.geometry.length_m - 1.0e-6, max(1.0e-6, 0.015 * scenario.geometry.length_m))
    return _Particle(
        release_frame=index % 36 if release_frame is None else release_frame,
        x=x,
        y=y,
        active=False if release_frame is None else True,
        trail=[] if release_frame is None else [(x, y)],
        speed_m_s=0.0,
    )


def _stable_time_step_s(scenario: PlanViewScenarioConfig, fields: HydraulicFieldData) -> float:
    nx = max(1, len(fields.x_centers_m))
    ny = max(1, len(fields.y_centers_m))
    dx_m = scenario.geometry.length_m / nx
    dy_m = scenario.geometry.width_m / ny
    max_speed = max(max(row) for row in fields.speed_m_s)
    if max_speed <= 1.0e-9:
        return 0.5
    return max(0.05, min(0.75, 0.75 * min(dx_m, dy_m) / max_speed))


def _build_guide_paths(
    scenario: PlanViewScenarioConfig,
    fields: HydraulicFieldData,
    *,
    substep_dt_s: float,
    substeps_per_frame: int,
    point_count: int,
) -> list[list[tuple[float, float]]]:
    inlet_lower = scenario.inlet.center_m - (scenario.inlet.span_m / 2.0)
    inlet_upper = scenario.inlet.center_m + (scenario.inlet.span_m / 2.0)
    paths: list[list[tuple[float, float]]] = []
    for index in range(7):
        fraction = index / 6.0
        x_m = max(1.0e-4, 0.012 * scenario.geometry.length_m)
        y_m = inlet_lower + fraction * (inlet_upper - inlet_lower)
        path: list[tuple[float, float]] = [(x_m, y_m)]
        for _ in range(point_count):
            advanced = _advance_position_for_frame(
                scenario=scenario,
                fields=fields,
                x_m=x_m,
                y_m=y_m,
                substep_dt_s=substep_dt_s,
                substeps_per_frame=substeps_per_frame,
            )
            if advanced is None:
                break
            next_x, next_y, _speed_m_s = advanced
            path.append((next_x, next_y))
            x_m = next_x
            y_m = next_y
        if len(path) > 1:
            paths.append(path)
    return paths


def _advance_position_for_frame(
    *,
    scenario: PlanViewScenarioConfig,
    fields: HydraulicFieldData,
    x_m: float,
    y_m: float,
    substep_dt_s: float,
    substeps_per_frame: int,
) -> tuple[float, float, float] | None:
    current_x = x_m
    current_y = y_m
    speed_m_s = 0.0
    for _ in range(substeps_per_frame):
        next_x, next_y, speed_m_s = _rk4_step(fields, scenario, current_x, current_y, substep_dt_s)
        if (
            speed_m_s <= 1.0e-9
            or not _inside_basin(scenario, next_x, next_y)
            or _hits_baffle(scenario, next_x, next_y)
        ):
            return None
        current_x = next_x
        current_y = next_y
    return current_x, current_y, speed_m_s


def _target_model_time_shown_s(scenario: PlanViewScenarioConfig) -> float:
    theoretical_detention_time_s = (
        scenario.geometry.length_m
        * scenario.geometry.width_m
        * scenario.geometry.water_depth_m
        / scenario.hydraulics.flow_rate_m3_s
    )
    return max(900.0, 0.5 * theoretical_detention_time_s)


def _inside_basin(scenario: PlanViewScenarioConfig, x_m: float, y_m: float) -> bool:
    return 0.0 <= x_m <= scenario.geometry.length_m and 0.0 <= y_m <= scenario.geometry.width_m


def _hits_baffle(scenario: PlanViewScenarioConfig, x_m: float, y_m: float) -> bool:
    for baffle in scenario.baffles:
        if baffle.x1_m == baffle.x2_m:
            if abs(x_m - baffle.x1_m) <= 0.12 and min(baffle.y1_m, baffle.y2_m) <= y_m <= max(baffle.y1_m, baffle.y2_m):
                return True
        elif abs(y_m - baffle.y1_m) <= 0.12 and min(baffle.x1_m, baffle.x2_m) <= x_m <= max(baffle.x1_m, baffle.x2_m):
            return True
    return False


def _plot_rect(width: int, height: int) -> tuple[int, int, int, int]:
    return (52, 68, width - 34, height - 72)


def _project_point(
    plot: tuple[int, int, int, int],
    scenario: PlanViewScenarioConfig,
    x_m: float,
    y_m: float,
) -> tuple[int, int]:
    x0, y0, x1, y1 = plot
    px = x0 + int((x_m / scenario.geometry.length_m) * (x1 - x0))
    py = y1 - int((y_m / scenario.geometry.width_m) * (y1 - y0))
    return px, py


def _speed_color(speed_m_s: float) -> tuple[int, int, int]:
    if speed_m_s <= 0.02:
        return (125, 211, 252)
    if speed_m_s <= 0.06:
        return (96, 165, 250)
    if speed_m_s <= 0.12:
        return (248, 250, 252)
    return (251, 146, 60)
