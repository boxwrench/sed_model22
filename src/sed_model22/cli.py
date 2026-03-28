from __future__ import annotations

import argparse
from pathlib import Path
import sys

from pydantic import ValidationError

from .config import LongitudinalScenarioConfig, PlanViewScenarioConfig, load_scenario, load_study
from .run import (
    load_fields,
    load_scenario_snapshot,
    load_summary,
    load_tracer,
    materialize_run,
)
from .study import run_comparison_study
from .viz import (
    write_layout_svg,
    write_longitudinal_layout_svg,
    write_longitudinal_tracer_breakthrough_svg,
    write_longitudinal_velocity_heatmap_svg,
    write_plan_view_streamline_svg,
    write_velocity_heatmap_svg,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="sed_model22 project CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate a scenario YAML file.")
    validate_parser.add_argument("scenario", help="Path to a scenario YAML file.")

    validate_study_parser = subparsers.add_parser("validate-study", help="Validate a study YAML file.")
    validate_study_parser.add_argument("study", help="Path to a study YAML file.")

    run_parser = subparsers.add_parser(
        "run-hydraulics",
        help="Create a hydraulic run bundle for a validated scenario.",
    )
    run_parser.add_argument("scenario", help="Path to a scenario YAML file.")
    run_parser.add_argument(
        "--run-root",
        help="Override the run root directory for artifact output.",
    )
    run_parser.add_argument(
        "--flow-rate-m3-s",
        type=float,
        help="Override the scenario flow rate without rewriting the YAML file.",
    )
    run_parser.add_argument(
        "--media-policy",
        choices=["off", "still_only", "best_effort_preview", "require_preview"],
        default="best_effort_preview",
        help="Control voxel and preview generation for the run bundle.",
    )

    summarize_parser = subparsers.add_parser("summarize", help="Print a concise run summary.")
    summarize_parser.add_argument("run_dir", help="Path to a run directory.")

    plot_parser = subparsers.add_parser("plot", help="Regenerate run SVG outputs.")
    plot_parser.add_argument("run_dir", help="Path to a run directory.")
    plot_parser.add_argument(
        "--output",
        help="Optional explicit SVG output path. Defaults to <run_dir>/plots/basin_layout.svg.",
    )

    compare_study_parser = subparsers.add_parser(
        "compare-study",
        help="Run a comparison study and write comparison artifacts.",
    )
    compare_study_parser.add_argument("study", help="Path to a study YAML file.")

    return parser


def _format_validation_summary(scenario) -> str:
    if isinstance(scenario, LongitudinalScenarioConfig):
        return (
            f"Validated longitudinal scenario '{scenario.metadata.case_id}' "
            f"({scenario.geometry.basin_length_m:.1f} m x {scenario.geometry.basin_width_m:.1f} m x "
            f"{scenario.geometry.water_depth_m:.1f} m, {len(scenario.features)} features, "
            f"{len(scenario.evaluation_stations)} stations)."
        )

    return (
        f"Validated scenario '{scenario.metadata.case_id}' "
        f"({scenario.geometry.length_m:.1f} m x {scenario.geometry.width_m:.1f} m x "
        f"{scenario.geometry.water_depth_m:.1f} m, {len(scenario.baffles)} baffles)."
    )


def _format_study_validation_summary(study) -> str:
    return f"Validated study '{study.study_id}' ({len(study.cases)} cases, {len(study.flows)} flows)."


