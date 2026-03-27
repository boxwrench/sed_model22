import sys
from pathlib import Path
import unittest

from pydantic import ValidationError


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sed_model22.config import PlanViewScenarioConfig, load_scenario  # noqa: E402


SCENARIO_PATH = ROOT / "scenarios" / "baseline_rectangular_basin.yaml"


class ScenarioConfigTests(unittest.TestCase):
    def test_baseline_scenario_validates(self) -> None:
        scenario = load_scenario(SCENARIO_PATH)
        self.assertEqual(scenario.metadata.case_id, "baseline_rectangular_basin")
        self.assertEqual(len(scenario.baffles), 2)
        self.assertEqual(scenario.numerics.nx, 80)
        self.assertEqual(scenario.inlet.side, "west")
        self.assertEqual(scenario.outlet.side, "east")

    def test_invalid_opening_span_fails_validation(self) -> None:
        invalid_payload = {
            "metadata": {"case_id": "bad-case", "title": "Bad Case"},
            "geometry": {
                "length_m": 10.0,
                "width_m": 5.0,
                "water_depth_m": 2.0,
            },
            "hydraulics": {"flow_rate_m3_s": 0.2},
            "inlet": {"side": "west", "center_m": 1.0, "span_m": 4.0},
            "outlet": {"side": "east", "center_m": 2.5, "span_m": 2.0},
            "baffles": [],
        }

        with self.assertRaises(ValidationError):
            PlanViewScenarioConfig.model_validate(invalid_payload)

    def test_non_opposite_inlet_and_outlet_fail_validation(self) -> None:
        invalid_payload = {
            "metadata": {"case_id": "bad-pair", "title": "Bad Pair"},
            "geometry": {
                "length_m": 20.0,
                "width_m": 8.0,
                "water_depth_m": 3.0,
            },
            "hydraulics": {"flow_rate_m3_s": 0.2},
            "inlet": {"side": "west", "center_m": 4.0, "span_m": 2.0},
            "outlet": {"side": "north", "center_m": 10.0, "span_m": 4.0},
            "baffles": [],
        }

        with self.assertRaises(ValidationError):
            PlanViewScenarioConfig.model_validate(invalid_payload)


if __name__ == "__main__":
    unittest.main()
