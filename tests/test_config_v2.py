import sys
from pathlib import Path
import unittest

from pydantic import ValidationError


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sed_model22.config import (  # noqa: E402
    ComparisonStudyConfig,
    LongitudinalScenarioConfig,
    PlanViewScenarioConfig,
    load_scenario,
    load_study,
)


BASELINE_SCENARIO_PATH = ROOT / "scenarios" / "baseline_rectangular_basin.yaml"
LONGITUDINAL_SCENARIO_PATH = ROOT / "scenarios" / "svwtp_design_spec_basin.yaml"
STUDY_PATH = ROOT / "scenarios" / "studies" / "svwtp_design_vs_current.yaml"


class ConfigV2Tests(unittest.TestCase):
    def test_v0_1_baseline_still_validates(self) -> None:
        scenario = load_scenario(BASELINE_SCENARIO_PATH)
        self.assertIsInstance(scenario, PlanViewScenarioConfig)
        self.assertEqual(scenario.model_form, "plan_view_v0_1")
        self.assertEqual(scenario.metadata.case_id, "baseline_rectangular_basin")

    def test_v0_2_longitudinal_scenario_validates(self) -> None:
        scenario = load_scenario(LONGITUDINAL_SCENARIO_PATH)
        self.assertIsInstance(scenario, LongitudinalScenarioConfig)
        self.assertEqual(scenario.model_form, "longitudinal_v0_2")
        self.assertEqual(scenario.metadata.case_id, "svwtp_design_spec")
        self.assertEqual(len(scenario.features), 3)

    def test_v0_3_longitudinal_scenario_with_explicit_bypass_validates(self) -> None:
        baseline = load_scenario(LONGITUDINAL_SCENARIO_PATH)
        scenario_data = baseline.model_dump()
        scenario_data["metadata"]["stage"] = "v0.3"
        scenario_data["features"].append(
            {
                "kind": "explicit_bypass_path",
                "name": "transition_overflow_bypass",
                "path_type": "over",
                "x_start_m": 1.0,
                "x_end_m": 2.0,
                "z_bottom_m": 2.6,
                "z_top_m": baseline.geometry.water_depth_m,
                "open_area_fraction": 0.18,
                "loss_scale": 1.0,
                "geometry_confidence": "low",
                "notes": "Unverified placeholder used only for schema coverage.",
            }
        )

        scenario = LongitudinalScenarioConfig.model_validate(scenario_data)

        self.assertEqual("v0.3", scenario.metadata.stage)
        self.assertEqual("explicit_bypass_path", scenario.features[-1].kind)
        self.assertEqual("over", scenario.features[-1].path_type)

    def test_invalid_explicit_bypass_path_fails_validation(self) -> None:
        baseline = load_scenario(LONGITUDINAL_SCENARIO_PATH)
        scenario_data = baseline.model_dump()
        scenario_data["features"].append(
            {
                "kind": "explicit_bypass_path",
                "name": "bad_bypass",
                "path_type": "over",
                "x_start_m": 3.0,
                "x_end_m": 2.0,
                "z_bottom_m": 2.8,
                "z_top_m": 2.5,
                "open_area_fraction": 0.18,
                "loss_scale": 1.0,
                "geometry_confidence": "low",
            }
        )

        with self.assertRaises(ValidationError):
            LongitudinalScenarioConfig.model_validate(scenario_data)

    def test_study_file_validates(self) -> None:
        study = load_study(STUDY_PATH)
        self.assertIsInstance(study, ComparisonStudyConfig)
        self.assertEqual(study.study_id, "svwtp_design_vs_current")
        self.assertEqual(len(study.cases), 2)
        self.assertEqual(len(study.flows), 3)


if __name__ == "__main__":
    unittest.main()
