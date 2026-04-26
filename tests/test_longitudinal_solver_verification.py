import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sed_model22.config import LongitudinalScenarioConfig, load_scenario  # noqa: E402
from sed_model22.mesh import build_longitudinal_mesh  # noqa: E402
from sed_model22.solver.longitudinal import solve_steady_longitudinal_screening_flow  # noqa: E402


DESIGN_SCENARIO_PATH = ROOT / "scenarios" / "svwtp_design_spec_basin.yaml"


class LongitudinalSolverVerificationTests(unittest.TestCase):
    def _build_uniform_conductance_scenario(self) -> LongitudinalScenarioConfig:
        baseline = load_scenario(DESIGN_SCENARIO_PATH)
        scenario_data = baseline.model_dump()
        scenario_data["features"] = [feature for feature in scenario_data["features"] if feature["kind"] == "launder_zone"]
        scenario_data["upstream"].update(
            {
                "mixing_zone_length_m": 1.0e-6,
                "mixing_intensity_factor": 1.0e-6,
                "inlet_zone_height_m": baseline.geometry.water_depth_m,
                "inlet_zone_center_elevation_m": baseline.geometry.water_depth_m / 2.0,
                "inlet_orifice_count": 100,
                "inlet_loss_coefficient": 0.0,
            }
        )
        scenario_data["numerics"].update({"nx": 24, "nz": 12, "max_iterations": 6000})
        return LongitudinalScenarioConfig.model_validate(scenario_data)

    def test_uniform_conductance_case_has_nearly_linear_interior_head_gradient(self) -> None:
        scenario = self._build_uniform_conductance_scenario()
        mesh = build_longitudinal_mesh(scenario)
        summary, fields = solve_steady_longitudinal_screening_flow(scenario, mesh)

        self.assertTrue(summary.converged)

        column_mean_head = [sum(column) / len(column) for column in fields.head]
        interior_mean_head = column_mean_head[:-3]
        adjacent_drops = [
            interior_mean_head[index] - interior_mean_head[index + 1]
            for index in range(len(interior_mean_head) - 1)
        ]
        second_differences = [
            abs(interior_mean_head[index - 1] - (2.0 * interior_mean_head[index]) + interior_mean_head[index + 1])
            for index in range(1, len(interior_mean_head) - 1)
        ]
        interior_column_limit = int(mesh.nx * 0.7)
        interior_upward_velocity = [
            abs(fields.velocity_w_m_s[i][k])
            for i in range(interior_column_limit)
            for k in range(mesh.nz)
        ]

        self.assertGreater(min(adjacent_drops), 0.0)
        self.assertLess(max(adjacent_drops) / min(adjacent_drops), 1.02)
        self.assertLess(max(second_differences), 1.0e-4)
        self.assertLess(max(interior_upward_velocity), 1.0e-4)

    def test_perforated_wall_introduces_head_jump_absent_in_uniform_case(self) -> None:
        uniform_scenario = self._build_uniform_conductance_scenario()
        mesh = build_longitudinal_mesh(uniform_scenario)
        face_index = 5
        wall_x_m = face_index * mesh.dx_m

        uniform_summary, uniform_fields = solve_steady_longitudinal_screening_flow(uniform_scenario, mesh)
        uniform_gap = self._column_mean(uniform_fields.head[face_index - 1]) - self._column_mean(
            uniform_fields.head[face_index]
        )

        wall_data = uniform_scenario.model_dump()
        wall_data["features"].append(
            {
                "kind": "perforated_baffle",
                "name": "verification_wall",
                "x_m": wall_x_m,
                "z_bottom_m": 0.0,
                "z_top_m": uniform_scenario.geometry.water_depth_m,
                "open_area_fraction": 0.06,
                "plate_thickness_m": 0.02,
                "loss_scale": 1.0,
            }
        )
        wall_scenario = LongitudinalScenarioConfig.model_validate(wall_data)
        wall_mesh = build_longitudinal_mesh(wall_scenario)
        wall_summary, wall_fields = solve_steady_longitudinal_screening_flow(wall_scenario, wall_mesh)
        wall_gap = self._column_mean(wall_fields.head[face_index - 1]) - self._column_mean(wall_fields.head[face_index])

        self.assertTrue(uniform_summary.converged)
        self.assertTrue(wall_summary.converged)
        self.assertGreater(wall_gap, uniform_gap * 10.0)

    @staticmethod
    def _column_mean(values: list[float]) -> float:
        return sum(values) / len(values)


if __name__ == "__main__":
    unittest.main()
