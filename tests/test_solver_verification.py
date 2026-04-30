import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sed_model22.config import PlanViewScenarioConfig  # noqa: E402
from sed_model22.mesh import build_structured_mesh  # noqa: E402
from sed_model22.metrics import compute_scenario_metrics  # noqa: E402
from sed_model22.solver import solve_steady_screening_flow  # noqa: E402


def _build_plan_view_scenario(*, span_m: float) -> PlanViewScenarioConfig:
    return PlanViewScenarioConfig.model_validate(
        {
            "metadata": {"case_id": f"verification_{span_m:g}", "title": "Verification Case"},
            "geometry": {"length_m": 40.0, "width_m": 10.0, "water_depth_m": 3.0},
            "hydraulics": {"flow_rate_m3_s": 1.2},
            "inlet": {"side": "west", "center_m": 5.0, "span_m": span_m},
            "outlet": {"side": "east", "center_m": 5.0, "span_m": span_m},
            "numerics": {"nx": 40, "ny": 10, "max_iterations": 5000, "tolerance": 1.0e-8},
        }
    )


class PlanViewSolverVerificationTests(unittest.TestCase):
    def test_full_span_empty_basin_matches_linear_head_solution(self) -> None:
        scenario = _build_plan_view_scenario(span_m=10.0)
        mesh = build_structured_mesh(scenario)
        metrics = compute_scenario_metrics(scenario)
        summary, fields = solve_steady_screening_flow(scenario, mesh, metrics)

        column_means = [sum(fields.head[i]) / len(fields.head[i]) for i in range(mesh.nx)]
        expected_column_means = [
            1.0 - (((i + 0.5) * mesh.dx_m) / scenario.geometry.length_m)
            for i in range(mesh.nx)
        ]
        max_head_error = max(
            abs(actual - expected)
            for actual, expected in zip(column_means, expected_column_means)
        )
        max_cross_stream_variation = max(
            max(column) - min(column)
            for column in fields.head
        )
        center_column = mesh.nx // 2
        center_u_values = fields.velocity_u_m_s[center_column]

        self.assertLess(summary.mass_balance_error, 1.0e-10)
        self.assertLess(max_head_error, 1.0e-10)
        self.assertLess(max_cross_stream_variation, 1.0e-12)
        self.assertLess(summary.max_transverse_velocity_m_s, 1.0e-12)
        self.assertLess(max(center_u_values) - min(center_u_values), 1.0e-12)

    def test_centered_openings_produce_symmetric_flow_field(self) -> None:
        scenario = _build_plan_view_scenario(span_m=2.0)
        mesh = build_structured_mesh(scenario)
        metrics = compute_scenario_metrics(scenario)
        summary, fields = solve_steady_screening_flow(scenario, mesh, metrics)

        max_head_symmetry_error = 0.0
        max_u_symmetry_error = 0.0
        max_v_antisymmetry_error = 0.0

        for i in range(mesh.nx):
            for j in range(mesh.ny):
                mirror_j = mesh.ny - 1 - j
                max_head_symmetry_error = max(
                    max_head_symmetry_error,
                    abs(fields.head[i][j] - fields.head[i][mirror_j]),
                )
                max_u_symmetry_error = max(
                    max_u_symmetry_error,
                    abs(fields.velocity_u_m_s[i][j] - fields.velocity_u_m_s[i][mirror_j]),
                )
                max_v_antisymmetry_error = max(
                    max_v_antisymmetry_error,
                    abs(fields.velocity_v_m_s[i][j] + fields.velocity_v_m_s[i][mirror_j]),
                )

        self.assertLess(summary.mass_balance_error, 1.0e-4)
        self.assertLess(max_head_symmetry_error, 1.0e-6)
        self.assertLess(max_u_symmetry_error, 1.0e-6)
        self.assertLess(max_v_antisymmetry_error, 1.0e-6)


if __name__ == "__main__":
    unittest.main()
