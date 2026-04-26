from __future__ import annotations

from datetime import UTC, datetime
import csv
import json
import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from .config import ComparisonStudyConfig, load_scenario, load_study
from .media.manifest import write_manifest
from .media.render_preview import materialize_preview_from_stills
from .media.render_still import MediaCaseTemplate, MediaTemplate, PreparedMediaCase, render_prepared_media_cases
from .run import load_fields, load_scenario_snapshot, load_summary, materialize_run, override_scenario_flow_rate


class ComparisonStudyArtifacts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    study_dir: str
    summary_path: str
    csv_path: str
    report_path: str
    media_root: str | None = None
    media_manifest_path: str | None = None
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
                media_policy="off",
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
    media_root, media_manifest_path = _materialize_study_media(
        study=study,
        study_dir=study_dir,
        rows=rows,
        run_details=run_details,
        case_order=case_order,
    )

    return ComparisonStudyArtifacts(
        study_dir=str(study_dir),
        summary_path=str(summary_path),
        csv_path=str(csv_path),
        report_path=str(report_path),
        media_root=str(media_root) if media_root else None,
        media_manifest_path=str(media_manifest_path) if media_manifest_path else None,
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
        "run_quality_tier",
        "quality_reasons",
        "solver_converged",
        "solver_mass_balance_error",
        "solver_max_velocity_m_s",
        "solver_max_upward_velocity_m_s",
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
    baseline_label, comparison_label = _comparison_labels(case_order)
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
            "- When the solver discharge mismatch diagnostic is large, absolute velocity values should be read as directional screening proxies, not literal field-credible m/s predictions.",
        ]
    )

    for flow_label in flow_order:
        flow_rows = [row for row in rows if row["flow_label"] == flow_label]
        lines.append("")
        lines.append(f"## Flow: {flow_label}")
        lines.append("")
        lines.append("Quality status:")
        lines.extend(_flow_quality_lines(flow_rows, case_order))
        lines.append("")
        lines.append(_comparison_table(flow_rows, threshold_columns, case_order))
        caution_lines = _flow_cautions(flow_rows, case_order, threshold_columns)
        if caution_lines:
            lines.append("")
            lines.append("Screening cautions:")
            lines.extend(caution_lines)

    lines.append("")
    lines.append("## Delta Summary")
    lines.append(f"Deltas are computed as `{comparison_label} - {baseline_label}`.")
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
        lines.append(
            f"- `{flow_label}` transition headloss in `{comparison_label}` is {_more_less_phrase(rows_by_metric['transition_headloss_m']['delta'])} relative to `{baseline_label}`."
        )
        lines.append(
            f"- `{flow_label}` post-transition uniformity in `{comparison_label}` is {_better_worse_phrase(rows_by_metric['post_transition_velocity_uniformity_index']['delta'])} relative to `{baseline_label}`."
        )
        lines.append(
            f"- `{flow_label}` RTD proxy timing shifts are: t10 {_earlier_later_phrase(rows_by_metric['t10_s']['delta'])}, t50 {_earlier_later_phrase(rows_by_metric['t50_s']['delta'])}, and t90 {_earlier_later_phrase(rows_by_metric['t90_s']['delta'])}."
        )
        lines.append(
            f"- `{flow_label}` launder upwelling proxy in `{comparison_label}` is {_higher_lower_phrase(rows_by_metric['launder_peak_upward_velocity_m_s']['delta'])} relative to `{baseline_label}`."
        )
        threshold_summary = ", ".join(
            f"{column.replace('settling_exceedance_', '').replace('_m_per_s', '').replace('_', '.')}: {_higher_lower_phrase(rows_by_metric[column]['delta'])}"
            for column in threshold_columns
        )
        lines.append(
            f"- `{flow_label}` settling-threshold exceedance in `{comparison_label}` is {threshold_summary} relative to `{baseline_label}`."
        )

    report_path.write_text("\n".join(lines), encoding="utf-8")


