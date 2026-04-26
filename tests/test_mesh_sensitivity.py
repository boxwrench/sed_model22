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
MESH_LEVELS = [(24, 8), (36, 12), (48, 16)]


class MeshSensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.design_profiles = cls._collect_profiles(DESIGN_SCENARIO_PATH)
        cls.current_profiles = cls._collect_profiles(CURRENT_SCENARIO_PATH)

    @classmethod
    def _collect_profiles(cls, scenario_path: Path) -> list[dict[str, float]]:
        baseline = load_scenario(scenario_path)
        profiles: list[dict[str, float]] = []

        for nx, nz in MESH_LEVELS:
            scenario = baseline.model_copy(
                update={"numerics": baseline.numerics.model_copy(update={"nx": nx, "nz": nz, "max_iterations": 5000})}
            )
            mesh = build_longitudinal_mesh(scenario)
            _summary, fields = solve_steady_longitudinal_screening_flow(scenario, mesh)
            tracer = simulate_longitudinal_tracer(scenario, mesh, fields)
            metrics = compute_longitudinal_metrics(scenario, mesh, fields, tracer)
            profiles.append(
                {
                    "headloss": metrics.transition_headloss_m,
                    "vui": metrics.post_transition_velocity_uniformity_index,
                    "launder_peak": metrics.launder_peak_upward_velocity_m_s,
                    "t10": metrics.t10_s,
                    "t50": metrics.t50_s,
                    "t90": metrics.t90_s,
                    "sci": metrics.short_circuiting_index,
                }
            )

        return profiles

    def test_headloss_uniformity_and_rtd_metrics_stay_within_loose_mesh_bands(self) -> None:
        # The current v0.2 geometry is numerically weak, so this smoke check uses
        # broad bounds and looks for directional stability rather than publication-
        # grade grid independence.
        for label, profiles in (("design", self.design_profiles), ("current", self.current_profiles)):
            with self.subTest(case=label, metric="headloss"):
                self.assertLess(self._relative_range(profiles, "headloss"), 0.15)

            with self.subTest(case=label, metric="vui"):
                self.assertLess(self._relative_range(profiles, "vui"), 0.01)

            with self.subTest(case=label, metric="t10"):
                self.assertLess(self._relative_range(profiles, "t10"), 0.15)

            with self.subTest(case=label, metric="t50"):
                self.assertLess(self._relative_range(profiles, "t50"), 0.10)

            with self.subTest(case=label, metric="t90"):
                self.assertLess(self._relative_range(profiles, "t90"), 0.10)

            with self.subTest(case=label, metric="sci"):
                self.assertLess(self._relative_range(profiles, "sci"), 0.15)

    def test_current_case_keeps_higher_headloss_and_launder_peak_than_design_across_meshes(self) -> None:
        for design_profile, current_profile, mesh in zip(self.design_profiles, self.current_profiles, MESH_LEVELS):
            with self.subTest(mesh=mesh, metric="headloss"):
                self.assertGreater(current_profile["headloss"], design_profile["headloss"])

            with self.subTest(mesh=mesh, metric="launder_peak"):
                self.assertGreater(current_profile["launder_peak"], design_profile["launder_peak"])

    @staticmethod
    def _relative_range(profiles: list[dict[str, float]], key: str) -> float:
        values = [profile[key] for profile in profiles]
        denominator = max(max(abs(value) for value in values), 1.0e-12)
        return (max(values) - min(values)) / denominator


if __name__ == "__main__":
    unittest.main()
