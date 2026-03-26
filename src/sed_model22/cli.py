from __future__ import annotations

import argparse
from pathlib import Path
import sys

from pydantic import ValidationError

from .config import load_scenario
from .run import load_fields, load_scenario_snapshot, load_summary, materialize_run
from .viz import write_layout_svg, write_velocity_heatmap_svg


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="sed_model22 project CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate a scenario YAML file.")
    validate_parser.add_argument("scenario", help="Path to a scenario YAML file.")

    run_parser = subparsers.add_parser(
        "run-hydraulics",
        help="Create a hydraulic run bundle for a validated scenario.",
    )
    run_parser.add_argument("scenario", help="Path to a scenario YAML file.")
    run_parser.add_argument(
        "--run-root",
        help="Override the run root directory for artifact output.",
    )

    summarize_parser = subparsers.add_parser("summarize", help="Print a concise run summary.")
    summarize_parser.add_argument("run_dir", help="Path to a run directory.")

    plot_parser = subparsers.add_parser("plot", help="Regenerate run SVG outputs.")
    plot_parser.add_argument("run_dir", help="Path to a run directory.")
    plot_parser.add_argument(
        "--output",
        help="Optional explicit SVG output path. Defaults to <run_dir>/plots/basin_layout.svg.",
    )

    return parser


def _format_validation_summary(scenario) -> str:
    return (
        f"Validated scenario '{scenario.metadata.case_id}' "
        f"({scenario.geometry.length_m:.1f} m x {scenario.geometry.width_m:.1f} m x "
        f"{scenario.geometry.water_depth_m:.1f} m, {len(scenario.baffles)} baffles)."
    )


def _format_run_summary(summary: dict) -> str:
    metadata = summary["metadata"]
    metrics = summary["metrics"]
    mesh = summary["mesh"]
    solver = summary["solver"]

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

        if args.command == "run-hydraulics":
            scenario = load_scenario(args.scenario)
            artifacts = materialize_run(
                scenario_path=args.scenario,
                scenario=scenario,
                run_root_override=args.run_root,
            )
            print(f"Created hydraulic run at {artifacts.run_dir}")
            return 0

        if args.command == "summarize":
            summary = load_summary(args.run_dir)
            print(_format_run_summary(summary))
            return 0

        if args.command == "plot":
            scenario = load_scenario_snapshot(args.run_dir)

            if args.output:
                output_path = Path(args.output)
                write_layout_svg(scenario, output_path)
                print(f"Wrote layout SVG to {output_path}")
                return 0

            layout_path = write_layout_svg(scenario, Path(args.run_dir) / "plots" / "basin_layout.svg")
            print(f"Wrote layout SVG to {layout_path}")

            fields_path = Path(args.run_dir) / "fields.json"
            if fields_path.exists():
                fields = load_fields(args.run_dir)
                velocity_path = write_velocity_heatmap_svg(
                    scenario,
                    fields,
                    Path(args.run_dir) / "plots" / "velocity_magnitude.svg",
                )
                print(f"Wrote velocity SVG to {velocity_path}")
            return 0

        parser.error(f"Unknown command: {args.command}")
        return 2
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except (ValidationError, ValueError) as exc:
        print(f"validation error: {exc}", file=sys.stderr)
        return 2