def _materialize_study_media(
    *,
    study: ComparisonStudyConfig,
    study_dir: Path,
    rows: list[dict[str, object]],
    run_details: list[dict[str, object]],
    case_order: list[str],
) -> tuple[Path | None, Path | None]:
    media_root = study_dir / "media"
    media_root.mkdir(parents=True, exist_ok=True)
    packages: list[dict[str, object]] = []

    for flow in study.flows:
        prepared_cases: list[PreparedMediaCase] = []
        for case_label in case_order:
            detail = next(
                (
                    item
                    for item in run_details
                    if item["flow_label"] == flow.label and item["case_label"] == case_label
                ),
                None,
            )
            if detail is None:
                continue
            run_dir = Path(str(detail["run_dir"]))
            prepared_cases.append(
                PreparedMediaCase(
                    label=case_label,
                    scenario_path=str(detail["scenario_path"]),
                    scenario_snapshot=load_scenario_snapshot(run_dir),
                    fields=load_fields(run_dir),
                    summary=load_summary(run_dir),
                )
            )

        if not prepared_cases:
            continue

        template = _study_flow_media_template(study, flow.label, flow.flow_rate_m3_s, prepared_cases)
        output_root = media_root / _slugify(flow.label)
        still_artifacts = render_prepared_media_cases(
            template=template,
            prepared_cases=prepared_cases,
            output_root=output_root,
        )
        preview_artifacts = materialize_preview_from_stills(
            still_artifacts=still_artifacts,
            template_id=template.template_id,
            title=template.title,
            subtitle=template.subtitle or "Study comparison preview",
            fps=10,
        )
        packages.append(
            {
                "flow_label": flow.label,
                "flow_rate_m3_s": flow.flow_rate_m3_s,
                "output_root": still_artifacts.output_root,
                "comparison_html_path": still_artifacts.comparison_html_path,
                "scene_manifest_path": still_artifacts.scene_manifest_path,
                "preview_root": preview_artifacts.preview_root,
                "preview_manifest_path": preview_artifacts.manifest_path,
                "preview_video_path": preview_artifacts.preview_video_path,
            }
        )

    media_manifest_path = media_root / "manifest.json"
    write_manifest(
        media_manifest_path,
        {
            "study_id": study.study_id,
            "title": study.title,
            "flow_media": packages,
        },
    )
    return media_root, media_manifest_path


def _study_flow_media_template(
    study: ComparisonStudyConfig,
    flow_label: str,
    flow_rate_m3_s: float,
    prepared_cases: list[PreparedMediaCase],
) -> MediaTemplate:
    title = f"{study.title} ({flow_label})"
    subtitle = f"{flow_label.title()} flow comparison at {flow_rate_m3_s:.3f} m3/s."
    narrative = study.description or (
        "Use the same voxel view for both cases so leadership can see directional hydraulic changes"
        " before committing to higher-fidelity study or capital work."
    )
    focus_points = [
        "transition-wall impact",
        "redistribution quality",
        "launder approach risk",
        "screening-only confidence",
    ]
    return MediaTemplate(
        template_id=f"{study.study_id}_{_slugify(flow_label)}",
        title=title,
        subtitle=subtitle,
        narrative=narrative,
        focus_points=focus_points,
        output_slug=f"{study.study_id}_{_slugify(flow_label)}",
        cases=[
            MediaCaseTemplate(
                label=case.label,
                scenario_path=case.scenario_path,
            )
            for case in prepared_cases
        ],
    )


