from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
import csv
import json
import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from .config import ComparisonStudyConfig, load_scenario, load_study
from .run import materialize_run, override_scenario_flow_rate, load_summary


class ComparisonStudyArtifacts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    study_dir: str
    summary_path: str
    csv_path: str
    report_path: str
    run_count: int


def run_comparison_study(study_path: str | Path) -> ComparisonStudyArtifacts:
    study_file = Path(study_path)
    study = load_study(study_file)
    study_root = _study_output_root(study)
    study_root.mkdir(parents=True, exist_ok=True)

    study_dir = study_root / f"{_timestamp()}_{_slugify(study.study_id)}"
    study_dir.mkdir(parents=True, exist_ok=False)
    runs_root = study_dir / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    run_details: list[dict[str, object]] = []
    case_order = [case.label for case in study.cases]
    flow_order = [flow.label for flow in study.flows]

    for flow in study.flows:
        for case in study.cases:
            scenario_path = _resolve_scenario_path(study_file, case.scenario_path)
            scenario = load_scenario(scenario_path)
            scenario = override_scenario_flow_rate(scenario, flow.flow_rate_m3_s)
            run_root_override = runs_root / _slugify(case.label) / _slugify(flow.label)
            artifacts = materialize_run(
                scenario_path=scenario_path,
                scenario=scenario,
                run_root_override=run_root_override,
            )
            summary = load_summary(artifacts.run_dir)
            row = _comparison_row(
                study_id=study.study_id,
                case_label=case.label,
                flow_label=flow.label,
                flow_rate_m3_s=flow.flow_rate_m3_s,
                run_dir=artifacts.run_dir,
                summary=summary,
            )
            rows.append(row)
            run_details.append(
                {
                    "case_label": case.label,
                    "flow_label": flow.label,
                    "scenario_path": str(scenario_path),
                    "run_dir": artifacts.run_dir,
                    "summary_path": artifacts.summary_path,
                    "metrics_path": artifacts.metrics_path,
                    "tracer_path": artifacts.tracer_path,
                }
            )

    summary_path = study_dir / "comparison_summary.json"
    csv_path = study_dir / study.outputs.csv_name
    report_path = study_dir / study.outputs.report_name

    threshold_columns = _threshold_columns(rows)
    _write_comparison_json(
        summary_path,
        study=study,
        study_dir=study_dir,
        rows=rows,
        run_details=run_details,
        case_order=case_order,
        flow_order=flow_order,
    )
    _write_comparison_csv(csv_path, rows, threshold_columns)
    _write_comparison_report(report_path, study, study_dir, rows, threshold_columns, case_order, flow_order)

    return ComparisonStudyArtifacts(
        study_dir=str(study_dir),
        summary_path=str(summary_path),
        csv_path=str(csv_path),
        report_path=str(report_path),
        run_count=len(rows),
    )


