from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import re

from pydantic import BaseModel, ConfigDict

from .config import (
    LongitudinalScenarioConfig,
    PlanViewScenarioConfig,
    ScenarioConfig,
    dump_scenario_yaml,
    load_scenario,
)
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
    write_operator_report_html,
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
    operator_report_path: str | None = None
    tracer_plot_path: str | None = None


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
        )

    if isinstance(scenario, PlanViewScenarioConfig):
        return _materialize_plan_view_run(
            source_path=source_path,
            scenario=scenario,
            run_dir=run_dir,
            plots_dir=plots_dir,
            scenario_snapshot_path=scenario_snapshot_path,
            timestamp=timestamp,
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
        "operator_report_path": str(operator_report_path),
        "tracer_plot_path": None,
        "solver_status": solver_summary.solver_status,
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
        operator_report_path=str(operator_report_path),
        tracer_plot_path=None,
    )


def _materialize_longitudinal_run(
    *,
    source_path: Path,
    scenario: LongitudinalScenarioConfig,
    run_dir: Path,
    plots_dir: Path,
    scenario_snapshot_path: Path,
    timestamp: str,
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
    )


def materialize_scaffold_run(
    scenario_path: str | Path,
    scenario: ScenarioConfig,
    run_root_override: str | Path | None = None,
    *,
    flow_rate_m3_s: float | None = None,
) -> RunArtifacts:
    return materialize_run(
        scenario_path,
        scenario,
        run_root_override,
        flow_rate_m3_s=flow_rate_m3_s,
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
