from __future__ import annotations

from pathlib import Path
import shutil


def rasterize_scene_sequence(
    scene_sequence: list[dict[str, object]],
    frames_root: Path,
) -> list[tuple[Path, float]]:
    frames_root.mkdir(parents=True, exist_ok=True)
    rasterized: list[tuple[Path, float]] = []
    for index, scene in enumerate(scene_sequence, start=1):
        source_path = Path(str(scene["path"]))
        duration_s = float(scene["duration_s"])
        raster_path = _rasterize_scene(source_path, frames_root / f"{index:02d}_{source_path.stem}.png")
        if raster_path is None:
            return []
        rasterized.append((raster_path, duration_s))
    return rasterized


def _rasterize_scene(source_path: Path, output_path: Path) -> Path | None:
    if source_path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
        shutil.copyfile(source_path, output_path)
        return output_path
    if source_path.suffix.lower() != ".svg":
        return None
    try:
        import cairosvg  # type: ignore

        cairosvg.svg2png(url=str(source_path), write_to=str(output_path))
        return output_path
    except Exception:
        return None
