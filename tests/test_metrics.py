import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sed_model22.config import LongitudinalScenarioConfig  # noqa: E402
from sed_model22.mesh.longitudinal import LongitudinalMeshSummary  # noqa: E402
from sed_model22.metrics import compute_longitudinal_metrics  # noqa: E402
from sed_model22.solver.longitudinal import LongitudinalFieldData, LongitudinalTracerSummary  # noqa: E402


def _build_metrics_fixture() -> tuple[
    LongitudinalScenarioConfig,
    LongitudinalMeshSummary,
    LongitudinalFieldData,
    LongitudinalTracerSummary,
]:
    scenario = LongitudinalScenarioConfig.model_validate(
        {
            "metadata": {"case_id": "metrics_fixture", "title": "Metrics Fixture"},
            "geometry": {"basin_length_m": 4.0, "basin_width_m": 2.0, "water_depth_m": 4.0},
            "hydraulics": {"flow_rate_m3_s": 1.0},
            "upstream": {
                "inlet_zone_height_m": 4.0,
                "inlet_zone_center_elevation_m": 2.0,
                "inlet_orifice_count": 4,
                "inlet_loss_coefficient": 0.0,
                "mixing_zone_length_m": 0.0,
                "mixing_intensity_factor": 1.0,
            },
            "features": [
                {
                    "kind": "perforated_baffle",
                    "name": "transition_wall",
                    "x_m": 1.0,
                    "z_bottom_m": 0.0,
                    "z_top_m": 4.0,
                    "open_area_fraction": 0.3,
                    "plate_thickness_m": 0.02,
                    "loss_scale": 1.0,
                },
                {"kind": "launder_zone", "name": "launder", "x_start_m": 2.0, "x_end_m": 4.0, "z_m": 4.0, "sink_weight": 1.0},
            ],
            "evaluation_stations": [
                {"name": "post_transition", "x_m": 1.5},
                {"name": "plate_inlet", "x_m": 2.5},
            ],
            "performance_proxies": {
                "settling_velocity_thresholds_m_per_s": [0.1, 0.3],
                "dead_zone_velocity_fraction": 0.5,
                "tracer_max_time_factor": 2.0,
                "tracer_target_fraction": 0.95,
            },
            "numerics": {"nx": 4, "nz": 4},
        }
    )
    mesh = LongitudinalMeshSummary(nx=4, nz=4, dx_m=1.0, dz_m=1.0, cell_count=16)
    fields = LongitudinalFieldData(
        x_centers_m=[0.5, 1.5, 2.5, 3.5],
        z_centers_m=[0.5, 1.5, 2.5, 3.5],
        head=[
            [1.0, 0.95, 0.9, 0.85],
            [0.7, 0.65, 0.6, 0.55],
            [0.5, 0.45, 0.4, 0.35],
            [0.3, 0.25, 0.2, 0.15],
        ],
        velocity_u_m_s=[
            [0.8, 0.8, 0.8, 0.8],
            [1.0, 0.75, 0.5, 0.25],
            [0.2, 0.6, 0.4, 0.8],
            [0.1, 0.1, 0.1, 0.1],
        ],
        velocity_w_m_s=[
            [0.0, 0.1, 0.0, 0.1],
            [0.0, 0.1, 0.0, 0.1],
            [0.0, 0.0, 0.0, 0.4],
            [0.0, 0.0, 0.0, 0.2],
        ],
        speed_m_s=[
            [1.0, 1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0, 1.0],
            [0.1, 0.1, 0.1, 0.1],
            [0.1, 0.1, 0.1, 0.1],
        ],
        cell_divergence_1_per_s=[[0.0] * 4 for _ in range(4)],
    )
    tracer = LongitudinalTracerSummary(
        time_points_s=[0.0, 10.0, 20.0, 30.0],
        outlet_concentration_history=[0.0, 0.2, 0.7, 1.0],
        t10_s=10.0,
        t50_s=20.0,
        t90_s=30.0,
        final_time_s=30.0,
        final_outlet_concentration=1.0,
        converged=True,
        termination_reason="rtd_proxy_target_fraction_reached",
        step_count=3,
    )
    return scenario, mesh, fields, tracer


class LongitudinalMetricsTests(unittest.TestCase):
    def test_dead_zone_fraction_uses_speed_threshold(self) -> None:
        scenario, mesh, fields, tracer = _build_metrics_fixture()

        metrics = compute_longitudinal_metrics(scenario, mesh, fields, tracer)

        self.assertAlmostEqual(metrics.dead_zone_fraction, 0.5)

    def test_post_transition_uniformity_index_uses_station_column(self) -> None:
        scenario, mesh, fields, tracer = _build_metrics_fixture()

        metrics = compute_longitudinal_metrics(scenario, mesh, fields, tracer)

        self.assertAlmostEqual(metrics.post_transition_velocity_uniformity_index, 0.625)
        self.assertAlmostEqual(metrics.transition_headloss_m, 0.3)

    def test_morrill_index_comes_from_tracer_quantiles(self) -> None:
        scenario, mesh, fields, tracer = _build_metrics_fixture()

        metrics = compute_longitudinal_metrics(scenario, mesh, fields, tracer)

        self.assertAlmostEqual(metrics.morrill_index, 3.0)
        self.assertAlmostEqual(metrics.short_circuiting_index, 0.3125)
        self.assertEqual(metrics.settling_exceedance_fraction_by_threshold, {"0.1": 1.0, "0.3": 0.5})


if __name__ == "__main__":
    unittest.main()
