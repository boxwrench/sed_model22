from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import re
import shutil
import subprocess

from pydantic import BaseModel, ConfigDict

from .config import (
    LongitudinalScenarioConfig,
    PlanViewScenarioConfig,
    ScenarioConfig,
    dump_scenario_yaml,
    load_scenario,
)
from .media.ffmpeg import resolve_ffmpeg_path, write_slideshow_preview
from .media.pathlines import materialize_plan_view_pathline_preview
from .media.rasterize import rasterize_scene_sequence
from .media.render_animation import (
    materialize_longitudinal_preview_animation,
)
from .media.scenes import write_metrics_card, write_title_card, write_warnings_card
from .mesh import build_longitudinal_mesh, build_structured_mesh
from .metrics import compute_longitudinal_metrics, compute_scenario_metrics
from .solver import (
    HydraulicFieldData,
    LongitudinalFieldData,
    LongitudinalTracerSummary,
    solve_steady_longitudinal_screening_flow,
    solve_steady_screening_flow,
    simulate_longitudinal_tracer,
)
from .viz import (
    write_layout_svg,
    write_longitudinal_layout_svg,
    write_longitudinal_tracer_breakthrough_svg,
    write_longitudinal_velocity_heatmap_svg,
    write_longitudinal_voxel_isometric_svg,
    write_operator_report_html,
    write_plan_view_streamline_svg,
    write_plan_view_voxel_isometric_svg,
    write_velocity_heatmap_svg,
)


class RunArtifacts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_dir: str
    manifest_path: str
    summary_path: str
    mesh_path: str
    metrics_path: str
    fields_path: str | None = None
    tracer_path: str | None = None
    plot_path: str | None = None
    velocity_plot_path: str | None = None
    streamline_plot_path: str | None = None
    operator_report_path: str | None = None
    tracer_plot_path: str | None = None
    voxel_plot_path: str | None = None
    media_manifest_path: str | None = None
    preview_video_path: str | None = None


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return cleaned or "scenario"


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def override_scenario_flow_rate(
    scenario: ScenarioConfig,
    flow_rate_m3_s: float | None,
) -> ScenarioConfig:
    if flow_rate_m3_s is None:
        return scenario
    return scenario.model_copy(
        update={
            "hydraulics": scenario.hydraulics.model_copy(update={"flow_rate_m3_s": flow_rate_m3_s}),
        }
    )


def materialize_run(
    scenario_path: str | Path,
    scenario: ScenarioConfig,
    run_root_override: str | Path | None = None,
    *,
    flow_rate_m3_s: float | None = None,
    media_policy: str = "best_effort_preview",
) -> RunArtifacts:
    source_path = Path(scenario_path).resolve()
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    scenario = override_scenario_flow_rate(scenario, flow_rate_m3_s)
    run_root = Path(run_root_override or scenario.outputs.run_root)
    run_root.mkdir(parents=True, exist_ok=True)

    run_dir = run_root / f"{timestamp}_{_slugify(scenario.metadata.case_id)}"
    run_dir.mkdir(parents=True, exist_ok=False)

    plots_dir = run_dir / "plots"
    plots_dir.mkdir()

    scenario_snapshot_path = run_dir / "scenario_snapshot.yaml"
    scenario_snapshot_path.write_text(dump_scenario_yaml(scenario), encoding="utf-8")

    if isinstance(scenario, LongitudinalScenarioConfig):
        return _materialize_longitudinal_run(
            source_path=source_path,
            scenario=scenario,
            run_dir=run_dir,
            plots_dir=plots_dir,
            scenario_snapshot_path=scenario_snapshot_path,
            timestamp=timestamp,
            media_policy=media_policy,
        )

    if isinstance(scenario, PlanViewScenarioConfig):
        return _materialize_plan_view_run(
            source_path=source_path,
            scenario=scenario,
            run_dir=run_dir,
            plots_dir=plots_dir,
            scenario_snapshot_path=scenario_snapshot_path,
            timestamp=timestamp,
            media_policy=media_policy,
        )

    raise TypeError(f"unsupported scenario type: {type(scenario)!r}")


