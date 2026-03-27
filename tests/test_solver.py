import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sed_model22.config import PlanViewScenarioConfig, load_scenario  # noqa: E402
from sed_model22.mesh import build_structured_mesh  # noqa: E402
from sed_model22.metrics import compute_scenario_metrics  # noqa: E402
from sed_model22.solver import solve_steady_screening_flow  # noqa: E402


BASELINE_SCENARIO_PATH = ROOT / "scenarios" / "baseline_rectangular_basin.yaml"
EMPTY_SCENARIO_PATH = ROOT / "scenarios" / "verification_empty_basin.yaml"


class SolverTests(unittest.TestCase):
    def test_empty_basin_solution_balances_mass(self) -> None:
        scenario = load_scenario(EMPTY_SCENARIO_PATH)
        mesh = build_structured_mesh(scenario)
        metrics = compute_scenario_metrics(scenario)
        summary, fields = solve_steady_screening_flow(scenario, mesh, metrics)

        self.assertEqual(summary.solver_status, "solved_screening_flow")
        self.assertLess(summary.mass_balance_error, 1.0e-3)
        self.assertGreater(summary.max_velocity_m_s, 0.0)
        self.assertEqual(len(fields.speed_m_s), mesh.nx)
        self.assertEqual(len(fields.speed_m_s[0]), mesh.ny)

    def test_baffle_case_induces_transverse_velocity(self) -> None:
        scenario = load_scenario(BASELINE_SCENARIO_PATH)
        mesh = build_structured_mesh(scenario)
        metrics = compute_scenario_metrics(scenario)
        summary, _fields = solve_steady_screening_flow(scenario, mesh, metrics)

        self.assertGreater(summary.blocked_face_count, 0)
        self.assertGreater(summary.max_transverse_velocity_m_s, 1.0e-8)

    def test_placeholder_baffles_are_ignored_but_do_not_break_solution(self) -> None:
        scenario = PlanViewScenarioConfig.model_validate(
            {
                "metadata": {"case_id": "placeholder-case", "title": "Placeholder Case"},
                "geometry": {"length_m": 40.0, "width_m": 10.0, "water_depth_m": 3.0},
                "hydraulics": {"flow_rate_m3_s": 0.4},
                "inlet": {"side": "west", "center_m": 5.0, "span_m": 2.0},
                "outlet": {"side": "east", "center_m": 5.0, "span_m": 2.0},
                "baffles": [
                    {
                        "name": "porous_note_only",
                        "kind": "porous_placeholder",
                        "x1_m": 15.0,
                        "y1_m": 1.0,
                        "x2_m": 15.0,
                        "y2_m": 9.0,
                    }
                ],
            }
        )

        mesh = build_structured_mesh(scenario)
        metrics = compute_scenario_metrics(scenario)
        summary, _fields = solve_steady_screening_flow(scenario, mesh, metrics)

        self.assertIn("porous_note_only", summary.ignored_baffles)


if __name__ == "__main__":
    unittest.main()
