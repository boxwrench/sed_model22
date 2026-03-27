import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sed_model22.config import load_scenario  # noqa: E402
from sed_model22.mesh import build_longitudinal_mesh  # noqa: E402


SCENARIO_PATH = ROOT / "scenarios" / "svwtp_design_spec_basin.yaml"


class LongitudinalMeshTests(unittest.TestCase):
    def test_longitudinal_mesh_summary(self) -> None:
        scenario = load_scenario(SCENARIO_PATH)
        mesh = build_longitudinal_mesh(scenario)

        self.assertEqual(mesh.nx, 72)
        self.assertEqual(mesh.nz, 24)
        self.assertEqual(mesh.cell_count, 72 * 24)
        self.assertAlmostEqual(mesh.dx_m, 103.63 / 72.0)
        self.assertAlmostEqual(mesh.dz_m, 3.35 / 24.0)


if __name__ == "__main__":
    unittest.main()
