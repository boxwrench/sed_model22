import io
import json
import shutil
import sys
from pathlib import Path
import unittest
from contextlib import redirect_stdout
from uuid import uuid4

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sed_model22.cli import main  # noqa: E402


STUDY_PATH = ROOT / "scenarios" / "studies" / "svwtp_design_vs_current.yaml"


class StudyTests(unittest.TestCase):
    def test_validate_study_command(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["validate-study", str(STUDY_PATH)])

        self.assertEqual(exit_code, 0)
        self.assertIn("Validated study 'svwtp_design_vs_current'", stdout.getvalue())

    def test_compare_study_writes_outputs(self) -> None:
        temp_dir = ROOT / f"_study_test_tmp_{uuid4().hex}"
        try:
            temp_dir.mkdir(parents=True, exist_ok=False)
            run_root = temp_dir / "runs"
            study_payload = yaml.safe_load(STUDY_PATH.read_text(encoding="utf-8"))
            for case in study_payload["cases"]:
                case["scenario_path"] = str((ROOT / case["scenario_path"]).resolve())
            study_payload["outputs"]["run_root"] = str(run_root)
            temp_study_path = temp_dir / "study.yaml"
            temp_study_path.write_text(yaml.safe_dump(study_payload, sort_keys=False), encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["compare-study", str(temp_study_path)])

            self.assertEqual(exit_code, 0)
            self.assertIn("Created comparison study", stdout.getvalue())

            study_dirs = list(run_root.iterdir())
            self.assertEqual(len(study_dirs), 1)
            study_dir = study_dirs[0]

            summary_path = study_dir / "comparison_summary.json"
            csv_path = study_dir / "comparison_summary.csv"
            report_path = study_dir / "comparison_report.md"
            self.assertTrue(summary_path.exists())
            self.assertTrue(csv_path.exists())
            self.assertTrue(report_path.exists())

            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["study_id"], "svwtp_design_vs_current")
            self.assertEqual(len(summary["rows"]), 6)
            self.assertEqual(
                {row["case_label"] for row in summary["rows"]},
                {"design_spec", "current_blocked"},
            )

            manifest_paths = list((study_dir / "runs").rglob("manifest.json"))
            self.assertEqual(len(manifest_paths), 6)

            report_text = report_path.read_text(encoding="utf-8")
            self.assertIn("current_blocked - design_spec", report_text)
            self.assertIn("Transition headloss", report_text)
            self.assertIn("RTD proxy breakthrough", report_text)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