def _write_comparison_json(
    summary_path: Path,
    *,
    study: ComparisonStudyConfig,
    study_dir: Path,
    rows: list[dict[str, object]],
    run_details: list[dict[str, object]],
    case_order: list[str],
    flow_order: list[str],
) -> None:
    payload = {
        "study_id": study.study_id,
        "title": study.title,
        "description": study.description,
        "study_dir": str(study_dir),
        "cases": [case.model_dump(mode="json") for case in study.cases],
        "flows": [flow.model_dump(mode="json") for flow in study.flows],
        "outputs": study.outputs.model_dump(mode="json"),
        "case_order": case_order,
        "flow_order": flow_order,
        "rows": rows,
        "runs": run_details,
        "delta_summary": _delta_summary(rows, case_order, flow_order),
    }
    summary_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_comparison_csv(
    csv_path: Path,
    rows: list[dict[str, object]],
    threshold_columns: list[str],
) -> None:
    fieldnames = [
        "study_id",
        "case_label",
        "flow_label",
        "flow_rate_m3_s",
        "run_dir",
        "basin_area_m2",
        "basin_volume_m3",
        "theoretical_detention_time_s",
        "surface_overflow_rate_m_per_d",
        "transition_headloss_m",
        "post_transition_velocity_uniformity_index",
        "jet_redistribution_length_m",
        "plate_inlet_mean_velocity_m_s",
        "plate_inlet_max_velocity_m_s",
        "plate_inlet_upward_velocity_m_s",
        "launder_mean_upward_velocity_m_s",
        "launder_peak_upward_velocity_m_s",
        "dead_zone_fraction",
        "short_circuiting_index",
        "t10_s",
        "t50_s",
        "t90_s",
        "morrill_index",
        "settling_exceedance_fraction_by_threshold",
        *threshold_columns,
    ]
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def _write_comparison_report(
    report_path: Path,
    study: ComparisonStudyConfig,
    study_dir: Path,
    rows: list[dict[str, object]],
    threshold_columns: list[str],
    case_order: list[str],
    flow_order: list[str],
) -> None:
    lines: list[str] = []
    lines.append(f"# {study.title}")
    if study.description:
        lines.append("")
        lines.append(study.description)
    lines.append("")
    lines.append("## Cases")
    for case in study.cases:
        lines.append(f"- `{case.label}`: `{case.scenario_path}`")
    lines.append("")
    lines.append("## Flows")
    for flow in study.flows:
        lines.append(f"- `{flow.label}`: `{flow.flow_rate_m3_s:.3f}` m3/s")
    lines.append("")
    lines.append("## Model Limitations")
    lines.extend(
        [
            "- This is a deterministic screening model, not a calibrated CFD or hydraulic network solver.",
            "- Transition-wall and plate-settler effects are represented through conductance modifiers, not explicit geometry meshing.",
            "- RTD proxy metrics are derived from the steady longitudinal velocity field, not explicit transient transport.",
        ]
    )

    for flow_label in flow_order:
        flow_rows = [row for row in rows if row["flow_label"] == flow_label]
        lines.append("")
        lines.append(f"## Flow: {flow_label}")
        lines.append(_comparison_table(flow_rows, threshold_columns))

    lines.append("")
    lines.append("## Delta Summary")
    lines.append("Deltas are computed as `current_blocked - design_spec`.")
    lines.append("")
    for flow_label in flow_order:
        delta_rows = _delta_rows_for_flow(rows, flow_label, case_order, threshold_columns)
        lines.append(f"### {flow_label}")
        lines.append(_delta_table(delta_rows, threshold_columns))
        lines.append("")

    lines.append("## Interpretation")
    for flow_label in flow_order:
        delta = _delta_rows_for_flow(rows, flow_label, case_order, threshold_columns)
        if not delta:
            continue
        rows_by_metric = {row["metric_key"]: row for row in delta}
        lines.append(f"- `{flow_label}` headloss is {_more_less_phrase(rows_by_metric['transition_headloss_m']['delta'])}.")
        lines.append(
            f"- `{flow_label}` post-transition uniformity is {_better_worse_phrase(rows_by_metric['post_transition_velocity_uniformity_index']['delta'])}."
        )
        lines.append(
            f"- `{flow_label}` RTD proxy breakthrough is {_earlier_later_phrase(rows_by_metric['t10_s']['delta'])} based on t10, with t50 and t90 moving in the same direction."
        )
        lines.append(
            f"- `{flow_label}` launder upwelling risk is {_higher_lower_phrase(rows_by_metric['launder_peak_upward_velocity_m_s']['delta'])}."
        )
        threshold_summary = ", ".join(
            f"{column.replace('settling_exceedance_', '').replace('_m_per_s', '').replace('_', '.')}: {_higher_lower_phrase(rows_by_metric[column]['delta'])}"
            for column in threshold_columns
        )
        lines.append(f"- `{flow_label}` settling-threshold exceedance is {threshold_summary}.")

    report_path.write_text("\n".join(lines), encoding="utf-8")


def _comparison_table(flow_rows: list[dict[str, object]], threshold_columns: list[str]) -> str:
    by_case = {row["case_label"]: row for row in flow_rows}
    design = by_case.get("design_spec")
    current = by_case.get("current_blocked")

    lines = [
        "| Metric | design_spec | current_blocked | delta (current - design) |",
        "| --- | ---: | ---: | ---: |",
    ]
    if design and current:
        for metric in _table_metrics(threshold_columns):
            lines.append(
                f"| {metric['label']} | {metric_value(design, metric['key'])} | {metric_value(current, metric['key'])} | {delta_value(current, design, metric['key'])} |"
            )
        for column in threshold_columns:
            label = column.replace("settling_exceedance_", "").replace("_m_per_s", "").replace("_", ".")
            lines.append(
                f"| Settling exceedance {label} | {metric_value(design, column)} | {metric_value(current, column)} | {delta_value(current, design, column)} |"
            )
    else:
        lines.append("| No comparison pairs were found | - | - | - |")
    return "\n".join(lines)


