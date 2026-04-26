import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sed_model22.config import load_scenario  # noqa: E402
from sed_model22.mesh import build_longitudinal_mesh  # noqa: E402
from sed_model22.metrics.longitudinal import compute_longitudinal_metrics  # noqa: E402
from sed_model22.solver.longitudinal import LongitudinalFieldData, LongitudinalTracerSummary  # noqa: E402


DESIGN_SCENARIO_PATH = ROOT / "scenarios" / "svwtp_design_spec_basin.yaml"


class LongitudinalMetricsTests(unittest.TestCase):
    def test_metrics_match_synthetic_dead_zone_uniformity_and_morrill_inputs(self) -> None:
        scenario = load_scenario(DESIGN_SCENARIO_PATH)
        scenario = scenario.model_copy(
            update={"numerics": scenario.numerics.model_copy(update={"nx": 6, "nz": 4})}
        )
        mesh = build_longitudinal_mesh(scenario)

        velocity_u = [
            [1.0, 2.0, 3.0, 4.0],
            [1.0, 1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0, 1.0],
        ]
        velocity_w = [
            [0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.03, 0.05],
        ]
        speed = [
            [0.01, 1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0, 0.01],
        ]
        head = [
            [1.00, 1.00, 1.00, 1.00],
            [0.95, 0.95, 0.95, 0.95],
            [0.90, 0.90, 0.90, 0.90],
            [0.85, 0.85, 0.85, 0.85],
            [0.80, 0.80, 0.80, 0.80],
            [0.75, 0.75, 0.75, 0.75],
        ]
        fields = LongitudinalFieldData(
            x_centers_m=[(index + 0.5) * mesh.dx_m for index in range(mesh.nx)],
            z_centers_m=[(index + 0.5) * mesh.dz_m for index in range(mesh.nz)],
            head=head,
            velocity_u_m_s=velocity_u,
            velocity_w_m_s=velocity_w,
            speed_m_s=speed,
            cell_divergence_1_per_s=[[0.0 for _ in range(mesh.nz)] for _ in range(mesh.nx)],
        )
        tracer = LongitudinalTracerSummary(
            time_points_s=[0.0, 100.0, 200.0, 400.0],
            outlet_concentration_history=[0.0, 0.1, 0.5, 0.9],
            t10_s=100.0,
            t50_s=200.0,
            t90_s=400.0,
            final_time_s=400.0,
            final_outlet_concentration=0.9,
            converged=False,
            termination_reason="rtd_proxy_time_horizon_reached",
            step_count=3,
        )

        metrics = compute_longitudinal_metrics(scenario, mesh, fields, tracer)

        expected_dead_zone_fraction = 2.0 / 24.0
        expected_uniformity_index = 2.5 / 4.0

        self.assertAlmostEqual(metrics.dead_zone_fraction, expected_dead_zone_fraction, places=6)
        self.assertAlmostEqual(metrics.post_transition_velocity_uniformity_index, expected_uniformity_index, places=6)
        self.assertAlmostEqual(metrics.morrill_index, 4.0, places=6)
        self.assertAlmostEqual(metrics.short_circuiting_index, 100.0 / metrics.theoretical_detention_time_s, places=6)


if __name__ == "__main__":
    unittest.main()
