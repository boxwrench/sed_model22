import io
import sys
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sed_model22.cli import main  # noqa: E402


SCENARIO_PATH = ROOT / "scenarios" / "baseline_rectangular_basin.yaml"


class CliTests(unittest.TestCase):
    def test_validate_command(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["validate", str(SCENARIO_PATH)])

        self.assertEqual(exit_code, 0)
        self.assertIn("Validated scenario 'baseline_rectangular_basin'", stdout.getvalue())

    def test_run_hydraulics_creates_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_root = Path(tmpdir) / "runs"
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
            self.assertTrue((run_dir / "plots" / "basin_layout.svg").exists())
            self.assertTrue((run_dir / "plots" / "velocity_magnitude.svg").exists())

    def test_summarize_command_reads_run_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_root = Path(tmpdir) / "runs"
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


if __name__ == "__main__":
    unittest.main()
