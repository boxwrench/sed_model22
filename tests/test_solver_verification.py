import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sed_model22.config import load_scenario  # noqa: E402
from sed_model22.mesh import build_structured_mesh  # noqa: E402
from sed_model22.metrics import compute_scenario_metrics  # noqa: E402
from sed_model22.solver import solve_steady_screening_flow  # noqa: E402


EMPTY_SCENARIO_PATH = ROOT / "scenarios" / "verification_empty_basin.yaml"


class SolverVerificationTests(unittest.TestCase):
    def _solve_empty_basin(self):
        scenario = load_scenario(EMPTY_SCENARIO_PATH)
        mesh = build_structured_mesh(scenario)
        metrics = compute_scenario_metrics(scenario)
        summary, fields = solve_steady_screening_flow(scenario, mesh, metrics)
        return scenario, mesh, summary, fields

    def test_empty_basin_interior_is_symmetric_about_centerline(self) -> None:
        _scenario, mesh, summary, fields = self._solve_empty_basin()

        self.assertTrue(summary.converged)

        for column_index in (mesh.nx // 4, mesh.nx // 2, (3 * mesh.nx) // 4):
            head_column = fields.head[column_index]
            u_column = fields.velocity_u_m_s[column_index]
            v_column = fields.velocity_v_m_s[column_index]

            head_symmetry_error = max(abs(head_column[j] - head_column[-1 - j]) for j in range(mesh.ny))
            u_symmetry_error = max(abs(u_column[j] - u_column[-1 - j]) for j in range(mesh.ny))
            v_antisymmetry_error = max(abs(v_column[j] + v_column[-1 - j]) for j in range(mesh.ny))

            self.assertLess(head_symmetry_error, 1.0e-5)
            self.assertLess(u_symmetry_error, 1.0e-6)
            self.assertLess(v_antisymmetry_error, 1.0e-6)

    def test_empty_basin_centerline_head_and_velocity_are_monotone(self) -> None:
        _scenario, mesh, _summary, fields = self._solve_empty_basin()

        center_row = mesh.ny // 2
        head_centerline = [fields.head[i][center_row] for i in range(mesh.nx)]
        u_centerline = [fields.velocity_u_m_s[i][center_row] for i in range(mesh.nx)]

        for left, right in zip(head_centerline, head_centerline[1:]):
            self.assertGreaterEqual(left, right)

        for velocity in u_centerline[1:-1]:
            self.assertGreater(velocity, 0.0)


if __name__ == "__main__":
    unittest.main()
