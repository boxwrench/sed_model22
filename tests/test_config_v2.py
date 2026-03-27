import sys
from pathlib import Path
import unittest


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

    def test_study_file_validates(self) -> None:
        study = load_study(STUDY_PATH)
        self.assertIsInstance(study, ComparisonStudyConfig)
        self.assertEqual(study.study_id, "svwtp_design_vs_current")
        self.assertEqual(len(study.cases), 2)
        self.assertEqual(len(study.flows), 3)


if __name__ == "__main__":
    unittest.main()
