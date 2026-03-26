from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import re

from pydantic import BaseModel

from .config import ScenarioConfig, dump_scenario_yaml, load_scenario
from .mesh import build_structured_mesh
from .metrics import compute_scenario_metrics
from .solver import HydraulicFieldData, solve_steady_screening_flow
from .viz import write_layout_svg, write_operator_report_html, write_velocity_heatmap_svg


class RunArtifacts(BaseModel):
    run_dir: str
    manifest_path: str
    summary_path: str
    mesh_path: str
    metrics_path: str
    fields_path: str | None = None
    plot_path: str | None = None
    velocity_plot_path: str | None = None
    operator_report_path: str | None = None


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return cleaned or "scenario"


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def materialize_run(
    scenario_path: str | Path,
    scenario: ScenarioConfig,
    run_root_override: str | Path | None = None,
) -> RunArtifacts:
    source_path = Path(scenario_path).resolve()
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_root = Path(run_root_override or scenario.outputs.run_root)
    run_root.mkdir(parents=True, exist_ok=True)

    run_dir = run_root / f"{timestamp}_{_slugify(scenario.metadata.case_id)}"
    run_dir.mkdir(parents=True, exist_ok=False)

    plots_dir = run_dir / "plots"
    plots_dir.mkdir()

    scenario_snapshot_path = run_dir / "scenario_snapshot.yaml"
    scenario_snapshot_path.write_text(dump_scenario_yaml(scenario), encoding="utf-8")

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
        "plot_path": str(plot_path) if plot_path else None,
        "velocity_plot_path": str(velocity_plot_path) if velocity_plot_path else None,
        "operator_report_path": str(operator_report_path),
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
        plot_path=str(plot_path) if plot_path else None,
        velocity_plot_path=str(velocity_plot_path) if velocity_plot_path else None,
        operator_report_path=str(operator_report_path),
    )


def materialize_scaffold_run(
    scenario_path: str | Path,
    scenario: ScenarioConfig,
    run_root_override: str | Path | None = None,
) -> RunArtifacts:
    return materialize_run(scenario_path, scenario, run_root_override)


def load_summary(run_dir: str | Path) -> dict:
    summary_path = Path(run_dir) / "summary.json"
    with summary_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_fields(run_dir: str | Path) -> HydraulicFieldData:
    fields_path = Path(run_dir) / "fields.json"
    with fields_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return HydraulicFieldData.model_validate(payload)


def load_scenario_snapshot(run_dir: str | Path) -> ScenarioConfig:
    return load_scenario(Path(run_dir) / "scenario_snapshot.yaml")
