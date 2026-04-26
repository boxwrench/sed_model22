from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from ..config import LongitudinalScenarioConfig, PlanViewScenarioConfig, ScenarioConfig, load_scenario
from ..run import load_fields, load_scenario_snapshot, load_summary, materialize_run, override_scenario_flow_rate
from ..solver import HydraulicFieldData, LongitudinalFieldData
from ..viz import write_longitudinal_voxel_isometric_svg, write_plan_view_voxel_isometric_svg
from .layouts import build_comparison_html
from .manifest import (
    RenderedCaseArtifact,
    StillRenderArtifacts,
    VisualScene,
    VisualSceneCase,
    write_manifest,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return cleaned or "media"


class MediaCaseTemplate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1)
    scenario_path: str = Field(min_length=1)
    flow_rate_m3_s: float | None = Field(default=None, gt=0)
    numerics_override: dict[str, int | float | str | bool] = Field(default_factory=dict)


class MediaTemplate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    template_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    subtitle: str = ""
    narrative: str = ""
    focus_points: list[str] = Field(default_factory=list)
    output_slug: str | None = None
    output_type: Literal["single_case_voxel_still", "comparison_voxel_stills"] = "comparison_voxel_stills"
    cases: list[MediaCaseTemplate] = Field(min_length=1)


@dataclass(frozen=True)
class PreparedMediaCase:
    label: str
    scenario_path: str
    scenario_snapshot: ScenarioConfig
    fields: HydraulicFieldData | LongitudinalFieldData
    summary: dict[str, object]


def load_media_template(path: str | Path) -> MediaTemplate:
    template_path = Path(path)
    with template_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError("media template root must be a mapping")
    return MediaTemplate.model_validate(payload)


def render_media_template(
    template_or_path: MediaTemplate | str | Path,
    *,
    output_root: str | Path | None = None,
) -> StillRenderArtifacts:
    template_path: Path | None = None
    if isinstance(template_or_path, MediaTemplate):
        template = template_or_path
    else:
        template_path = Path(template_or_path).resolve()
        template = load_media_template(template_path)

    root = Path(output_root) if output_root else (
        _repo_root() / "visualizations" / "_generated" / _slugify(template.output_slug or template.template_id)
    )
    root.mkdir(parents=True, exist_ok=True)
    run_root = root / "_runs"
    run_root.mkdir(parents=True, exist_ok=True)
    prepared_cases: list[PreparedMediaCase] = []

    for case in template.cases:
        scenario_path = _resolve_template_path(case.scenario_path, template_path)
        scenario = _load_media_scenario(case, scenario_path)
        artifacts = materialize_run(
            scenario_path=scenario_path,
            scenario=scenario,
            run_root_override=run_root / _slugify(case.label),
        )
        prepared_cases.append(
            PreparedMediaCase(
                label=case.label,
                scenario_path=str(scenario_path),
                scenario_snapshot=load_scenario_snapshot(artifacts.run_dir),
                fields=load_fields(artifacts.run_dir),
                summary=load_summary(artifacts.run_dir),
            )
        )

    return render_prepared_media_cases(
        template=template,
        prepared_cases=prepared_cases,
        output_root=root,
    )


