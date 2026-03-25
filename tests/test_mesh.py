import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sed_model22.config import load_scenario  # noqa: E402
from sed_model22.mesh import build_structured_mesh  # noqa: E402


SCENARIO_PATH = ROOT / "scenarios" / "baseline_rectangular_basin.yaml"


class StructuredMeshTests(unittest.TestCase):
    def test_structured_mesh_summary(self) -> None:
        scenario = load_scenario(SCENARIO_PATH)
        mesh = build_structured_mesh(scenario)

        self.assertEqual(mesh.cell_count, 80 * 24)
        self.assertAlmostEqual(mesh.dx_m, 1.25)
        self.assertAlmostEqual(mesh.dy_m, 1.25)


if __name__ == "__main__":
    unittest.main()
