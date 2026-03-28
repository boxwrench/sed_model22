from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class RenderedCaseArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    scenario_path: str
    model_form: str
    still_path: str
    highlighted_metrics: dict[str, object] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class StillRenderArtifacts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    template_id: str
    title: str
    output_root: str
    comparison_html_path: str | None = None
    manifest_path: str
    cases: list[RenderedCaseArtifact]
    comparison_lines: list[str] = Field(default_factory=list)
    warning_lines: list[str] = Field(default_factory=list)


class PreviewArtifacts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    template_id: str
    preview_root: str
    manifest_path: str
    title_card_path: str
    metrics_card_path: str
    warnings_card_path: str
    poster_path: str
    scene_sequence_path: str
    preview_video_path: str | None = None
    ffmpeg_path: str | None = None


def write_manifest(path: str | Path, payload: BaseModel | dict) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, BaseModel):
        body = payload.model_dump(mode="json")
    else:
        body = payload
    destination.write_text(json.dumps(body, indent=2, sort_keys=True), encoding="utf-8")
    return destination