def render_prepared_media_cases(
    *,
    template: MediaTemplate,
    prepared_cases: list[PreparedMediaCase],
    output_root: str | Path | None = None,
) -> StillRenderArtifacts:
    root = Path(output_root) if output_root else (
        _repo_root() / "visualizations" / "_generated" / _slugify(template.output_slug or template.template_id)
    )
    root.mkdir(parents=True, exist_ok=True)

    rendered_cases: list[RenderedCaseArtifact] = []
    case_summaries: list[dict[str, object]] = []

    # Compute a shared color ceiling for comparison renders so that visual speed
    # differences between cases are real, not artifacts of independent normalization.
    # Per-run renders (single case) still auto-scale.
    shared_vmax: float | None = None
    if len(prepared_cases) >= 2:
        all_speeds = [
            speed
            for case in prepared_cases
            for row in case.fields.speed_m_s
            for speed in row
        ]
        candidate = max(all_speeds, default=0.0)
        if candidate > 0.0:
            shared_vmax = candidate

    for index, case in enumerate(prepared_cases, start=1):
        still_path = root / f"{index:02d}_{_slugify(case.label)}_voxel_isometric.svg"
        model_form = _write_case_still(case.scenario_snapshot, case.fields, still_path, shared_vmax=shared_vmax)
        case_summaries.append(case.summary)
        rendered_cases.append(
            RenderedCaseArtifact(
                label=case.label,
                scenario_path=case.scenario_path,
                model_form=model_form,
                still_path=str(still_path),
                highlighted_metrics=_highlighted_metrics(case.summary),
                warnings=_summary_warnings(case.summary),
            )
        )
    comparison_lines = _comparison_lines(rendered_cases, case_summaries)
    executive_summary = _executive_summary_lines(template, case_summaries)
    warning_lines = _dedupe_lines([warning for case in rendered_cases for warning in case.warnings])
    visual_scene = _build_visual_scene(
        template=template,
        rendered_cases=rendered_cases,
        comparison_lines=comparison_lines,
        executive_summary=executive_summary,
        warning_lines=warning_lines,
    )
    scene_manifest_path = root / "visual_scene.json"
    write_manifest(scene_manifest_path, visual_scene)

    comparison_html_path: Path | None = None
    if len(rendered_cases) >= 2:
        comparison_html_path = root / f"{_slugify(template.output_slug or template.template_id)}.html"
        comparison_html_path.write_text(
            build_comparison_html(scene=visual_scene),
            encoding="utf-8",
        )

    manifest_path = root / "manifest.json"
    artifacts = StillRenderArtifacts(
        template_id=template.template_id,
        title=template.title,
        output_root=str(root),
        comparison_html_path=str(comparison_html_path) if comparison_html_path else None,
        manifest_path=str(manifest_path),
        scene_manifest_path=str(scene_manifest_path),
        cases=rendered_cases,
        comparison_lines=comparison_lines,
        warning_lines=warning_lines,
    )
    write_manifest(manifest_path, artifacts)
    return artifacts


def _write_case_still(
    scenario_snapshot: ScenarioConfig,
    fields: HydraulicFieldData | LongitudinalFieldData,
    still_path: Path,
    *,
    shared_vmax: float | None = None,
) -> str:
    if isinstance(scenario_snapshot, LongitudinalScenarioConfig):
        write_longitudinal_voxel_isometric_svg(scenario_snapshot, fields, still_path, shared_vmax=shared_vmax)
        return "v0.2 longitudinal 2.5D voxel view"
    if isinstance(scenario_snapshot, PlanViewScenarioConfig):
        write_plan_view_voxel_isometric_svg(scenario_snapshot, fields, still_path, shared_vmax=shared_vmax)
        return "v0.1 plan-view 2.5D voxel view"
    raise TypeError(f"unsupported scenario snapshot type: {type(scenario_snapshot)!r}")


def _resolve_template_path(raw_path: str, template_path: Path | None) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate.resolve()
    if template_path is not None:
        return (template_path.parent / candidate).resolve()
    return (_repo_root() / candidate).resolve()


def _load_media_scenario(case: MediaCaseTemplate, scenario_path: Path) -> ScenarioConfig:
    scenario = load_scenario(scenario_path)
    if case.numerics_override:
        scenario = scenario.model_copy(
            update={
                "numerics": scenario.numerics.model_copy(update=case.numerics_override),
            }
        )
    return override_scenario_flow_rate(scenario, case.flow_rate_m3_s)