def _materialize_plan_view_run(
    *,
    source_path: Path,
    scenario: PlanViewScenarioConfig,
    run_dir: Path,
    plots_dir: Path,
    scenario_snapshot_path: Path,
    timestamp: str,
    media_policy: str,
) -> RunArtifacts:
    mesh = build_structured_mesh(scenario)
    metrics = compute_scenario_metrics(scenario)
    solver_summary, fields = solve_steady_screening_flow(scenario, mesh, metrics)

    mesh_path = run_dir / "mesh.json"
    metrics_path = run_dir / "metrics.json"
    summary_path = run_dir / "summary.json"
    manifest_path = run_dir / "manifest.json"
    fields_path = run_dir / "fields.json"

    _write_json(mesh_path, mesh.model_dump(mode="json"))
    _write_json(metrics_path, metrics.model_dump(mode="json"))

    output_fields_path: Path | None = None
    if scenario.outputs.write_fields_json:
        _write_json(fields_path, fields.model_dump(mode="json"))
        output_fields_path = fields_path

    plot_path: Path | None = None
    if scenario.outputs.write_layout_svg:
        plot_path = write_layout_svg(scenario, plots_dir / "basin_layout.svg")

    velocity_plot_path: Path | None = None
    if scenario.outputs.write_velocity_svg:
        velocity_plot_path = write_velocity_heatmap_svg(
            scenario,
            fields,
            plots_dir / "velocity_magnitude.svg",
        )
        streamline_plot_path = write_plan_view_streamline_svg(
            scenario,
            fields,
            plots_dir / "streamlines.svg",
        )
    else:
        streamline_plot_path = None

    operator_report_path = write_operator_report_html(
        scenario,
        summary={
            "metadata": scenario.metadata.model_dump(mode="json"),
            "geometry": scenario.geometry.model_dump(mode="json"),
            "hydraulics": scenario.hydraulics.model_dump(mode="json"),
            "inlet": scenario.inlet.model_dump(mode="json"),
            "outlet": scenario.outlet.model_dump(mode="json"),
            "boundaries": scenario.boundaries.model_dump(mode="json"),
            "bed": scenario.bed.model_dump(mode="json"),
            "numerics": scenario.numerics.model_dump(mode="json"),
            "baffle_count": len(scenario.baffles),
            "baffles": [baffle.model_dump(mode="json") for baffle in scenario.baffles],
            "mesh": mesh.model_dump(mode="json"),
            "metrics": metrics.model_dump(mode="json"),
            "solver": solver_summary.model_dump(mode="json"),
        },
        fields=fields,
        output_path=run_dir / "operator_report.html",
        generated_at_utc=timestamp,
    )

    summary = {
        "model_form": scenario.model_form,
        "metadata": scenario.metadata.model_dump(mode="json"),
        "geometry": scenario.geometry.model_dump(mode="json"),
        "hydraulics": scenario.hydraulics.model_dump(mode="json"),
        "inlet": scenario.inlet.model_dump(mode="json"),
        "outlet": scenario.outlet.model_dump(mode="json"),
        "boundaries": scenario.boundaries.model_dump(mode="json"),
        "bed": scenario.bed.model_dump(mode="json"),
        "numerics": scenario.numerics.model_dump(mode="json"),
        "baffle_count": len(scenario.baffles),
        "baffles": [baffle.model_dump(mode="json") for baffle in scenario.baffles],
        "mesh": mesh.model_dump(mode="json"),
        "metrics": metrics.model_dump(mode="json"),
        "solver": solver_summary.model_dump(mode="json"),
    }
    _write_json(summary_path, summary)
    media_artifacts = _materialize_run_media(
        scenario=scenario,
        fields=fields,
        summary=summary,
        run_dir=run_dir,
        media_policy=media_policy,
        tracer=None,
    )

    manifest = {
        "generated_at_utc": timestamp,
        "scenario_source": str(source_path),
        "scenario_snapshot": str(scenario_snapshot_path),
        "summary_path": str(summary_path),
        "mesh_path": str(mesh_path),
        "metrics_path": str(metrics_path),
        "fields_path": str(output_fields_path) if output_fields_path else None,
        "tracer_path": None,
        "plot_path": str(plot_path) if plot_path else None,
        "velocity_plot_path": str(velocity_plot_path) if velocity_plot_path else None,
        "streamline_plot_path": str(streamline_plot_path) if streamline_plot_path else None,
        "operator_report_path": str(operator_report_path),
        "tracer_plot_path": None,
        "solver_status": solver_summary.solver_status,
        **media_artifacts,
    }
    _write_json(manifest_path, manifest)

    return RunArtifacts(
        run_dir=str(run_dir),
        manifest_path=str(manifest_path),
        summary_path=str(summary_path),
        mesh_path=str(mesh_path),
        metrics_path=str(metrics_path),
        fields_path=str(output_fields_path) if output_fields_path else None,
        tracer_path=None,
        plot_path=str(plot_path) if plot_path else None,
        velocity_plot_path=str(velocity_plot_path) if velocity_plot_path else None,
        streamline_plot_path=str(streamline_plot_path) if streamline_plot_path else None,
        operator_report_path=str(operator_report_path),
        tracer_plot_path=None,
        voxel_plot_path=_optional_string(media_artifacts.get("voxel_plot_path")),
        media_manifest_path=_optional_string(media_artifacts.get("media_manifest_path")),
        preview_video_path=_optional_string(media_artifacts.get("preview_video_path")),
    )


