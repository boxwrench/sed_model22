import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sed_model22.config import load_scenario  # noqa: E402
from sed_model22.mesh import build_longitudinal_mesh, build_structured_mesh  # noqa: E402
from sed_model22.metrics import compute_scenario_metrics  # noqa: E402
from sed_model22.solver import solve_steady_screening_flow  # noqa: E402
from sed_model22.solver.longitudinal import solve_steady_longitudinal_screening_flow  # noqa: E402
from sed_model22.viz import (  # noqa: E402
    build_longitudinal_voxel_isometric_svg,
    build_plan_view_voxel_isometric_svg,
)


CURRENT_SCENARIO_PATH = ROOT / "scenarios" / "svwtp_current_blocked_wall_basin.yaml"
DESIGN_SCENARIO_PATH = ROOT / "scenarios" / "svwtp_design_spec_basin.yaml"
BASELINE_SCENARIO_PATH = ROOT / "scenarios" / "baseline_rectangular_basin.yaml"


class VoxelVisualizationTests(unittest.TestCase):
    def test_voxel_svg_carries_screening_labels(self) -> None:
        scenario = load_scenario(CURRENT_SCENARIO_PATH)
        scenario = scenario.model_copy(
            update={
                "numerics": scenario.numerics.model_copy(
                    update={"nx": 24, "nz": 12, "max_iterations": 600}
                )
            }
        )
        mesh = build_longitudinal_mesh(scenario)
        _summary, fields = solve_steady_longitudinal_screening_flow(scenario, mesh)

        svg = build_longitudinal_voxel_isometric_svg(scenario, fields)

        self.assertIn("<svg", svg)
        self.assertIn("Voxelized screening visualization", svg)
        self.assertIn("not a full 3D solve", svg)
        self.assertIn("Blocked transition wall", svg)
        self.assertIn("Plate settler proxy zone", svg)

    def test_design_case_uses_generic_transition_wall_label(self) -> None:
        scenario = load_scenario(DESIGN_SCENARIO_PATH)
        scenario = scenario.model_copy(
            update={
                "numerics": scenario.numerics.model_copy(
                    update={"nx": 24, "nz": 12, "max_iterations": 600}
                )
            }
        )
        mesh = build_longitudinal_mesh(scenario)
        _summary, fields = solve_steady_longitudinal_screening_flow(scenario, mesh)

        svg = build_longitudinal_voxel_isometric_svg(scenario, fields)

        self.assertIn("Transition wall", svg)
        self.assertNotIn("Blocked transition wall", svg)

    def test_plan_view_voxel_svg_renders_baffles(self) -> None:
        scenario = load_scenario(BASELINE_SCENARIO_PATH)
        scenario = scenario.model_copy(
            update={
                "numerics": scenario.numerics.model_copy(
                    update={"nx": 24, "ny": 12, "max_iterations": 800}
                )
            }
        )
        mesh = build_structured_mesh(scenario)
        metrics = compute_scenario_metrics(scenario)
        _summary, fields = solve_steady_screening_flow(scenario, mesh, metrics)

        svg = build_plan_view_voxel_isometric_svg(scenario, fields)

        self.assertIn("<svg", svg)
        self.assertIn("plan-view x-y field extruded through water depth", svg)
        self.assertIn("Solid gray prisms show full-depth solid baffles", svg)


if __name__ == "__main__":
    unittest.main()
