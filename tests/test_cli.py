import io
import shutil
import sys
from pathlib import Path
import unittest
from contextlib import redirect_stdout
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sed_model22.cli import main  # noqa: E402


SCENARIO_PATH = ROOT / "scenarios" / "baseline_rectangular_basin.yaml"
LONGITUDINAL_SCENARIO_PATH = ROOT / "scenarios" / "svwtp_design_spec_basin.yaml"


class CliTests(unittest.TestCase):
    def _scratch_dir(self) -> Path:
        path = ROOT / f"_cli_test_tmp_{uuid4().hex}"
        path.mkdir(parents=True, exist_ok=False)
        return path

    def test_validate_command(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["validate", str(SCENARIO_PATH)])

        self.assertEqual(exit_code, 0)
        self.assertIn("Validated scenario 'baseline_rectangular_basin'", stdout.getvalue())

    def test_run_hydraulics_creates_artifacts(self) -> None:
        scratch = self._scratch_dir()
        run_dir: Path | None = None
        try:
            run_root = scratch / "runs"
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "run-hydraulics",
                        str(SCENARIO_PATH),
                        "--run-root",
                        str(run_root),
                    ]
                )

            self.assertEqual(exit_code, 0)
            created_runs = list(run_root.iterdir())
            self.assertEqual(len(created_runs), 1)

            run_dir = created_runs[0]
            self.assertTrue((run_dir / "manifest.json").exists())
            self.assertTrue((run_dir / "summary.json").exists())
            self.assertTrue((run_dir / "mesh.json").exists())
            self.assertTrue((run_dir / "metrics.json").exists())
            self.assertTrue((run_dir / "fields.json").exists())
            self.assertTrue((run_dir / "operator_report.html").exists())
            self.assertTrue((run_dir / "media" / "voxel_isometric.svg").exists())
            self.assertTrue((run_dir / "media" / "manifest.json").exists())
            self.assertTrue((run_dir / "plots" / "basin_layout.svg").exists())
            self.assertTrue((run_dir / "plots" / "velocity_magnitude.svg").exists())
            self.assertTrue((run_dir / "plots" / "streamlines.svg").exists())
            report_html = (run_dir / "operator_report.html").read_text(encoding="utf-8")
            self.assertIn("Technical basis:", report_html)
            self.assertIn("slow-moving", report_html)
            self.assertIn("Engineering detail", report_html)
            self.assertIn("Scope and limits", report_html)
            self.assertIn("Technical appendix", report_html)
            self.assertIn("Scenario summary", report_html)
            self.assertIn("Hydraulic metrics", report_html)
            self.assertIn("Boundary conditions", report_html)
            self.assertIn("Baffles", report_html)
            output = stdout.getvalue()
            self.assertIn("Voxel still:", output)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)

    def test_summarize_command_reads_run_artifacts(self) -> None:
        scratch = self._scratch_dir()
        try:
            run_root = scratch / "runs"
            run_exit_code = main(
                [
                    "run-hydraulics",
                    str(SCENARIO_PATH),
                    "--run-root",
                    str(run_root),
                ]
            )
            self.assertEqual(run_exit_code, 0)

            run_dir = next(run_root.iterdir())
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["summarize", str(run_dir)])

            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("Detention time:", output)
            self.assertIn("Mass balance error:", output)
            self.assertIn("Operator report:", output)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)

    def test_longitudinal_run_and_summarize_use_rtd_proxy_language(self) -> None:
        scratch = self._scratch_dir()
        try:
            run_root = scratch / "runs"
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "run-hydraulics",
                        str(LONGITUDINAL_SCENARIO_PATH),
                        "--run-root",
                        str(run_root),
                    ]
                )

            self.assertEqual(exit_code, 0)
            run_dir = next(run_root.iterdir())
            self.assertTrue((run_dir / "tracer.json").exists())
            self.assertTrue((run_dir / "plots" / "tracer_breakthrough.svg").exists())
            self.assertTrue((run_dir / "media" / "voxel_isometric.svg").exists())
            self.assertTrue((run_dir / "media" / "manifest.json").exists())

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["summarize", str(run_dir)])

            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("RTD proxy model:", output)
            self.assertIn("RTD proxy breakthrough:", output)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