def _delta_table(delta_rows: list[dict[str, object]], threshold_columns: list[str]) -> str:
    lines = [
        "| Metric | Delta |",
        "| --- | ---: |",
    ]
    if not delta_rows:
        lines.append("| No comparison pairs were found | - |")
        return "\n".join(lines)
    for row in delta_rows:
        lines.append(f"| {row['metric_label']} | {format_number(row['delta'])} |")
    return "\n".join(lines)


def _table_metrics(threshold_columns: list[str]) -> list[dict[str, str]]:
    return [
        {"key": "basin_area_m2", "label": "Basin area"},
        {"key": "basin_volume_m3", "label": "Basin volume"},
        {"key": "theoretical_detention_time_s", "label": "Theoretical detention"},
        {"key": "surface_overflow_rate_m_per_d", "label": "Surface overflow rate"},
        {"key": "transition_headloss_m", "label": "Transition headloss"},
        {"key": "post_transition_velocity_uniformity_index", "label": "Post-transition VUI"},
        {"key": "jet_redistribution_length_m", "label": "Jet redistribution length"},
        {"key": "plate_inlet_mean_velocity_m_s", "label": "Plate inlet mean velocity"},
        {"key": "plate_inlet_max_velocity_m_s", "label": "Plate inlet max velocity"},
        {"key": "plate_inlet_upward_velocity_m_s", "label": "Plate inlet upward velocity"},
        {"key": "launder_mean_upward_velocity_m_s", "label": "Launder mean upward velocity"},
        {"key": "launder_peak_upward_velocity_m_s", "label": "Launder peak upward velocity"},
        {"key": "dead_zone_fraction", "label": "Dead zone fraction"},
        {"key": "short_circuiting_index", "label": "Short-circuiting index"},
        {"key": "t10_s", "label": "t10"},
        {"key": "t50_s", "label": "t50"},
        {"key": "t90_s", "label": "t90"},
        {"key": "morrill_index", "label": "Morrill index"},
    ]


def _delta_rows_for_flow(
    rows: list[dict[str, object]],
    flow_label: str,
    case_order: list[str],
    threshold_columns: list[str],
) -> list[dict[str, object]]:
    flow_rows = [row for row in rows if row["flow_label"] == flow_label]
    by_case = {row["case_label"]: row for row in flow_rows}
    if "design_spec" in by_case and "current_blocked" in by_case:
        baseline = by_case["design_spec"]
        comparison = by_case["current_blocked"]
    elif len(case_order) >= 2 and case_order[0] in by_case and case_order[1] in by_case:
        baseline = by_case[case_order[0]]
        comparison = by_case[case_order[1]]
    else:
        return []

    rows_out: list[dict[str, object]] = []
    for metric in _table_metrics([]):
        metric_key = metric["key"]
        rows_out.append(
            {
                "metric_key": metric_key,
                "metric_label": metric["label"],
                "delta": _difference(comparison.get(metric_key), baseline.get(metric_key)),
            }
        )
    for column in threshold_columns:
        rows_out.append(
            {
                "metric_key": column,
                "metric_label": f"Settling exceedance {column.replace('settling_exceedance_', '').replace('_m_per_s', '').replace('_', '.')}",
                "delta": _difference(comparison.get(column), baseline.get(column)),
            }
        )
    return rows_out


def _delta_summary(
    rows: list[dict[str, object]],
    case_order: list[str],
    flow_order: list[str],
) -> dict[str, dict[str, float]]:
    summary: dict[str, dict[str, float]] = {}
    for flow_label in flow_order:
        delta_rows = _delta_rows_for_flow(rows, flow_label, case_order, _threshold_columns(rows))
        summary[flow_label] = {row["metric_key"]: row["delta"] for row in delta_rows}
    return summary


