import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sed_model22.media.ffmpeg import resolve_ffmpeg_path  # noqa: E402
from sed_model22.media.guardrails import RenderBudget, check_render_safety  # noqa: E402
from sed_model22.media.pathlines import materialize_plan_view_pathline_preview  # noqa: E402
from sed_model22.media.render_preview import materialize_preview  # noqa: E402
from sed_model22.media.render_still import render_media_template  # noqa: E402
from sed_model22.config import load_scenario  # noqa: E402
from sed_model22.mesh import build_structured_mesh  # noqa: E402
from sed_model22.metrics import compute_scenario_metrics  # noqa: E402
from sed_model22.solver import solve_steady_screening_flow  # noqa: E402
from sed_model22.viz import build_plan_view_streamline_svg  # noqa: E402


class MediaPipelineTests(unittest.TestCase):
    def test_plan_view_pathline_preview_writes_manifest_and_poster(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            scenario = load_scenario(ROOT / "scenarios" / "baseline_rectangular_basin.yaml")
            scenario = scenario.model_copy(
                update={
                    "numerics": scenario.numerics.model_copy(
                        update={"nx": 20, "ny": 12, "max_iterations": 600}
                    )
                }
            )
            mesh = build_structured_mesh(scenario)
            metrics = compute_scenario_metrics(scenario)
            _summary, fields = solve_steady_screening_flow(scenario, mesh, metrics)

            artifacts = materialize_plan_view_pathline_preview(
                scenario=scenario,
                fields=fields,
                media_dir=Path(temp_dir),
                frame_count=24,
                particle_count=32,
            )

            self.assertTrue(Path(artifacts.manifest_path).exists())
            self.assertTrue(Path(artifacts.poster_path).exists())
            manifest = json.loads(Path(artifacts.manifest_path).read_text(encoding="utf-8"))
            self.assertEqual("plan_view_pathline_preview_v1", manifest["type"])
            self.assertIn("steady screening field", " ".join(manifest["notes"]))

    def test_render_media_template_writes_stills_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            template_path = temp_root / "template.yaml"
            template_path.write_text(
                yaml.safe_dump(
                    {
                        "template_id": "test_v0_2_pair",
                        "title": "Test v0.2 Pair",
                        "subtitle": "Template smoke test",
                        "narrative": "Leadership-facing comparison smoke test.",
                        "focus_points": ["headloss shift", "launder proxy"],
                        "cases": [
                            {
                                "label": "design_spec",
                                "scenario_path": str(ROOT / "scenarios" / "svwtp_design_spec_basin.yaml"),
                                "numerics_override": {"nx": 20, "nz": 10, "max_iterations": 500},
                            },
                            {
                                "label": "current_blocked",
                                "scenario_path": str(ROOT / "scenarios" / "svwtp_current_blocked_wall_basin.yaml"),
                                "numerics_override": {"nx": 20, "nz": 10, "max_iterations": 500},
                            },
                        ],
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            artifacts = render_media_template(template_path, output_root=temp_root / "output")

            self.assertEqual(2, len(artifacts.cases))
            self.assertTrue((temp_root / "output" / "manifest.json").exists())
            self.assertTrue((temp_root / "output" / "visual_scene.json").exists())
            self.assertTrue((temp_root / "output" / "01_design-spec_voxel_isometric.svg").exists())
            self.assertTrue((temp_root / "output" / "02_current-blocked_voxel_isometric.svg").exists())
            self.assertIsNotNone(artifacts.comparison_html_path)
            self.assertTrue(Path(artifacts.comparison_html_path).exists())

            manifest = json.loads((temp_root / "output" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual("test_v0_2_pair", manifest["template_id"])
            self.assertIn("comparison_lines", manifest)
            scene = json.loads((temp_root / "output" / "visual_scene.json").read_text(encoding="utf-8"))
            self.assertEqual("comparison_voxel_scene", scene["scene_type"])
            self.assertIn("headloss shift", scene["focus_points"])
            self.assertEqual(2, len(scene["cases"]))

            comparison_html = Path(artifacts.comparison_html_path).read_text(encoding="utf-8")
            self.assertIn("Executive Takeaways", comparison_html)
            self.assertIn("Leadership-facing comparison smoke test.", comparison_html)

    def test_materialize_preview_writes_cards_and_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            template_path = temp_root / "template.yaml"
            template_path.write_text(
                yaml.safe_dump(
                    {
                        "template_id": "test_v0_1_pair",
                        "title": "Test v0.1 Pair",
                        "cases": [
                            {
                                "label": "verification_empty",
                                "scenario_path": str(ROOT / "scenarios" / "verification_empty_basin.yaml"),
                                "numerics_override": {"nx": 18, "ny": 10, "max_iterations": 600},
                            },
                            {
                                "label": "baseline_baffle",
                                "scenario_path": str(ROOT / "scenarios" / "baseline_rectangular_basin.yaml"),
                                "numerics_override": {"nx": 18, "ny": 10, "max_iterations": 600},
                            },
                        ],
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            artifacts = materialize_preview(template_path, output_root=temp_root / "output")

            self.assertTrue(Path(artifacts.title_card_path).exists())
            self.assertTrue(Path(artifacts.metrics_card_path).exists())
            self.assertTrue(Path(artifacts.warnings_card_path).exists())
            self.assertTrue(Path(artifacts.poster_path).exists())
            self.assertTrue(Path(artifacts.scene_sequence_path).exists())
            self.assertIsNotNone(artifacts.scene_manifest_path)
            self.assertTrue(Path(artifacts.scene_manifest_path).exists())
            if artifacts.preview_video_path is not None:
                self.assertTrue(Path(artifacts.preview_video_path).exists())

    def test_resolve_ffmpeg_path_uses_env_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_ffmpeg = Path(temp_dir) / "ffmpeg.exe"
            fake_ffmpeg.write_text("", encoding="utf-8")
            prior = os.environ.get("SED_MODEL22_FFMPEG")
            os.environ["SED_MODEL22_FFMPEG"] = str(fake_ffmpeg)
            try:
                self.assertEqual(str(fake_ffmpeg), resolve_ffmpeg_path())
            finally:
                if prior is None:
                    os.environ.pop("SED_MODEL22_FFMPEG", None)
                else:
                    os.environ["SED_MODEL22_FFMPEG"] = prior

    def test_render_guardrails_reject_overlarge_preview(self) -> None:
        safe, estimate, recommendation = check_render_safety(
            RenderBudget(width=1920, height=1080, frame_count=400, max_wall_time_s=60.0)
        )
        self.assertFalse(safe)
        self.assertGreater(estimate, 0.0)
        self.assertIn("Reduce", recommendation)

    def test_plan_view_streamline_svg_carries_screening_language(self) -> None:
        scenario = load_scenario(ROOT / "scenarios" / "baseline_rectangular_basin.yaml")
        scenario = scenario.model_copy(
            update={
                "numerics": scenario.numerics.model_copy(
                    update={"nx": 20, "ny": 12, "max_iterations": 600}
                )
            }
        )
        mesh = build_structured_mesh(scenario)
        metrics = compute_scenario_metrics(scenario)
        _summary, fields = solve_steady_screening_flow(scenario, mesh, metrics)

        svg = build_plan_view_streamline_svg(scenario, fields)

        self.assertIn("<svg", svg)
        self.assertIn("Deterministic streamlines from steady screening field", svg)
        self.assertIn("Not transient CFD", svg)

    def test_preview_skipped_when_ffmpeg_missing(self) -> None:
        """Verify preview generation is skipped gracefully when ffmpeg is unavailable."""
        import subprocess

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            template_path = temp_root / "template.yaml"
            template_path.write_text(
                yaml.safe_dump(
                    {
                        "template_id": "test_missing_ffmpeg",
                        "title": "Test Missing FFmpeg",
                        "cases": [
                            {
                                "label": "empty",
                                "scenario_path": str(ROOT / "scenarios" / "verification_empty_basin.yaml"),
                                "numerics_override": {"nx": 12, "ny": 8, "max_iterations": 200},
                            },
                        ],
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            # Set a non-existent ffmpeg path to simulate missing binary
            prior = os.environ.get("SED_MODEL22_FFMPEG")
            os.environ["SED_MODEL22_FFMPEG"] = str(temp_root / "nonexistent_ffmpeg.exe")
            try:
                artifacts = materialize_preview(template_path, output_root=temp_root / "output")

                # Should still produce stills even if video fails
                self.assertTrue(Path(artifacts.title_card_path).exists())
                self.assertTrue(Path(artifacts.poster_path).exists())
                # Video may be None when ffmpeg fails
            finally:
                if prior is None:
                    os.environ.pop("SED_MODEL22_FFMPEG", None)
                else:
                    os.environ["SED_MODEL22_FFMPEG"] = prior


if __name__ == "__main__":
    unittest.main()
