import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sed_model22.config import load_scenario  # noqa: E402
from sed_model22.mesh import build_longitudinal_mesh  # noqa: E402
from sed_model22.metrics import compute_longitudinal_metrics  # noqa: E402
from sed_model22.solver.longitudinal import (  # noqa: E402
    simulate_longitudinal_tracer,
    solve_steady_longitudinal_screening_flow,
)


DESIGN_SCENARIO_PATH = ROOT / "scenarios" / "svwtp_design_spec_basin.yaml"
CURRENT_SCENARIO_PATH = ROOT / "scenarios" / "svwtp_current_blocked_wall_basin.yaml"


def _solve_with_mesh(path: Path, *, nx: int, nz: int):
    scenario = load_scenario(path)
    scenario = scenario.model_copy(
        update={
            "numerics": scenario.numerics.model_copy(
                update={"nx": nx, "nz": nz, "max_iterations": 4000}
            )
        }
    )
    mesh = build_longitudinal_mesh(scenario)
    _summary, fields = solve_steady_longitudinal_screening_flow(scenario, mesh)
    tracer = simulate_longitudinal_tracer(scenario, mesh, fields)
    metrics = compute_longitudinal_metrics(scenario, mesh, fields, tracer)
    return metrics


class MeshSensitivitySmokeTests(unittest.TestCase):
    def test_design_case_dimensionless_rtd_metrics_are_stable_between_meshes(self) -> None:
        coarse_metrics = _solve_with_mesh(DESIGN_SCENARIO_PATH, nx=36, nz=12)
        baseline_metrics = _solve_with_mesh(DESIGN_SCENARIO_PATH, nx=72, nz=24)

        self.assertAlmostEqual(
            coarse_metrics.short_circuiting_index,
            baseline_metrics.short_circuiting_index,
            delta=2.0e-4,
        )
        self.assertAlmostEqual(
            coarse_metrics.morrill_index,
            baseline_metrics.morrill_index,
            delta=0.05,
        )
        self.assertGreater(coarse_metrics.transition_headloss_m, 0.0)
        self.assertGreater(baseline_metrics.transition_headloss_m, 0.0)

    def test_design_vs_current_directional_signal_survives_mesh_change(self) -> None:
        design_coarse = _solve_with_mesh(DESIGN_SCENARIO_PATH, nx=36, nz=12)
        current_coarse = _solve_with_mesh(CURRENT_SCENARIO_PATH, nx=36, nz=12)
        design_baseline = _solve_with_mesh(DESIGN_SCENARIO_PATH, nx=72, nz=24)
        current_baseline = _solve_with_mesh(CURRENT_SCENARIO_PATH, nx=72, nz=24)

        self.assertLess(current_coarse.transition_headloss_m, design_coarse.transition_headloss_m)
        self.assertLess(current_baseline.transition_headloss_m, design_baseline.transition_headloss_m)
        self.assertGreater(current_coarse.short_circuiting_index, design_coarse.short_circuiting_index)
        self.assertGreater(current_baseline.short_circuiting_index, design_baseline.short_circuiting_index)
        self.assertLess(current_coarse.morrill_index, design_coarse.morrill_index)
        self.assertLess(current_baseline.morrill_index, design_baseline.morrill_index)


if __name__ == "__main__":
    unittest.main()