def _materialize_longitudinal_run(
    *,
    source_path: Path,
    scenario: LongitudinalScenarioConfig,
    run_dir: Path,
    plots_dir: Path,
    scenario_snapshot_path: Path,
    timestamp: str,
    media_policy: str,
) -> RunArtifacts:
    mesh = build_longitudinal_mesh(scenario)
    solver_summary, fields = solve_steady_longitudinal_screening_flow(scenario, mesh)
    tracer = simulate_longitudinal_tracer(scenario, mesh, fields)
    metrics = compute_longitudinal_metrics(scenario, mesh, fields, tracer)

    mesh_path = run_dir / "mesh.json"
    metrics_path = run_dir / "metrics.json"
    summary_path = run_dir / "summary.json"
    manifest_path = run_dir / "manifest.json"
    fields_path = run_dir / "fields.json"
    tracer_path = run_dir / "tracer.json"

    _write_json(mesh_path, mesh.model_dump(mode="json"))
    _write_json(metrics_path, metrics.model_dump(mode="json"))
    _write_json(fields_path, fields.model_dump(mode="json"))
    _write_json(tracer_path, tracer.model_dump(mode="json"))

    layout_path = write_longitudinal_layout_svg(scenario, plots_dir / "basin_layout.svg")
    velocity_path = write_longitudinal_velocity_heatmap_svg(
        scenario,
        fields,
        plots_dir / "velocity_magnitude.svg",
    )
    tracer_plot_path = write_longitudinal_tracer_breakthrough_svg(
        scenario,
        tracer,
        plots_dir / "tracer_breakthrough.svg",
    )

    summary = {
        "model_form": scenario.model_form,
        "metadata": scenario.metadata.model_dump(mode="json"),
        "geometry": scenario.geometry.model_dump(mode="json"),
        "hydraulics": scenario.hydraulics.model_dump(mode="json"),
        "upstream": scenario.upstream.model_dump(mode="json"),
        "features": [feature.model_dump(mode="json") for feature in scenario.features],
        "evaluation_stations": [station.model_dump(mode="json") for station in scenario.evaluation_stations],
        "performance_proxies": scenario.performance_proxies.model_dump(mode="json"),
        "numerics": scenario.numerics.model_dump(mode="json"),
        "outputs": scenario.outputs.model_dump(mode="json"),
        "mesh": mesh.model_dump(mode="json"),
        "metrics": metrics.model_dump(mode="json"),
        "solver": solver_summary.model_dump(mode="json"),
        "tracer": tracer.model_dump(mode="json"),
    }
    _write_json(summary_path, summary)
    media_artifacts = _materialize_run_media(
        scenario=scenario,
        fields=fields,
        summary=summary,
        run_dir=run_dir,
        media_policy=media_policy,
        tracer=tracer,
    )

    manifest = {
        "generated_at_utc": timestamp,
        "scenario_source": str(source_path),
        "scenario_snapshot": str(scenario_snapshot_path),
        "summary_path": str(summary_path),
        "mesh_path": str(mesh_path),
        "metrics_path": str(metrics_path),
        "fields_path": str(fields_path),
        "tracer_path": str(tracer_path),
        "plot_path": str(layout_path),
        "velocity_plot_path": str(velocity_path),
        "operator_report_path": None,
        "tracer_plot_path": str(tracer_plot_path),
        "solver_status": solver_summary.solver_status,
        **media_artifacts,
    }
    _write_json(manifest_path, manifest)

    return RunArtifacts(
        run_dir=str(run_dir),
        manifest_path=str(manifest_path),
        summary_path=str(summary_path),
        mesh_path=str(mesh_path),
        metrics_path=str(metrics_path),
        fields_path=str(fields_path),
        tracer_path=str(tracer_path),
        plot_path=str(layout_path),
        velocity_plot_path=str(velocity_path),
        operator_report_path=None,
        tracer_plot_path=str(tracer_plot_path),
        voxel_plot_path=_optional_string(media_artifacts.get("voxel_plot_path")),
        media_manifest_path=_optional_string(media_artifacts.get("media_manifest_path")),
        preview_video_path=_optional_string(media_artifacts.get("preview_video_path")),
    )


