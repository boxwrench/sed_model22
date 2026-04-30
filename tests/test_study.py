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
            self.assertIn("Media:", stdout.getvalue())

            study_dirs = list(run_root.iterdir())
            self.assertEqual(len(study_dirs), 1)
            study_dir = study_dirs[0]

            summary_path = study_dir / "comparison_summary.json"
            csv_path = study_dir / "comparison_summary.csv"
            report_path = study_dir / "comparison_report.md"
            media_root = study_dir / "media"
            media_manifest_path = media_root / "manifest.json"
            self.assertTrue(summary_path.exists())
            self.assertTrue(csv_path.exists())
            self.assertTrue(report_path.exists())
            self.assertTrue(media_manifest_path.exists())

            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["study_id"], "svwtp_design_vs_current")
            self.assertEqual(len(summary["rows"]), 6)
            self.assertEqual(
                {row["case_label"] for row in summary["rows"]},
                {"design_spec", "current_blocked"},
            )

            run_manifest_paths = [
                path for path in (study_dir / "runs").rglob("manifest.json") if path.parent.name != "media"
            ]
            media_manifest_paths = [
                path for path in (study_dir / "runs").rglob("manifest.json") if path.parent.name == "media"
            ]
            self.assertEqual(len(run_manifest_paths), 6)
            self.assertEqual(len(media_manifest_paths), 0)

            media_manifest = json.loads(media_manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(3, len(media_manifest["flow_media"]))
            low_media = media_root / "low"
            self.assertTrue((low_media / "manifest.json").exists())
            self.assertTrue((low_media / "visual_scene.json").exists())
            self.assertTrue((low_media / "preview" / "manifest.json").exists())
            self.assertTrue((low_media / "svwtp-design-vs-current-low.html").exists())

            report_text = report_path.read_text(encoding="utf-8")
            self.assertIn("current_blocked - design_spec", report_text)
            self.assertIn("Transition headloss", report_text)
            self.assertIn("RTD proxy timing shifts", report_text)
            self.assertIn("Model Limitations", report_text)
            self.assertIn("Provisional explicit bypass-opening features", report_text)
            self.assertIn("Screening cautions:", report_text)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_compare_study_report_uses_generic_case_labels(self) -> None:
        temp_dir = ROOT / f"_study_test_tmp_{uuid4().hex}"
        try:
            temp_dir.mkdir(parents=True, exist_ok=False)
            run_root = temp_dir / "runs"
            study_payload = yaml.safe_load(STUDY_PATH.read_text(encoding="utf-8"))
            study_payload["cases"][0]["label"] = "design_case"
            study_payload["cases"][1]["label"] = "blocked_case"
            for case in study_payload["cases"]:
                case["scenario_path"] = str((ROOT / case["scenario_path"]).resolve())
            study_payload["outputs"]["run_root"] = str(run_root)
            temp_study_path = temp_dir / "study.yaml"
            temp_study_path.write_text(yaml.safe_dump(study_payload, sort_keys=False), encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["compare-study", str(temp_study_path)])

            self.assertEqual(exit_code, 0)

            study_dir = next(run_root.iterdir())
            report_path = study_dir / "comparison_report.md"
            report_text = report_path.read_text(encoding="utf-8")
            media_html = (study_dir / "media" / "low" / "svwtp-design-vs-current-low.html").read_text(encoding="utf-8")

            self.assertIn("blocked_case - design_case", report_text)
            self.assertIn("| Metric | design_case | blocked_case | delta (blocked_case - design_case) |", report_text)
            self.assertIn("relative to `design_case`", report_text)
            self.assertIn("t10", report_text)
            self.assertIn("t50", report_text)
            self.assertIn("t90", report_text)
            self.assertIn("Screening cautions:", report_text)
            self.assertNotIn("No comparison pairs were found", report_text)
            self.assertIn("Executive Takeaways", media_html)
            self.assertIn("transition-wall impact", media_html)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