def _comparison_table(
    flow_rows: list[dict[str, object]],
    threshold_columns: list[str],
    case_order: list[str],
) -> str:
    pair = _comparison_pair(flow_rows, case_order)

    lines = [
        f"| Metric | {case_order[0]} | {case_order[1]} | delta ({case_order[1]} - {case_order[0]}) |",
        "| --- | ---: | ---: | ---: |",
    ]
    if pair is not None:
        _, _, baseline, comparison = pair
        for metric in _table_metrics(threshold_columns):
            lines.append(
                f"| {metric['label']} | {metric_value(baseline, metric['key'])} | {metric_value(comparison, metric['key'])} | {delta_value(comparison, baseline, metric['key'])} |"
            )
        for column in threshold_columns:
            label = column.replace("settling_exceedance_", "").replace("_m_per_s", "").replace("_", ".")
            lines.append(
                f"| Settling exceedance {label} | {metric_value(baseline, column)} | {metric_value(comparison, column)} | {delta_value(comparison, baseline, column)} |"
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
    pair = _comparison_pair(flow_rows, case_order)
    if pair is None:
        return []
    _, _, baseline, comparison = pair

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
    solver = summary["solver"]
    row: dict[str, object] = {
        "study_id": study_id,
        "case_label": case_label,
        "flow_label": flow_label,
        "flow_rate_m3_s": flow_rate_m3_s,
        "run_dir": str(run_dir),
        "run_quality_tier": summary.get("run_quality_tier", "unknown"),
        "quality_reasons": json.dumps(summary.get("quality_reasons", [])),
        "solver_converged": solver["converged"],
        "solver_mass_balance_error": solver["mass_balance_error"],
        "solver_max_velocity_m_s": solver["max_velocity_m_s"],
        "solver_max_upward_velocity_m_s": solver["max_upward_velocity_m_s"],
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


def _flow_quality_lines(
    flow_rows: list[dict[str, object]],
    case_order: list[str],
) -> list[str]:
    by_case = {row["case_label"]: row for row in flow_rows}
    lines: list[str] = []
    for case_label in case_order:
        row = by_case.get(case_label)
        if row is None:
            continue
        tier = str(row.get("run_quality_tier", "unknown"))
        reasons = _parse_quality_reasons(row.get("quality_reasons"))
        if reasons:
            lines.append(f"- `{case_label}`: `{tier}` - {'; '.join(reasons)}")
        else:
            lines.append(f"- `{case_label}`: `{tier}`")
    return lines


def _threshold_columns(rows: list[dict[str, object]]) -> list[str]:
    keys: list[str] = []
    for row in rows:
        for column in row:
            if column.startswith("settling_exceedance_") and column.endswith("_m_per_s") and column != "settling_exceedance_fraction_by_threshold":
                if column not in keys:
                    keys.append(column)
    keys.sort(key=lambda value: float(value[len("settling_exceedance_") : -len("_m_per_s")].replace("_", ".")))
    return keys


def _parse_quality_reasons(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return [value] if value else []
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    return []


def _comparison_labels(case_order: list[str]) -> tuple[str, str]:
    if len(case_order) < 2:
        raise ValueError("comparison studies require at least two cases")
    return case_order[0], case_order[1]


def _comparison_pair(
    flow_rows: list[dict[str, object]],
    case_order: list[str],
) -> tuple[str, str, dict[str, object], dict[str, object]] | None:
    baseline_label, comparison_label = _comparison_labels(case_order)
    by_case = {row["case_label"]: row for row in flow_rows}
    if baseline_label not in by_case or comparison_label not in by_case:
        return None
    return baseline_label, comparison_label, by_case[baseline_label], by_case[comparison_label]


def _flow_cautions(
    flow_rows: list[dict[str, object]],
    case_order: list[str],
    threshold_columns: list[str],
) -> list[str]:
    pair = _comparison_pair(flow_rows, case_order)
    if pair is None:
        return []

    baseline_label, comparison_label, baseline, comparison = pair
    cautions: list[str] = []

    for label, row in ((baseline_label, baseline), (comparison_label, comparison)):
        mass_balance_error = float(row.get("solver_mass_balance_error", 0.0))
        if mass_balance_error > 0.25:
            cautions.append(
                f"- `{label}` solver discharge mismatch diagnostic is {format_number(mass_balance_error)}; absolute velocity-derived m/s values are not field-credible for this run and should be read directionally only."
            )

    if threshold_columns and _thresholds_are_saturated(baseline, comparison, threshold_columns):
        cautions.append(
            "- Settling-threshold exceedance is saturated across both cases for this flow, so it is not distinguishing the scenarios in the current threshold set."
        )

    peak_ratio = _safe_ratio(
        float(comparison.get("launder_peak_upward_velocity_m_s", 0.0)),
        float(baseline.get("launder_peak_upward_velocity_m_s", 0.0)),
    )
    if peak_ratio >= 10.0:
        cautions.append(
            f"- `{comparison_label}` is driving an extreme increase in the launder upwelling proxy relative to `{baseline_label}`. In the current model form this may reflect both a real directional warning and any missing explicit bypass-path representation."
        )

    return cautions


def _thresholds_are_saturated(
    baseline: dict[str, object],
    comparison: dict[str, object],
    threshold_columns: list[str],
) -> bool:
    for column in threshold_columns:
        baseline_value = float(baseline.get(column, 0.0))
        comparison_value = float(comparison.get(column, 0.0))
        if baseline_value not in (0.0, 1.0):
            return False
        if comparison_value not in (0.0, 1.0):
            return False
        if baseline_value != comparison_value:
            return False
    return bool(threshold_columns)


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0.0:
        return float("inf") if numerator > 0.0 else 1.0
    return numerator / denominator


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