def _comparison_row(
    *,
    study_id: str,
    case_label: str,
    flow_label: str,
    flow_rate_m3_s: float,
    run_dir: str | Path,
    summary: dict,
) -> dict[str, object]:
    metrics = summary["metrics"]
    row: dict[str, object] = {
        "study_id": study_id,
        "case_label": case_label,
        "flow_label": flow_label,
        "flow_rate_m3_s": flow_rate_m3_s,
        "run_dir": str(run_dir),
        "basin_area_m2": metrics["basin_area_m2"],
        "basin_volume_m3": metrics["basin_volume_m3"],
        "theoretical_detention_time_s": metrics["theoretical_detention_time_s"],
        "surface_overflow_rate_m_per_d": metrics["surface_overflow_rate_m_per_d"],
        "transition_headloss_m": metrics["transition_headloss_m"],
        "post_transition_velocity_uniformity_index": metrics["post_transition_velocity_uniformity_index"],
        "jet_redistribution_length_m": metrics["jet_redistribution_length_m"],
        "plate_inlet_mean_velocity_m_s": metrics["plate_inlet_mean_velocity_m_s"],
        "plate_inlet_max_velocity_m_s": metrics["plate_inlet_max_velocity_m_s"],
        "plate_inlet_upward_velocity_m_s": metrics["plate_inlet_upward_velocity_m_s"],
        "launder_mean_upward_velocity_m_s": metrics["launder_mean_upward_velocity_m_s"],
        "launder_peak_upward_velocity_m_s": metrics["launder_peak_upward_velocity_m_s"],
        "dead_zone_fraction": metrics["dead_zone_fraction"],
        "short_circuiting_index": metrics["short_circuiting_index"],
        "t10_s": metrics["t10_s"],
        "t50_s": metrics["t50_s"],
        "t90_s": metrics["t90_s"],
        "morrill_index": metrics["morrill_index"],
        "settling_exceedance_fraction_by_threshold": json.dumps(
            metrics["settling_exceedance_fraction_by_threshold"],
            sort_keys=True,
        ),
    }

    threshold_map = metrics["settling_exceedance_fraction_by_threshold"]
    for key in sorted(threshold_map, key=lambda value: float(value)):
        row[f"settling_exceedance_{key.replace('.', '_')}_m_per_s"] = threshold_map[key]
    return row


def _threshold_columns(rows: list[dict[str, object]]) -> list[str]:
    keys: list[str] = []
    for row in rows:
        for column in row:
            if column.startswith("settling_exceedance_") and column.endswith("_m_per_s") and column != "settling_exceedance_fraction_by_threshold":
                if column not in keys:
                    keys.append(column)
    keys.sort(key=lambda value: float(value[len("settling_exceedance_") : -len("_m_per_s")].replace("_", ".")))
    return keys


def _resolve_scenario_path(study_file: Path, scenario_path: str) -> Path:
    candidate = Path(scenario_path)
    if candidate.is_absolute():
        return candidate

    relative_to_study = (study_file.parent / candidate).resolve()
    if relative_to_study.exists():
        return relative_to_study

    project_root = _find_project_root(study_file)
    relative_to_project = (project_root / candidate).resolve()
    if relative_to_project.exists():
        return relative_to_project

    return relative_to_study


def _find_project_root(study_file: Path) -> Path:
    for parent in (study_file.resolve(), *study_file.resolve().parents):
        if (parent / "pyproject.toml").exists():
            return parent
    return study_file.parent.resolve()


def _study_output_root(study: ComparisonStudyConfig) -> Path:
    return Path(study.outputs.run_root)


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return cleaned or "study"


def _difference(comparison_value: object, baseline_value: object) -> float:
    try:
        return float(comparison_value) - float(baseline_value)
    except (TypeError, ValueError):
        return 0.0


def _direction_phrase(delta: object) -> str:
    value = float(delta)
    if value > 0.0:
        return f"higher by {format_number(value)}"
    if value < 0.0:
        return f"lower by {format_number(abs(value))}"
    return "unchanged"


def _higher_lower_phrase(delta: object) -> str:
    return _direction_phrase(delta)


def _more_less_phrase(delta: object) -> str:
    value = float(delta)
    if value > 0.0:
        return f"more by {format_number(value)}"
    if value < 0.0:
        return f"less by {format_number(abs(value))}"
    return "unchanged"


def _better_worse_phrase(delta: object) -> str:
    value = float(delta)
    if value > 0.0:
        return f"better by {format_number(value)}"
    if value < 0.0:
        return f"worse by {format_number(abs(value))}"
    return "unchanged"


def _earlier_later_phrase(delta: object) -> str:
    value = float(delta)
    if value > 0.0:
        return f"later by {format_number(value)}"
    if value < 0.0:
        return f"earlier by {format_number(abs(value))}"
    return "unchanged"


def format_number(value: object) -> str:
    if value is None:
        return "n/a"
    numeric = float(value)
    if abs(numeric) >= 1000.0 or (0.0 < abs(numeric) < 1.0e-3):
        return f"{numeric:.3e}"
    return f"{numeric:.4f}"


def metric_value(row: dict[str, object], key: str) -> str:
    return format_number(row.get(key))


def delta_value(current: dict[str, object], baseline: dict[str, object], key: str) -> str:
    return format_number(_difference(current.get(key), baseline.get(key)))
