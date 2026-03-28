from __future__ import annotations

import json
from pathlib import Path
import shutil

from .ffmpeg import resolve_ffmpeg_path, write_slideshow_preview
from .manifest import PreviewArtifacts, write_manifest
from .rasterize import rasterize_scene_sequence
from .render_still import MediaTemplate, load_media_template, render_media_template
from .scenes import write_metrics_card, write_title_card, write_warnings_card


def materialize_preview(
    template_or_path: MediaTemplate | str | Path,
    *,
    output_root: str | Path | None = None,
    ffmpeg_path: str | None = None,
    fps: int = 12,
) -> PreviewArtifacts:
    template_path: Path | None = None
    if isinstance(template_or_path, MediaTemplate):
        template = template_or_path
    else:
        template_path = Path(template_or_path).resolve()
        template = load_media_template(template_path)

    still_artifacts = render_media_template(template_path or template, output_root=output_root)
    preview_root = Path(still_artifacts.output_root) / "preview"
    preview_root.mkdir(parents=True, exist_ok=True)

    title_card_path = write_title_card(
        preview_root / "title_card.svg",
        title=template.title,
        subtitle=template.subtitle or "Template-driven basin comparison preview",
        template_id=template.template_id,
    )
    metrics_card_path = write_metrics_card(
        preview_root / "metrics_card.svg",
        title=template.title,
        lines=still_artifacts.comparison_lines[:6] or ["Comparison metrics will be populated once case stills are available."],
    )
    warnings_card_path = write_warnings_card(
        preview_root / "warnings_card.svg",
        title=template.title,
        lines=still_artifacts.warning_lines[:6] or ["This output remains a screening visualization and does not imply a 3D solve."],
    )

    poster_source = Path(still_artifacts.cases[0].still_path)
    poster_path = preview_root / "poster.svg"
    shutil.copyfile(poster_source, poster_path)

    scene_sequence = [
        {"path": str(title_card_path), "duration_s": 2.0},
        *[
            {"path": artifact.still_path, "duration_s": 2.2}
            for artifact in still_artifacts.cases[:2]
        ],
        {"path": str(metrics_card_path), "duration_s": 2.4},
        {"path": str(warnings_card_path), "duration_s": 2.4},
        {"path": str(poster_path), "duration_s": 1.6},
    ]
    scene_sequence_path = preview_root / "scene_sequence.json"
    scene_sequence_path.write_text(json.dumps(scene_sequence, indent=2), encoding="utf-8")

    resolved_ffmpeg_path = resolve_ffmpeg_path(ffmpeg_path)
    preview_video_path: Path | None = None
    rasterized_scenes = rasterize_scene_sequence(scene_sequence, preview_root / "frames")
    if resolved_ffmpeg_path and len(rasterized_scenes) == len(scene_sequence):
        preview_video_path = write_slideshow_preview(
            ffmpeg_path=resolved_ffmpeg_path,
            fps=fps,
            scenes=[(str(path), duration_s) for path, duration_s in rasterized_scenes],
            output_path=preview_root / "preview.mp4",
        )

    manifest_path = preview_root / "manifest.json"
    artifacts = PreviewArtifacts(
        template_id=template.template_id,
        preview_root=str(preview_root),
        manifest_path=str(manifest_path),
        title_card_path=str(title_card_path),
        metrics_card_path=str(metrics_card_path),
        warnings_card_path=str(warnings_card_path),
        poster_path=str(poster_path),
        scene_sequence_path=str(scene_sequence_path),
        preview_video_path=str(preview_video_path) if preview_video_path else None,
        ffmpeg_path=resolved_ffmpeg_path,
    )
    write_manifest(manifest_path, artifacts)
    return artifacts