def _highlighted_metrics(summary: dict[str, object]) -> dict[str, object]:
    metrics = _mapping(summary.get("metrics"))
    hydraulics = _mapping(summary.get("hydraulics"))
    solver = _mapping(summary.get("solver"))
    highlighted: dict[str, object] = {}
    if "run_quality_tier" in summary:
        highlighted["run_quality_tier"] = summary["run_quality_tier"]
    for key in (
        "flow_rate_m3_s",
        "transition_headloss_m",
        "post_transition_velocity_uniformity_index",
        "plate_inlet_mean_velocity_m_s",
        "launder_peak_upward_velocity_m_s",
        "dead_zone_fraction",
        "t10_s",
        "t50_s",
        "t90_s",
        "morrill_index",
    ):
        if key == "flow_rate_m3_s" and key in hydraulics:
            highlighted[key] = hydraulics[key]
        elif key in metrics:
            highlighted[key] = metrics[key]
    if "mass_balance_error" in solver:
        highlighted["solver_mass_balance_error"] = solver["mass_balance_error"]
    return highlighted


def _summary_warnings(summary: dict[str, object]) -> list[str]:
    warnings: list[str] = []
    model_form = str(summary.get("model_form", ""))
    solver = _mapping(summary.get("solver"))
    quality_tier = str(summary.get("run_quality_tier", "unknown"))
    quality_reasons = summary.get("quality_reasons", [])
    if isinstance(quality_reasons, list) and quality_tier in {"credible", "directional_only", "weak"}:
        if quality_tier == "credible":
            warnings.append("Run quality tier is `credible` under the current screening thresholds.")
        else:
            warnings.append(
                f"Run quality tier is `{quality_tier}`: {'; '.join(str(item) for item in quality_reasons)}."
            )
    if model_form == "plan_view_v0_1":
        warnings.append("This is a 2.5D display of a 2D plan-view screening field, not a full 3D solve.")
    elif model_form == "longitudinal_v0_2":
        warnings.append("This is a 2.5D display of a 2D longitudinal screening field, not a full 3D solve.")

    if solver.get("solver_status") not in (None, "converged"):
        warnings.append(f"Solver status is `{solver.get('solver_status')}`, so treat this media output cautiously.")

    mass_balance_error = solver.get("mass_balance_error")
    if isinstance(mass_balance_error, (int, float)) and abs(mass_balance_error) > 1.0:
        warnings.append(
            "Solver discharge mismatch is large, so absolute velocity-derived values should be read as proxy-only screening outputs."
        )

    metrics = _mapping(summary.get("metrics"))
    settling = metrics.get("settling_exceedance_fraction_by_threshold")
    if isinstance(settling, dict) and settling and all(value in (0.0, 1.0) for value in settling.values()):
        warnings.append("Settling-threshold exceedance is saturated in this run, so it may not distinguish cases cleanly.")
    return warnings


def _comparison_lines(
    rendered_cases: list[RenderedCaseArtifact],
    case_summaries: list[dict[str, object]],
) -> list[str]:
    if len(rendered_cases) < 2 or len(case_summaries) < 2:
        return ["Single-case voxel render for screening review."]

    left_case = rendered_cases[0]
    right_case = rendered_cases[1]
    left_metrics = _mapping(case_summaries[0].get("metrics"))
    right_metrics = _mapping(case_summaries[1].get("metrics"))
    lines = [
        f"{left_case.label} and {right_case.label} use the same voxel view template for repeatable side-by-side review.",
    ]

    metric_labels = {
        "transition_headloss_m": "transition headloss",
        "post_transition_velocity_uniformity_index": "post-transition uniformity index",
        "launder_peak_upward_velocity_m_s": "launder peak upward-velocity proxy",
        "t10_s": "RTD proxy t10",
        "t50_s": "RTD proxy t50",
        "t90_s": "RTD proxy t90",
    }
    for key, label in metric_labels.items():
        left_value = left_metrics.get(key)
        right_value = right_metrics.get(key)
        if isinstance(left_value, (int, float)) and isinstance(right_value, (int, float)):
            delta = right_value - left_value
            lines.append(f"{label}: `{right_case.label} - {left_case.label} = {delta:+.4g}`")
    return lines