def materialize_scaffold_run(
    scenario_path: str | Path,
    scenario: ScenarioConfig,
    run_root_override: str | Path | None = None,
    *,
    flow_rate_m3_s: float | None = None,
    media_policy: str = "best_effort_preview",
) -> RunArtifacts:
    return materialize_run(
        scenario_path,
        scenario,
        run_root_override,
        flow_rate_m3_s=flow_rate_m3_s,
        media_policy=media_policy,
    )


def load_summary(run_dir: str | Path) -> dict:
    summary_path = Path(run_dir) / "summary.json"
    with summary_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_fields(run_dir: str | Path) -> HydraulicFieldData | LongitudinalFieldData:
    fields_path = Path(run_dir) / "fields.json"
    with fields_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if "z_centers_m" in payload:
        return LongitudinalFieldData.model_validate(payload)
    return HydraulicFieldData.model_validate(payload)


def load_tracer(run_dir: str | Path) -> LongitudinalTracerSummary:
    tracer_path = Path(run_dir) / "tracer.json"
    with tracer_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return LongitudinalTracerSummary.model_validate(payload)


def load_scenario_snapshot(run_dir: str | Path) -> ScenarioConfig:
    return load_scenario(Path(run_dir) / "scenario_snapshot.yaml")


def _materialize_run_media(
    *,
    scenario: ScenarioConfig,
    fields: HydraulicFieldData | LongitudinalFieldData,
    summary: dict,
    run_dir: Path,
    media_policy: str,
    tracer: LongitudinalTracerSummary | None,
) -> dict[str, object]:
    if media_policy == "off":
        return {"media_policy": media_policy, "media_status": "disabled"}

    media_dir = run_dir / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    voxel_path = media_dir / "voxel_isometric.svg"
    if isinstance(scenario, LongitudinalScenarioConfig):
        write_longitudinal_voxel_isometric_svg(scenario, fields, voxel_path)
    else:
        write_plan_view_voxel_isometric_svg(scenario, fields, voxel_path)

    media_manifest_path = media_dir / "manifest.json"
    manifest: dict[str, object] = {
        "media_policy": media_policy,
        "voxel_plot_path": str(voxel_path),
        "preview_video_path": None,
        "media_status": "still_only",
        "preview_profile": "low_fidelity" if media_policy == "low_fidelity_preview" else "standard",
    }

    if media_policy == "still_only":
        _write_json(media_manifest_path, manifest)
        manifest["media_manifest_path"] = str(media_manifest_path)
        return manifest

    try:
        preview_video_path = _materialize_run_preview(
            scenario=scenario,
            fields=fields,
            summary=summary,
            voxel_path=voxel_path,
            media_dir=media_dir,
            tracer=tracer,
            low_fidelity=(media_policy == "low_fidelity_preview"),
        )
        manifest["preview_video_path"] = str(preview_video_path) if preview_video_path else None
        manifest["media_status"] = "preview_rendered" if preview_video_path else "preview_skipped"
    except (RuntimeError, FileNotFoundError, OSError, subprocess.CalledProcessError) as exc:
        if media_policy == "require_preview":
            raise
        manifest["media_status"] = "preview_skipped"
        manifest["preview_skip_reason"] = str(exc)
        manifest["preview_skip_exception_type"] = type(exc).__name__

    _write_json(media_manifest_path, manifest)
    manifest["media_manifest_path"] = str(media_manifest_path)
    return manifest