def _format_run_summary(summary: dict) -> str:
    metadata = summary["metadata"]
    metrics = summary["metrics"]
    mesh = summary["mesh"]
    solver = summary["solver"]
    model_form = summary.get("model_form")

    if model_form == "longitudinal_v0_2":
        detention_time_s = metrics["theoretical_detention_time_s"]
        detention_time_h = detention_time_s / 3600.0
        tracer = summary.get("tracer", {})
        lines = [
            f"Case: {metadata['case_id']}",
            f"Stage: {metadata['stage']}",
            f"Model form: {model_form}",
            f"Detention time: {detention_time_h:.2f} h ({detention_time_s:.0f} s)",
            f"Headloss across transition wall: {metrics['transition_headloss_m']:.4f} m",
            f"Post-transition VUI: {metrics['post_transition_velocity_uniformity_index']:.4f}",
            f"Jet redistribution length: {metrics['jet_redistribution_length_m']:.2f} m",
            f"RTD proxy model: {tracer.get('proxy_model', 'steady_rtd_proxy_v1')}",
            (
                "RTD proxy breakthrough: "
                f"t10 {tracer.get('t10_s', metrics['t10_s']):.0f} s, "
                f"t50 {tracer.get('t50_s', metrics['t50_s']):.0f} s, "
                f"t90 {tracer.get('t90_s', metrics['t90_s']):.0f} s"
            ),
            f"Launder peak upward velocity: {metrics['launder_peak_upward_velocity_m_s']:.5f} m/s",
            f"Short-circuiting index: {metrics['short_circuiting_index']:.4f}",
            f"Morrill index: {metrics['morrill_index']:.4f}",
            f"Solver status: {solver['solver_status']}",
        ]
        return "\n".join(lines)

    lines = [
        f"Case: {metadata['case_id']}",
        f"Stage: {metadata['stage']}",
        f"Detention time: {metrics['detention_time_h']:.2f} h",
        f"Surface overflow rate: {metrics['surface_overflow_rate_m_per_d']:.2f} m/day",
        f"Mesh: {mesh['nx']} x {mesh['ny']} ({mesh['cell_count']} cells)",
        f"Solver status: {solver['solver_status']}",
        f"Mass balance error: {solver['mass_balance_error']:.3e}",
        f"Max velocity: {solver['max_velocity_m_s']:.4f} m/s",
        "Operator report: operator_report.html",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "validate":
            scenario = load_scenario(args.scenario)
            print(_format_validation_summary(scenario))
            return 0

        if args.command == "validate-study":
            study = load_study(args.study)
            print(_format_study_validation_summary(study))
            return 0

        if args.command == "run-hydraulics":
            scenario = load_scenario(args.scenario)
            artifacts = materialize_run(
                scenario_path=args.scenario,
                scenario=scenario,
                run_root_override=args.run_root,
                flow_rate_m3_s=args.flow_rate_m3_s,
                media_policy=args.media_policy,
            )
            print(f"Created hydraulic run at {artifacts.run_dir}")
            if artifacts.voxel_plot_path:
                print(f"Voxel still: {artifacts.voxel_plot_path}")
            if artifacts.preview_video_path:
                print(f"Preview video: {artifacts.preview_video_path}")
            elif artifacts.media_manifest_path:
                print(f"Media manifest: {artifacts.media_manifest_path}")
            return 0

        if args.command == "summarize":
            summary = load_summary(args.run_dir)
            print(_format_run_summary(summary))
            return 0

        if args.command == "plot":
            scenario = load_scenario_snapshot(args.run_dir)

            if args.output:
                output_path = Path(args.output)
                if isinstance(scenario, LongitudinalScenarioConfig):
                    write_longitudinal_layout_svg(scenario, output_path)
                else:
                    write_layout_svg(scenario, output_path)
                print(f"Wrote layout SVG to {output_path}")
                return 0

            plots_dir = Path(args.run_dir) / "plots"
            if isinstance(scenario, LongitudinalScenarioConfig):
                layout_path = write_longitudinal_layout_svg(scenario, plots_dir / "basin_layout.svg")
                print(f"Wrote layout SVG to {layout_path}")

                fields_path = Path(args.run_dir) / "fields.json"
                if fields_path.exists():
                    fields = load_fields(args.run_dir)
                    if hasattr(fields, "z_centers_m"):
                        velocity_path = write_longitudinal_velocity_heatmap_svg(
                            scenario,
                            fields,
                            plots_dir / "velocity_magnitude.svg",
                        )
                        print(f"Wrote velocity SVG to {velocity_path}")

                tracer_path = Path(args.run_dir) / "tracer.json"
                if tracer_path.exists():
                    tracer = load_tracer(args.run_dir)
                    tracer_plot_path = write_longitudinal_tracer_breakthrough_svg(
                        scenario,
                        tracer,
                        plots_dir / "tracer_breakthrough.svg",
                    )
                    print(f"Wrote tracer SVG to {tracer_plot_path}")
                return 0

            layout_path = write_layout_svg(scenario, plots_dir / "basin_layout.svg")
            print(f"Wrote layout SVG to {layout_path}")

            fields_path = Path(args.run_dir) / "fields.json"
            if fields_path.exists():
                fields = load_fields(args.run_dir)
                velocity_path = write_velocity_heatmap_svg(
                    scenario,
                    fields,
                    plots_dir / "velocity_magnitude.svg",
                )
                print(f"Wrote velocity SVG to {velocity_path}")
                streamline_path = write_plan_view_streamline_svg(
                    scenario,
                    fields,
                    plots_dir / "streamlines.svg",
                )
                print(f"Wrote streamline SVG to {streamline_path}")
            return 0

        if args.command == "compare-study":
            artifacts = run_comparison_study(args.study)
            print(f"Created comparison study at {artifacts.study_dir}")
            print(f"Report: {artifacts.report_path}")
            return 0

        parser.error(f"Unknown command: {args.command}")
        return 2
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except (ValidationError, ValueError) as exc:
        print(f"validation error: {exc}", file=sys.stderr)
        return 2
