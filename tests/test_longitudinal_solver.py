import math
import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sed_model22.config import load_scenario  # noqa: E402
from sed_model22.mesh import build_longitudinal_mesh  # noqa: E402
from sed_model22.metrics import compute_longitudinal_metrics  # noqa: E402
from sed_model22.solver.longitudinal import (  # noqa: E402
    _perforated_baffle_conductance,
    simulate_longitudinal_tracer,
    solve_steady_longitudinal_screening_flow,
)


DESIGN_SCENARIO_PATH = ROOT / "scenarios" / "svwtp_design_spec_basin.yaml"
CURRENT_SCENARIO_PATH = ROOT / "scenarios" / "svwtp_current_blocked_wall_basin.yaml"


class LongitudinalSolverTests(unittest.TestCase):
    def _solve(self, scenario_path: Path):
        scenario = load_scenario(scenario_path)
        mesh = build_longitudinal_mesh(scenario)
        solver_summary, fields = solve_steady_longitudinal_screening_flow(scenario, mesh)
        tracer = simulate_longitudinal_tracer(scenario, mesh, fields)
        metrics = compute_longitudinal_metrics(scenario, mesh, fields, tracer)
        return scenario, mesh, solver_summary, fields, tracer, metrics

    def test_perforated_wall_conductance_decreases_with_open_area(self) -> None:
        open_conductance = _perforated_baffle_conductance(0.06, 1.0)
        blocked_conductance = _perforated_baffle_conductance(0.001, 4.0)

        self.assertGreater(open_conductance, blocked_conductance)

    def test_blocked_wall_case_produces_more_transition_headloss(self) -> None:
        _design, _mesh, _solver_design, _fields_design, _tracer_design, design_metrics = self._solve(
            DESIGN_SCENARIO_PATH
        )
        _current, _mesh, _solver_current, _fields_current, _tracer_current, current_metrics = self._solve(
            CURRENT_SCENARIO_PATH
        )

        self.assertGreater(current_metrics.transition_headloss_m, design_metrics.transition_headloss_m)

    def test_plate_settler_zone_changes_upper_zone_velocity_pattern(self) -> None:
        scenario = load_scenario(DESIGN_SCENARIO_PATH)
        mesh = build_longitudinal_mesh(scenario)
        _solver_summary, fields_with_plate = solve_steady_longitudinal_screening_flow(scenario, mesh)

        no_plate_features = [feature for feature in scenario.features if feature.kind != "plate_settler_zone"]
        scenario_no_plate = scenario.model_copy(update={"features": no_plate_features})
        _solver_summary, fields_without_plate = solve_steady_longitudinal_screening_flow(scenario_no_plate, mesh)

        upper_band_with_plate = self._upper_band_mean(fields_with_plate.speed_m_s)
        upper_band_without_plate = self._upper_band_mean(fields_without_plate.speed_m_s)

        self.assertNotAlmostEqual(upper_band_with_plate, upper_band_without_plate, places=6)

    def test_launder_mass_balance_and_tracer_ordering(self) -> None:
        _scenario, _mesh, solver_summary, _fields, tracer, _metrics = self._solve(DESIGN_SCENARIO_PATH)

        self.assertTrue(math.isfinite(solver_summary.mass_balance_error))
        self.assertGreaterEqual(solver_summary.mass_balance_error, 0.0)
        self.assertIn("mass balance error is a screening-flow discharge mismatch diagnostic", " ".join(solver_summary.notes))
        self.assertIn("RTD proxy", " ".join(solver_summary.notes))
        self.assertEqual(tracer.proxy_model, "steady_rtd_proxy_v1")
        self.assertTrue(any("RTD proxy" in note for note in tracer.notes))
        self.assertLessEqual(tracer.step_count, 180)
        self.assertTrue(math.isfinite(tracer.t10_s))
        self.assertTrue(math.isfinite(tracer.t50_s))
        self.assertTrue(math.isfinite(tracer.t90_s))
        self.assertLess(tracer.t10_s, tracer.t50_s)
        self.assertLess(tracer.t50_s, tracer.t90_s)
        self.assertTrue(any("RTD proxy" in note for note in _metrics.notes))

    def test_tracer_handles_zero_velocity_edge_case(self) -> None:
        """Verify tracer simulation handles near-zero velocity fields gracefully."""
        # Create a minimal scenario with very low flow
        scenario = load_scenario(DESIGN_SCENARIO_PATH)
        minimal_scenario = scenario.model_copy(
            update={
                "hydraulics": scenario.hydraulics.model_copy(update={"flow_rate_m3_s": 0.001}),
                "numerics": scenario.numerics.model_copy(
                    update={"nx": 10, "nz": 5, "max_iterations": 200}
                ),
            }
        )
        mesh = build_longitudinal_mesh(minimal_scenario)
        _solver_summary, fields = solve_steady_longitudinal_screening_flow(minimal_scenario, mesh)

        tracer = simulate_longitudinal_tracer(minimal_scenario, mesh, fields)

        # Tracer should complete or terminate gracefully even with very low flow
        self.assertIsNotNone(tracer)
        self.assertTrue(math.isfinite(tracer.t10_s) or tracer.termination_reason == "max_steps_reached")
        self.assertIn(tracer.termination_reason, ["rtd_proxy_target_fraction_reached", "max_steps_reached", "stagnant"])

    @staticmethod
    def _upper_band_mean(speed_field: list[list[float]]) -> float:
        upper_rows = [row for row in speed_field if row]
        if not upper_rows:
            return 0.0
        midpoint = len(upper_rows[0]) // 2
        values = [value for row in upper_rows for value in row[midpoint:]]
        return sum(values) / len(values)


if __name__ == "__main__":
    unittest.main()