def _materialize_run_preview(
    *,
    scenario: ScenarioConfig,
    fields: HydraulicFieldData | LongitudinalFieldData,
    summary: dict,
    voxel_path: Path,
    media_dir: Path,
    tracer: LongitudinalTracerSummary | None,
    low_fidelity: bool = False,
) -> Path | None:
    if (
        isinstance(scenario, LongitudinalScenarioConfig)
        and isinstance(fields, LongitudinalFieldData)
        and tracer is not None
    ):
        artifacts = materialize_longitudinal_preview_animation(
            scenario=scenario,
            fields=fields,
            tracer=tracer,
            summary=summary,
            media_dir=media_dir,
            width=640 if low_fidelity else 854,
            height=360 if low_fidelity else 480,
            fps=8 if low_fidelity else 10,
            max_wall_time_s=45.0 if low_fidelity else 180.0,
        )
        return Path(artifacts.preview_video_path)

    if isinstance(scenario, PlanViewScenarioConfig) and isinstance(fields, HydraulicFieldData):
        artifacts = materialize_plan_view_pathline_preview(
            scenario=scenario,
            fields=fields,
            media_dir=media_dir,
            width=640 if low_fidelity else 854,
            height=360 if low_fidelity else 480,
            fps=12 if low_fidelity else 24,
            frame_count=60 if low_fidelity else 144,
            particle_count=72 if low_fidelity else 220,
            trail_length=10 if low_fidelity else 16,
        )
        manifest = json.loads(Path(artifacts.manifest_path).read_text(encoding="utf-8"))
        poster_path = manifest.get("poster_path")
        if isinstance(poster_path, str):
            shutil.copyfile(poster_path, media_dir / "poster.ppm")
        return Path(artifacts.preview_video_path) if artifacts.preview_video_path else None

    title_card_path = write_title_card(
        media_dir / "title_card.svg",
        title=scenario.metadata.title,
        subtitle="Best-effort run preview generated from the solved basin fields",
        template_id="run_preview_v1",
    )
    metrics_card_path = write_metrics_card(
        media_dir / "metrics_card.svg",
        title=scenario.metadata.title,
        lines=_run_metric_lines(summary),
    )
    warnings_card_path = write_warnings_card(
        media_dir / "warnings_card.svg",
        title=scenario.metadata.title,
        lines=_run_warning_lines(summary),
    )

    poster_path = media_dir / "poster.svg"
    shutil.copyfile(voxel_path, poster_path)

    scene_sequence = [
        {"path": str(title_card_path), "duration_s": 1.8},
        {"path": str(voxel_path), "duration_s": 2.6},
        {"path": str(metrics_card_path), "duration_s": 2.4},
        {"path": str(warnings_card_path), "duration_s": 2.4},
        {"path": str(poster_path), "duration_s": 1.4},
    ]
    _write_json(media_dir / "scene_sequence.json", {"scenes": scene_sequence})

    rasterized_scenes = rasterize_scene_sequence(scene_sequence, media_dir / "frames")
    if len(rasterized_scenes) != len(scene_sequence):
        raise RuntimeError("preview rasterization is unavailable; install CairoSVG to enable mp4 preview output")

    ffmpeg_path = resolve_ffmpeg_path()
    if not ffmpeg_path:
        raise RuntimeError("ffmpeg was not found; set SED_MODEL22_FFMPEG, add ffmpeg to PATH, or place it at tools/ffmpeg/bin/ffmpeg.exe")

    return write_slideshow_preview(
        ffmpeg_path=ffmpeg_path,
        fps=8 if low_fidelity else 12,
        scenes=[(str(path), duration_s) for path, duration_s in rasterized_scenes],
        output_path=media_dir / "preview.mp4",
    )


def _run_metric_lines(summary: dict) -> list[str]:
    metrics = summary["metrics"]
    solver = summary["solver"]
    model_form = summary.get("model_form")
    if model_form == "longitudinal_v0_2":
        tracer = summary.get("tracer", {})
        return [
            f"Transition headloss: {metrics['transition_headloss_m']:.4f} m",
            f"Post-transition uniformity index: {metrics['post_transition_velocity_uniformity_index']:.4f}",
            f"RTD proxy: t10 {tracer.get('t10_s', metrics['t10_s']):.0f} s | t50 {tracer.get('t50_s', metrics['t50_s']):.0f} s | t90 {tracer.get('t90_s', metrics['t90_s']):.0f} s",
            f"Launder peak upward-velocity proxy: {metrics['launder_peak_upward_velocity_m_s']:.5f} m/s",
            f"Solver mass-balance diagnostic: {solver['mass_balance_error']:.3e}",
        ]
    return [
        f"Detention time: {metrics['detention_time_h']:.2f} h",
        f"Surface overflow rate: {metrics['surface_overflow_rate_m_per_d']:.2f} m/day",
        f"Max velocity: {solver['max_velocity_m_s']:.4f} m/s",
        f"Mass-balance diagnostic: {solver['mass_balance_error']:.3e}",
    ]


def _run_warning_lines(summary: dict) -> list[str]:
    lines = []
    model_form = summary.get("model_form")
    if model_form == "longitudinal_v0_2":
        lines.append("This is a 2.5D display of a 2D longitudinal screening field, not a full 3D solve.")
        lines.append("RTD values in this preview are deterministic proxy timings derived from the steady field.")
    else:
        lines.append("This is a 2.5D display of a 2D plan-view screening field, not a full 3D solve.")
    lines.append("Voxel colors show run-normalized relative speed bands, not literal 3D cell velocities.")
    solver = summary["solver"]
    if abs(solver.get("mass_balance_error", 0.0)) > 1.0:
        lines.append("Large discharge mismatch means absolute velocity-derived values should be read as proxy-only screening outputs.")
    return lines


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) else None