def _executive_summary_lines(
    template: MediaTemplate,
    case_summaries: list[dict[str, object]],
) -> list[str]:
    summary_lines = list(template.focus_points)
    if len(case_summaries) < 2:
        return summary_lines or ["Single-case screening visualization for structured review."]

    left_metrics = _mapping(case_summaries[0].get("metrics"))
    right_metrics = _mapping(case_summaries[1].get("metrics"))
    left_label = str(_mapping(case_summaries[0].get("metadata")).get("case_id", "left_case"))
    right_label = str(_mapping(case_summaries[1].get("metadata")).get("case_id", "right_case"))
    left_quality = str(case_summaries[0].get("run_quality_tier", "unknown"))
    right_quality = str(case_summaries[1].get("run_quality_tier", "unknown"))

    if left_quality == right_quality:
        summary_lines.append(f"Both runs are currently labeled `{left_quality}`.")
    else:
        summary_lines.append(f"{left_label} is labeled `{left_quality}` while {right_label} is labeled `{right_quality}`.")

    transition_headloss = _delta_phrase(
        right_metrics.get("transition_headloss_m"),
        left_metrics.get("transition_headloss_m"),
        higher="higher transition-wall headloss",
        lower="lower transition-wall headloss",
    )
    if transition_headloss:
        summary_lines.append(_relationship_sentence(right_label, left_label, transition_headloss))

    uniformity = _delta_phrase(
        right_metrics.get("post_transition_velocity_uniformity_index"),
        left_metrics.get("post_transition_velocity_uniformity_index"),
        higher="better post-transition redistribution uniformity",
        lower="worse post-transition redistribution uniformity",
    )
    if uniformity:
        summary_lines.append(_relationship_sentence(right_label, left_label, uniformity))

    launder = _delta_phrase(
        right_metrics.get("launder_peak_upward_velocity_m_s"),
        left_metrics.get("launder_peak_upward_velocity_m_s"),
        higher="higher launder upwelling proxy",
        lower="lower launder upwelling proxy",
    )
    if launder:
        summary_lines.append(_relationship_sentence(right_label, left_label, launder))

    return _dedupe_lines(summary_lines)


def _build_visual_scene(
    *,
    template: MediaTemplate,
    rendered_cases: list[RenderedCaseArtifact],
    comparison_lines: list[str],
    executive_summary: list[str],
    warning_lines: list[str],
) -> VisualScene:
    scene_type = "comparison_voxel_scene" if len(rendered_cases) >= 2 else "single_case_voxel_scene"
    return VisualScene(
        scene_type=scene_type,
        title=template.title,
        subtitle=template.subtitle or "Template-driven voxel comparison output",
        narrative=template.narrative,
        focus_points=list(template.focus_points),
        executive_summary=executive_summary,
        comparison_lines=comparison_lines,
        warning_lines=warning_lines or ["This output remains a screening visualization, not a fidelity upgrade."],
        cases=[
            VisualSceneCase(
                label=case.label,
                model_form=case.model_form,
                still_filename=Path(case.still_path).name,
                highlighted_metrics=case.highlighted_metrics,
                warnings=case.warnings,
            )
            for case in rendered_cases
        ],
    )


def _delta_phrase(
    value: object,
    baseline: object,
    *,
    higher: str,
    lower: str,
) -> str | None:
    if not isinstance(value, (int, float)) or not isinstance(baseline, (int, float)):
        return None
    if abs(value - baseline) < 1.0e-9:
        return "no material change"
    return higher if value > baseline else lower


def _relationship_sentence(label: str, baseline_label: str, phrase: str) -> str:
    if phrase == "no material change":
        return f"{label} shows no material change relative to {baseline_label}."
    return f"{label} shows {phrase} than {baseline_label}."


def _mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _dedupe_lines(lines: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for line in lines:
        if line not in seen:
            ordered.append(line)
            seen.add(line)
    return ordered
