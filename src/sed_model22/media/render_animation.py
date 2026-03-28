from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess

from ..config import LongitudinalScenarioConfig, PlanViewScenarioConfig
from ..solver.hydraulics import HydraulicFieldData
from ..solver.longitudinal import LongitudinalFieldData, LongitudinalTracerSummary
from .guardrails import RenderBudget, RenderMonitor, check_render_safety
from .runtime import detect_render_runtime, smoke_test_workers


@dataclass(frozen=True)
class AnimationArtifacts:
    frames_dir: str
    manifest_path: str
    preview_video_path: str
    ffmpeg_path: str
    width: int
    height: int
    fps: int
    frame_count: int


@dataclass(frozen=True)
class _Shot:
    name: str
    frame_count: int


def materialize_plan_view_preview_animation(
    *,
    scenario: PlanViewScenarioConfig,
    fields: HydraulicFieldData,
    media_dir: Path,
    width: int = 854,
    height: int = 480,
    fps: int = 12,
    max_wall_time_s: float = 180.0,
) -> AnimationArtifacts:
    runtime = detect_render_runtime(workers=1)
    if not smoke_test_workers(runtime.workers):
        runtime = detect_render_runtime(workers=1)

    total_frames = 144
    budget = RenderBudget(
        width=width,
        height=height,
        frame_count=total_frames,
        complexity=1.05,
        max_wall_time_s=max_wall_time_s,
    )
    safe, estimate_s, recommendation = check_render_safety(budget)
    if not safe:
        raise RuntimeError(f"preview render aborted before start: {recommendation}")

    frames_dir = media_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    monitor = RenderMonitor(total_frames, timeout_seconds=max_wall_time_s)
    manifest_path = media_dir / "animation_manifest.json"

    plot = _plan_view_plot_area(width, height)
    particles = _seed_plan_view_particles(scenario, fields, 180)
    for frame_index in range(total_frames):
        monitor.check_frame(frame_index)
        image = _blank_canvas(width, height, (239, 245, 248))
        _render_plan_view_frame(image, width, height, scenario, fields, plot, particles)
        _write_ppm(frames_dir / f"frame_{frame_index:05d}.ppm", width, height, image)
        _advance_plan_view_particles(particles, scenario, fields)
        if frame_index % max(1, fps * 2) == 0:
            print(f"  preview render: {monitor.progress_str(frame_index)}")

    preview_video_path = media_dir / "preview.mp4"
    _encode_ppm_sequence(
        ffmpeg_path=runtime.ffmpeg_path,
        frames_dir=frames_dir,
        output_path=preview_video_path,
        fps=fps,
        video_args=runtime.video_args,
    )

    manifest = {
        "type": "plan_view_preview_animation_v1",
        "width": width,
        "height": height,
        "fps": fps,
        "frame_count": total_frames,
        "estimated_render_time_s": round(estimate_s, 2),
        "ffmpeg_path": runtime.ffmpeg_path,
        "encoder": runtime.encoder,
        "workers": runtime.workers,
        "frames_dir": str(frames_dir),
        "preview_video_path": str(preview_video_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    return AnimationArtifacts(
        frames_dir=str(frames_dir),
        manifest_path=str(manifest_path),
        preview_video_path=str(preview_video_path),
        ffmpeg_path=runtime.ffmpeg_path,
        width=width,
        height=height,
        fps=fps,
        frame_count=total_frames,
    )


def materialize_longitudinal_preview_animation(
    *,
    scenario: LongitudinalScenarioConfig,
    fields: LongitudinalFieldData,
    tracer: LongitudinalTracerSummary,
    summary: dict,
    media_dir: Path,
    width: int = 854,
    height: int = 480,
    fps: int = 10,
    max_wall_time_s: float = 180.0,
) -> AnimationArtifacts:
    runtime = detect_render_runtime(workers=1)
    if not smoke_test_workers(runtime.workers):
        runtime = detect_render_runtime(workers=1)

    shots = [
        _Shot("title", 14),
        _Shot("basin_reveal", 42),
        _Shot("tracer_curve", 32),
        _Shot("metrics", 24),
    ]
    total_frames = sum(shot.frame_count for shot in shots)
    budget = RenderBudget(
        width=width,
        height=height,
        frame_count=total_frames,
        complexity=1.15,
        max_wall_time_s=max_wall_time_s,
    )
    safe, estimate_s, recommendation = check_render_safety(budget)
    if not safe:
        raise RuntimeError(f"preview render aborted before start: {recommendation}")

    frames_dir = media_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    monitor = RenderMonitor(total_frames, timeout_seconds=max_wall_time_s)
    manifest_path = media_dir / "animation_manifest.json"

    max_speed = _max_nested(fields.speed_m_s)
    max_time = max(tracer.time_points_s[-1] if tracer.time_points_s else 1.0, 1.0)
    max_concentration = max(max(tracer.outlet_concentration_history, default=1.0), 1.0)
    metric_lines = _metric_lines(summary)

    frame_index = 0
    last_heartbeat = -1
    for shot in shots:
        for shot_index in range(shot.frame_count):
            monitor.check_frame(frame_index)
            image = _blank_canvas(width, height, (242, 246, 250))
            if shot.name == "title":
                _render_title_frame(image, width, height, scenario, shot_index / max(1, shot.frame_count - 1))
            elif shot.name == "basin_reveal":
                _render_basin_frame(
                    image,
                    width,
                    height,
                    scenario,
                    fields,
                    reveal_fraction=(shot_index + 1) / shot.frame_count,
                    max_speed=max_speed,
                )
            elif shot.name == "tracer_curve":
                _render_tracer_frame(
                    image,
                    width,
                    height,
                    tracer,
                    draw_fraction=(shot_index + 1) / shot.frame_count,
                    max_time=max_time,
                    max_concentration=max_concentration,
                )
            else:
                _render_metrics_frame(image, width, height, scenario, metric_lines, shot_index / max(1, shot.frame_count - 1))

            _write_ppm(frames_dir / f"frame_{frame_index:05d}.ppm", width, height, image)
            heartbeat = frame_index // max(1, fps * 2)
            if heartbeat != last_heartbeat:
                print(f"  preview render: {monitor.progress_str(frame_index)}")
                last_heartbeat = heartbeat
            frame_index += 1

    preview_video_path = media_dir / "preview.mp4"
    _encode_ppm_sequence(
        ffmpeg_path=runtime.ffmpeg_path,
        frames_dir=frames_dir,
        output_path=preview_video_path,
        fps=fps,
        video_args=runtime.video_args,
    )

    manifest = {
        "type": "longitudinal_preview_animation_v1",
        "width": width,
        "height": height,
        "fps": fps,
        "frame_count": total_frames,
        "estimated_render_time_s": round(estimate_s, 2),
        "shots": [shot.__dict__ for shot in shots],
        "ffmpeg_path": runtime.ffmpeg_path,
        "encoder": runtime.encoder,
        "workers": runtime.workers,
        "frames_dir": str(frames_dir),
        "preview_video_path": str(preview_video_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    return AnimationArtifacts(
        frames_dir=str(frames_dir),
        manifest_path=str(manifest_path),
        preview_video_path=str(preview_video_path),
        ffmpeg_path=runtime.ffmpeg_path,
        width=width,
        height=height,
        fps=fps,
        frame_count=total_frames,
    )


def _render_title_frame(
    image: bytearray,
    width: int,
    height: int,
    scenario: LongitudinalScenarioConfig,
    alpha: float,
) -> None:
    _vertical_gradient(image, width, height, (236, 244, 252), (247, 243, 236))
    panel = (36, 46, width - 36, height - 42)
    _fill_rect(image, width, *panel, (255, 255, 255))
    _stroke_rect(image, width, *panel, (212, 222, 232), 2)
    band_width = max(1, int((width - 72) * min(1.0, 0.15 + alpha)))
    _fill_rect(image, width, 36, 46, 36 + band_width, 54, (78, 153, 211))
    _draw_text(image, width, 66, 88, scenario.metadata.title.upper(), scale=4, color=(15, 23, 42))
    _draw_text(image, width, 66, 146, scenario.metadata.case_id.upper(), scale=2, color=(71, 85, 105))
    _draw_text(image, width, 66, 178, "LONGITUDINAL SCREENING PREVIEW", scale=2, color=(51, 65, 85))
    _draw_text(image, width, 66, 214, "480P LOW-RES PREVIEW FOR ITERATION", scale=2, color=(100, 116, 139))


def _render_basin_frame(
    image: bytearray,
    width: int,
    height: int,
    scenario: LongitudinalScenarioConfig,
    fields: LongitudinalFieldData,
    *,
    reveal_fraction: float,
    max_speed: float,
) -> None:
    _vertical_gradient(image, width, height, (244, 248, 252), (236, 242, 247))
    panel_x0 = 48
    panel_y0 = 60
    panel_x1 = width - 48
    panel_y1 = height - 72
    _fill_rect(image, width, panel_x0, panel_y0, panel_x1, panel_y1, (255, 255, 255))
    _stroke_rect(image, width, panel_x0, panel_y0, panel_x1, panel_y1, (210, 220, 230), 2)
    _draw_text(image, width, panel_x0 + 18, 74, "BASIN FIELD REVEAL", scale=2, color=(15, 23, 42))

    plot_x0 = panel_x0 + 18
    plot_y0 = panel_y0 + 34
    plot_x1 = panel_x1 - 18
    plot_y1 = panel_y1 - 18
    _fill_rect(image, width, plot_x0, plot_y0, plot_x1, plot_y1, (228, 238, 246))
    _stroke_rect(image, width, plot_x0, plot_y0, plot_x1, plot_y1, (40, 52, 64), 2)

    nx = len(fields.x_centers_m)
    nz = len(fields.z_centers_m)
    reveal_columns = max(1, min(nx, int(nx * reveal_fraction)))
    cell_w = max(1, (plot_x1 - plot_x0) // max(1, nx))
    cell_h = max(1, (plot_y1 - plot_y0) // max(1, nz))
    for ix in range(reveal_columns):
        for iz in range(nz):
            speed = fields.speed_m_s[ix][iz]
            color = _speed_color(speed / max(1.0e-9, max_speed))
            x0 = plot_x0 + ix * cell_w
            x1 = min(plot_x1, x0 + cell_w)
            y1 = plot_y1 - iz * cell_h
            y0 = max(plot_y0, y1 - cell_h)
            _fill_rect(image, width, x0, y0, x1, y1, color)

    for feature in scenario.features:
        if feature.kind in {"perforated_baffle", "solid_baffle"}:
            x = plot_x0 + int((feature.x_m / scenario.geometry.basin_length_m) * (plot_x1 - plot_x0))
            y0 = plot_y1 - int((feature.z_top_m / scenario.geometry.water_depth_m) * (plot_y1 - plot_y0))
            y1 = plot_y1 - int((feature.z_bottom_m / scenario.geometry.water_depth_m) * (plot_y1 - plot_y0))
            _draw_vertical_line(image, width, x, y0, y1, (210, 106, 59), 3)
        elif feature.kind == "plate_settler_zone":
            x0 = plot_x0 + int((feature.x_start_m / scenario.geometry.basin_length_m) * (plot_x1 - plot_x0))
            x1 = plot_x0 + int((feature.x_end_m / scenario.geometry.basin_length_m) * (plot_x1 - plot_x0))
            y0 = plot_y1 - int((feature.z_top_m / scenario.geometry.water_depth_m) * (plot_y1 - plot_y0))
            y1 = plot_y1 - int((feature.z_bottom_m / scenario.geometry.water_depth_m) * (plot_y1 - plot_y0))
            _stroke_rect(image, width, x0, y0, x1, y1, (2, 132, 199), 2)
        elif feature.kind == "launder_zone":
            x0 = plot_x0 + int((feature.x_start_m / scenario.geometry.basin_length_m) * (plot_x1 - plot_x0))
            x1 = plot_x0 + int((feature.x_end_m / scenario.geometry.basin_length_m) * (plot_x1 - plot_x0))
            _fill_rect(image, width, x0, plot_y0, x1, plot_y0 + 6, (239, 68, 68))

    _draw_text(image, width, plot_x0 + 8, plot_y0 + 8, "FLOW FIELD", scale=2, color=(15, 23, 42))
    _draw_text(image, width, plot_x0 + 8, plot_y0 + 34, f"REVEAL {int(reveal_fraction * 100):02d} PERCENT", scale=1, color=(71, 85, 105))


def _render_tracer_frame(
    image: bytearray,
    width: int,
    height: int,
    tracer: LongitudinalTracerSummary,
    *,
    draw_fraction: float,
    max_time: float,
    max_concentration: float,
) -> None:
    _vertical_gradient(image, width, height, (246, 248, 251), (236, 244, 242))
    panel_x0 = 48
    panel_y0 = 60
    panel_x1 = width - 48
    panel_y1 = height - 72
    _fill_rect(image, width, panel_x0, panel_y0, panel_x1, panel_y1, (255, 255, 255))
    _stroke_rect(image, width, panel_x0, panel_y0, panel_x1, panel_y1, (210, 220, 230), 2)
    _draw_text(image, width, panel_x0 + 18, 74, "TRACER BREAKTHROUGH", scale=2, color=(15, 23, 42))

    plot_x0 = panel_x0 + 22
    plot_y0 = panel_y0 + 42
    plot_x1 = panel_x1 - 18
    plot_y1 = panel_y1 - 20
    _fill_rect(image, width, plot_x0, plot_y0, plot_x1, plot_y1, (250, 252, 255))
    _stroke_rect(image, width, plot_x0, plot_y0, plot_x1, plot_y1, (40, 52, 64), 2)

    _draw_horizontal_line(image, width, plot_x0, plot_x1, plot_y1, (148, 163, 184), 1)
    _draw_horizontal_line(image, width, plot_x0, plot_x1, plot_y0 + (plot_y1 - plot_y0) // 2, (203, 213, 225), 1)

    point_count = max(2, int(len(tracer.time_points_s) * draw_fraction))
    points = list(zip(tracer.time_points_s[:point_count], tracer.outlet_concentration_history[:point_count]))
    last_px: tuple[int, int] | None = None
    for time_s, concentration in points:
        x = plot_x0 + int((time_s / max_time) * (plot_x1 - plot_x0))
        y = plot_y1 - int((concentration / max_concentration) * (plot_y1 - plot_y0))
        if last_px is not None:
            _draw_line(image, width, last_px[0], last_px[1], x, y, (30, 64, 175), 2)
        last_px = (x, y)

    _draw_text(image, width, plot_x0 + 8, plot_y0 + 8, f"T10 {int(tracer.t10_s)}S", scale=1, color=(15, 118, 110))
    _draw_text(image, width, plot_x0 + 120, plot_y0 + 8, f"T50 {int(tracer.t50_s)}S", scale=1, color=(124, 58, 237))
    _draw_text(image, width, plot_x0 + 240, plot_y0 + 8, f"T90 {int(tracer.t90_s)}S", scale=1, color=(220, 38, 38))


def _render_metrics_frame(
    image: bytearray,
    width: int,
    height: int,
    scenario: LongitudinalScenarioConfig,
    metric_lines: list[str],
    alpha: float,
) -> None:
    _vertical_gradient(image, width, height, (247, 245, 240), (243, 247, 252))
    panel_x0 = 54
    panel_y0 = 54
    panel_x1 = width - 54
    panel_y1 = height - 54
    _fill_rect(image, width, panel_x0, panel_y0, panel_x1, panel_y1, (255, 255, 255))
    _stroke_rect(image, width, panel_x0, panel_y0, panel_x1, panel_y1, (220, 212, 203), 2)
    _draw_text(image, width, panel_x0 + 18, 74, "SCREENING METRICS", scale=2, color=(15, 23, 42))
    _draw_text(image, width, panel_x0 + 18, 104, scenario.metadata.case_id.upper(), scale=1, color=(100, 116, 139))
    bar_w = int((panel_x1 - panel_x0 - 36) * min(1.0, 0.2 + alpha))
    _fill_rect(image, width, panel_x0 + 18, 118, panel_x0 + 18 + bar_w, 124, (210, 106, 59))
    for index, line in enumerate(metric_lines):
        _draw_text(image, width, panel_x0 + 24, 154 + index * 42, line, scale=2, color=(51, 65, 85))


def _metric_lines(summary: dict) -> list[str]:
    metrics = summary["metrics"]
    return [
        f"FLOW {summary['hydraulics']['flow_rate_m3_s']:.2f} M3/S",
        f"HEADLOSS {metrics['transition_headloss_m']:.3f} M",
        f"POST VUI {metrics['post_transition_velocity_uniformity_index']:.3f}",
        f"LAUNDER UP {metrics['launder_peak_upward_velocity_m_s']:.4f} M/S",
        f"SHORT CIRCUIT {metrics['short_circuiting_index']:.3f}",
    ]


def _encode_ppm_sequence(
    *,
    ffmpeg_path: str,
    frames_dir: Path,
    output_path: Path,
    fps: int,
    video_args: tuple[str, ...],
) -> None:
    command = [
        ffmpeg_path,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-framerate",
        str(fps),
        "-i",
        str(frames_dir / "frame_%05d.ppm"),
        *video_args,
        "-pix_fmt",
        "yuv420p",
        str(output_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg animation encode failed: {result.stderr.strip()}")


def _blank_canvas(width: int, height: int, color: tuple[int, int, int]) -> bytearray:
    return bytearray(color * (width * height))


def _write_ppm(path: Path, width: int, height: int, pixels: bytearray) -> None:
    header = f"P6\n{width} {height}\n255\n".encode("ascii")
    path.write_bytes(header + pixels)


def _vertical_gradient(image: bytearray, width: int, height: int, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> None:
    for y in range(height):
        mix = y / max(1, height - 1)
        color = tuple(int(round(top[index] * (1.0 - mix) + bottom[index] * mix)) for index in range(3))
        _fill_rect(image, width, 0, y, width, y + 1, color)


def _fill_rect(
    image: bytearray,
    width: int,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    color: tuple[int, int, int],
) -> None:
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = max(x0, x1)
    y1 = max(y0, y1)
    row_bytes = width * 3
    color_bytes = bytes(color)
    for y in range(y0, y1):
        offset = y * row_bytes + x0 * 3
        image[offset : offset + (x1 - x0) * 3] = color_bytes * (x1 - x0)


def _stroke_rect(
    image: bytearray,
    width: int,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    color: tuple[int, int, int],
    thickness: int,
) -> None:
    _fill_rect(image, width, x0, y0, x1, y0 + thickness, color)
    _fill_rect(image, width, x0, y1 - thickness, x1, y1, color)
    _fill_rect(image, width, x0, y0, x0 + thickness, y1, color)
    _fill_rect(image, width, x1 - thickness, y0, x1, y1, color)


def _draw_vertical_line(image: bytearray, width: int, x: int, y0: int, y1: int, color: tuple[int, int, int], thickness: int) -> None:
    _fill_rect(image, width, x - thickness // 2, min(y0, y1), x + thickness // 2 + 1, max(y0, y1) + 1, color)


def _draw_horizontal_line(image: bytearray, width: int, x0: int, x1: int, y: int, color: tuple[int, int, int], thickness: int) -> None:
    _fill_rect(image, width, min(x0, x1), y - thickness // 2, max(x0, x1) + 1, y + thickness // 2 + 1, color)


def _draw_line(
    image: bytearray,
    width: int,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    color: tuple[int, int, int],
    thickness: int,
) -> None:
    dx = abs(x1 - x0)
    sx = 1 if x0 < x1 else -1
    dy = -abs(y1 - y0)
    sy = 1 if y0 < y1 else -1
    error = dx + dy
    while True:
        _fill_rect(image, width, x0 - thickness // 2, y0 - thickness // 2, x0 + thickness // 2 + 1, y0 + thickness // 2 + 1, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * error
        if e2 >= dy:
            error += dy
            x0 += sx
        if e2 <= dx:
            error += dx
            y0 += sy


def _draw_text(
    image: bytearray,
    width: int,
    x: int,
    y: int,
    text: str,
    *,
    scale: int,
    color: tuple[int, int, int],
) -> None:
    cursor = x
    for char in text.upper():
        glyph = _FONT.get(char, _FONT["?"])
        for row_index, row in enumerate(glyph):
            for col_index, value in enumerate(row):
                if value == "1":
                    _fill_rect(
                        image,
                        width,
                        cursor + col_index * scale,
                        y + row_index * scale,
                        cursor + (col_index + 1) * scale,
                        y + (row_index + 1) * scale,
                        color,
                    )
        cursor += (len(glyph[0]) + 1) * scale


def _max_nested(values: list[list[float]]) -> float:
    maximum = max((max(row) for row in values), default=0.0)
    return maximum if maximum > 0.0 else 1.0


def _speed_color(normalized_speed: float) -> tuple[int, int, int]:
    value = max(0.0, min(1.0, normalized_speed))
    if value <= 0.25:
        return (216, 239, 247)
    if value <= 0.5:
        return (139, 211, 230)
    if value <= 0.75:
        return (78, 153, 211)
    return (210, 106, 59)


_FONT = {
    " ": ["000", "000", "000", "000", "000", "000", "000"],
    "-": ["000", "000", "000", "111", "000", "000", "000"],
    ".": ["0", "0", "0", "0", "0", "1", "1"],
    "/": ["001", "001", "010", "010", "100", "100", "000"],
    ":": ["0", "1", "1", "0", "1", "1", "0"],
    "%": ["11001", "11010", "00100", "01000", "10011", "00011", "00000"],
    "?": ["111", "001", "010", "010", "000", "010", "000"],
    "0": ["111", "101", "101", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "010", "010", "111"],
    "2": ["111", "001", "001", "111", "100", "100", "111"],
    "3": ["111", "001", "001", "111", "001", "001", "111"],
    "4": ["101", "101", "101", "111", "001", "001", "001"],
    "5": ["111", "100", "100", "111", "001", "001", "111"],
    "6": ["111", "100", "100", "111", "101", "101", "111"],
    "7": ["111", "001", "001", "010", "010", "010", "010"],
    "8": ["111", "101", "101", "111", "101", "101", "111"],
    "9": ["111", "101", "101", "111", "001", "001", "111"],
    "A": ["111", "101", "101", "111", "101", "101", "101"],
    "B": ["110", "101", "101", "110", "101", "101", "110"],
    "C": ["111", "100", "100", "100", "100", "100", "111"],
    "D": ["110", "101", "101", "101", "101", "101", "110"],
    "E": ["111", "100", "100", "110", "100", "100", "111"],
    "F": ["111", "100", "100", "110", "100", "100", "100"],
    "G": ["111", "100", "100", "101", "101", "101", "111"],
    "H": ["101", "101", "101", "111", "101", "101", "101"],
    "I": ["111", "010", "010", "010", "010", "010", "111"],
    "J": ["111", "001", "001", "001", "001", "101", "111"],
    "K": ["101", "101", "110", "100", "110", "101", "101"],
    "L": ["100", "100", "100", "100", "100", "100", "111"],
    "M": ["101", "111", "111", "101", "101", "101", "101"],
    "N": ["101", "111", "111", "111", "111", "111", "101"],
    "O": ["111", "101", "101", "101", "101", "101", "111"],
    "P": ["111", "101", "101", "111", "100", "100", "100"],
    "Q": ["111", "101", "101", "101", "111", "001", "001"],
    "R": ["111", "101", "101", "111", "110", "101", "101"],
    "S": ["111", "100", "100", "111", "001", "001", "111"],
    "T": ["111", "010", "010", "010", "010", "010", "010"],
    "U": ["101", "101", "101", "101", "101", "101", "111"],
    "V": ["101", "101", "101", "101", "101", "101", "010"],
    "W": ["101", "101", "101", "101", "111", "111", "101"],
    "X": ["101", "101", "101", "010", "101", "101", "101"],
    "Y": ["101", "101", "101", "010", "010", "010", "010"],
    "Z": ["111", "001", "001", "010", "100", "100", "111"],
}


def _plan_view_plot_area(width: int, height: int) -> tuple[int, int, int, int]:
    return (72, 44, width - 72, height - 44)


def _render_plan_view_frame(
    image: bytearray,
    width: int,
    height: int,
    scenario: PlanViewScenarioConfig,
    fields: HydraulicFieldData,
    plot: tuple[int, int, int, int],
    particles: list[dict[str, object]],
) -> None:
    _vertical_gradient(image, width, height, (238, 245, 249), (246, 242, 236))
    x0, y0, x1, y1 = plot
    _fill_rect(image, width, x0, y0, x1, y1, (250, 252, 255))
    _stroke_rect(image, width, x0, y0, x1, y1, (120, 142, 160), 2)

    nx = len(fields.x_centers_m)
    ny = len(fields.y_centers_m)
    cell_w = max(1, (x1 - x0) // max(1, nx))
    cell_h = max(1, (y1 - y0) // max(1, ny))
    max_speed = _max_nested(fields.speed_m_s)
    for ix in range(nx):
        for iy in range(ny):
            color = _plan_speed_color(fields.speed_m_s[ix][iy] / max_speed)
            rx0 = x0 + ix * cell_w
            rx1 = min(x1, rx0 + cell_w)
            ry0 = y0 + iy * cell_h
            ry1 = min(y1, ry0 + cell_h)
            _fill_rect(image, width, rx0, ry0, rx1, ry1, color)

    for baffle in scenario.baffles:
        if baffle.x1_m == baffle.x2_m:
            bx = x0 + int((baffle.x1_m / scenario.geometry.length_m) * (x1 - x0))
            by0 = y0 + int((min(baffle.y1_m, baffle.y2_m) / scenario.geometry.width_m) * (y1 - y0))
            by1 = y0 + int((max(baffle.y1_m, baffle.y2_m) / scenario.geometry.width_m) * (y1 - y0))
            _fill_rect(image, width, bx - 2, by0, bx + 3, by1, (32, 39, 48))
        else:
            by = y0 + int((baffle.y1_m / scenario.geometry.width_m) * (y1 - y0))
            bx0 = x0 + int((min(baffle.x1_m, baffle.x2_m) / scenario.geometry.length_m) * (x1 - x0))
            bx1 = x0 + int((max(baffle.x1_m, baffle.x2_m) / scenario.geometry.length_m) * (x1 - x0))
            _fill_rect(image, width, bx0, by - 2, bx1, by + 3, (32, 39, 48))

    for particle in particles:
        trail = particle["trail"]
        for index, position in enumerate(trail):
            px = x0 + int((position[0] / scenario.geometry.length_m) * (x1 - x0))
            py = y0 + int((position[1] / scenario.geometry.width_m) * (y1 - y0))
            radius = 1 if index < len(trail) - 1 else 2
            color = (90, 160, 220) if index < len(trail) - 1 else (220, 245, 255)
            _fill_rect(image, width, px - radius, py - radius, px + radius + 1, py + radius + 1, color)


def _seed_plan_view_particles(
    scenario: PlanViewScenarioConfig,
    fields: HydraulicFieldData,
    count: int,
) -> list[dict[str, object]]:
    particles: list[dict[str, object]] = []
    inlet_min = scenario.inlet.center_m - scenario.inlet.span_m / 2.0
    inlet_max = scenario.inlet.center_m + scenario.inlet.span_m / 2.0
    for index in range(count):
        fraction = ((index * 37) % count) / max(1, count - 1)
        y = inlet_min + fraction * (inlet_max - inlet_min)
        x = 0.8 + ((index * 19) % 11) * 0.08
        particles.append({"x": x, "y": y, "trail": [(x, y)], "age": 0})
    return particles


def _advance_plan_view_particles(
    particles: list[dict[str, object]],
    scenario: PlanViewScenarioConfig,
    fields: HydraulicFieldData,
) -> None:
    for index, particle in enumerate(particles):
        x = float(particle["x"])
        y = float(particle["y"])
        u, v = _sample_plan_velocity(fields, scenario, x, y)
        speed = max(0.02, (u * u + v * v) ** 0.5)
        step = min(1.25, max(0.12, speed * 5.0))
        new_x = x + u * step
        new_y = y + v * step

        if _hits_baffle(new_x, new_y, scenario):
            new_x = x
            new_y = y + 0.35 * (1 if (index % 2 == 0) else -1)

        particle["x"] = new_x
        particle["y"] = new_y
        particle["age"] = int(particle["age"]) + 1
        trail = list(particle["trail"])
        trail.append((new_x, new_y))
        particle["trail"] = trail[-6:]

        if (
            new_x < 0.0
            or new_x > scenario.geometry.length_m
            or new_y < 0.0
            or new_y > scenario.geometry.width_m
            or int(particle["age"]) > 80
        ):
            _reset_particle(particle, scenario, index)


def _sample_plan_velocity(
    fields: HydraulicFieldData,
    scenario: PlanViewScenarioConfig,
    x: float,
    y: float,
) -> tuple[float, float]:
    nx = len(fields.x_centers_m)
    ny = len(fields.y_centers_m)
    i = min(nx - 1, max(0, int((x / scenario.geometry.length_m) * nx)))
    j = min(ny - 1, max(0, int((y / scenario.geometry.width_m) * ny)))
    return fields.velocity_u_m_s[i][j], fields.velocity_v_m_s[i][j]


def _hits_baffle(x: float, y: float, scenario: PlanViewScenarioConfig) -> bool:
    for baffle in scenario.baffles:
        if baffle.x1_m == baffle.x2_m:
            if abs(x - baffle.x1_m) <= 0.6 and min(baffle.y1_m, baffle.y2_m) <= y <= max(baffle.y1_m, baffle.y2_m):
                return True
        else:
            if abs(y - baffle.y1_m) <= 0.6 and min(baffle.x1_m, baffle.x2_m) <= x <= max(baffle.x1_m, baffle.x2_m):
                return True
    return False


def _reset_particle(
    particle: dict[str, object],
    scenario: PlanViewScenarioConfig,
    index: int,
) -> None:
    inlet_min = scenario.inlet.center_m - scenario.inlet.span_m / 2.0
    inlet_max = scenario.inlet.center_m + scenario.inlet.span_m / 2.0
    fraction = ((index * 37) % 180) / 179.0
    y = inlet_min + fraction * (inlet_max - inlet_min)
    x = 0.8 + ((index * 19) % 11) * 0.08
    particle["x"] = x
    particle["y"] = y
    particle["age"] = 0
    particle["trail"] = [(x, y)]


def _plan_speed_color(normalized_speed: float) -> tuple[int, int, int]:
    value = max(0.0, min(1.0, normalized_speed))
    return (
        int(214 - 90 * value),
        int(236 - 60 * value),
        int(247 - 20 * value),
    )
