import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sed_model22.config import LongitudinalScenarioConfig  # noqa: E402
from sed_model22.mesh import build_longitudinal_mesh  # noqa: E402
from sed_model22.solver.longitudinal import solve_steady_longitudinal_screening_flow  # noqa: E402


def _build_longitudinal_scenario(*, extra_features: list[dict] | None = None) -> LongitudinalScenarioConfig:
    features = [
        {"kind": "launder_zone", "name": "launder", "x_start_m": 9.0, "x_end_m": 12.0, "z_m": 4.0, "sink_weight": 1.0},
    ]
    if extra_features:
        features.extend(extra_features)

    return LongitudinalScenarioConfig.model_validate(
        {
            "metadata": {"case_id": "verification_longitudinal", "title": "Longitudinal Verification"},
            "geometry": {"basin_length_m": 12.0, "basin_width_m": 4.0, "water_depth_m": 4.0},
            "hydraulics": {"flow_rate_m3_s": 1.2},
            "upstream": {
                "inlet_zone_height_m": 4.0,
                "inlet_zone_center_elevation_m": 2.0,
                "inlet_orifice_count": 20,
                "inlet_loss_coefficient": 0.0,
                "mixing_zone_length_m": 0.0,
                "mixing_intensity_factor": 1.0,
            },
            "features": features,
            "evaluation_stations": [
                {"name": "post_transition", "x_m": 6.5},
                {"name": "plate_inlet", "x_m": 9.5},
            ],
            "performance_proxies": {
                "settling_velocity_thresholds_m_per_s": [0.001],
                "dead_zone_velocity_fraction": 0.5,
                "tracer_max_time_factor": 2.0,
                "tracer_target_fraction": 0.95,
            },
            "numerics": {"nx": 12, "nz": 8, "max_iterations": 8000, "tolerance": 1.0e-8},
        }
    )


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


class LongitudinalSolverVerificationTests(unittest.TestCase):
    def test_uniform_conductance_case_has_expected_head_gradient(self) -> None:
        scenario = _build_longitudinal_scenario()
        mesh = build_longitudinal_mesh(scenario)
        summary, fields = solve_steady_longitudinal_screening_flow(scenario, mesh)

        column_mean_heads = [_mean(column) for column in fields.head]
        min_u = min(value for column in fields.velocity_u_m_s for value in column)

        self.assertEqual(summary.low_conductance_face_count, 0)
        self.assertEqual(summary.blocked_face_count, 0)
        self.assertTrue(
            all(
                column_mean_heads[i] > column_mean_heads[i + 1]
                for i in range(len(column_mean_heads) - 1)
            )
        )
        self.assertLess(fields.head[10][-1], fields.head[10][0])
        self.assertGreater(min_u, 0.0)

    def test_perforated_transition_wall_reduces_upper_downstream_velocity(self) -> None:
        open_scenario = _build_longitudinal_scenario()
        wall_scenario = _build_longitudinal_scenario(
            extra_features=[
                {
                    "kind": "perforated_baffle",
                    "name": "transition_wall",
                    "x_m": 6.0,
                    "z_bottom_m": 1.5,
                    "z_top_m": 4.0,
                    "open_area_fraction": 0.12,
                    "plate_thickness_m": 0.02,
                    "loss_scale": 1.5,
                }
            ]
        )

        open_mesh = build_longitudinal_mesh(open_scenario)
        wall_mesh = build_longitudinal_mesh(wall_scenario)
        open_summary, open_fields = solve_steady_longitudinal_screening_flow(open_scenario, open_mesh)
        wall_summary, wall_fields = solve_steady_longitudinal_screening_flow(wall_scenario, wall_mesh)

        downstream_column = 6
        open_upper_mean_u = _mean(open_fields.velocity_u_m_s[downstream_column][4:])
        wall_upper_mean_u = _mean(wall_fields.velocity_u_m_s[downstream_column][4:])
        open_lower_mean_u = _mean(open_fields.velocity_u_m_s[downstream_column][:4])
        wall_lower_mean_u = _mean(wall_fields.velocity_u_m_s[downstream_column][:4])
        open_head_drop = _mean(open_fields.head[5]) - _mean(open_fields.head[6])
        wall_head_drop = _mean(wall_fields.head[5]) - _mean(wall_fields.head[6])

        self.assertGreater(wall_summary.low_conductance_face_count, open_summary.low_conductance_face_count)
        self.assertLess(wall_upper_mean_u, 0.5 * open_upper_mean_u)
        self.assertGreater(wall_lower_mean_u, 1.5 * open_lower_mean_u)
        self.assertGreater(wall_head_drop, 2.0 * open_head_drop)


if __name__ == "__main__":
    unittest.main()
