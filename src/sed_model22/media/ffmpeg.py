from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def common_ffmpeg_paths() -> list[Path]:
    repo_root = _repo_root()
    return [
        repo_root / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe",
        repo_root / ".tools" / "ffmpeg" / "bin" / "ffmpeg.exe",
        repo_root / "ffmpeg" / "bin" / "ffmpeg.exe",
        Path(r"C:\pinokio\bin\miniconda\Library\bin\ffmpeg.exe"),
    ]


def resolve_ffmpeg_path(explicit_path: str | None = None) -> str | None:
    if explicit_path:
        candidate = Path(explicit_path)
        if candidate.exists():
            return str(candidate)

    env_path = os.environ.get("SED_MODEL22_FFMPEG")
    if env_path:
        candidate = Path(env_path)
        if candidate.exists():
            return str(candidate)

    path_candidate = shutil.which("ffmpeg")
    if path_candidate:
        return path_candidate

    for candidate in common_ffmpeg_paths():
        if candidate.exists():
            return str(candidate)

    try:
        import imageio_ffmpeg  # type: ignore

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def write_slideshow_preview(
    *,
    ffmpeg_path: str,
    fps: int,
    scenes: list[tuple[str, float]],
    output_path: str | Path,
) -> Path:
    if not scenes:
        raise ValueError("preview scene list must not be empty")

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    command: list[str] = [ffmpeg_path, "-y", "-hide_banner", "-loglevel", "error"]
    filter_inputs = []
    for index, (scene_path, duration_s) in enumerate(scenes):
        command.extend(
            [
                "-loop",
                "1",
                "-framerate",
                str(fps),
                "-t",
                f"{duration_s:.3f}",
                "-i",
                str(scene_path),
            ]
        )
        filter_inputs.append(f"[{index}:v]")

    command.extend(
        [
            "-filter_complex",
            "".join(filter_inputs) + f"concat=n={len(scenes)}:v=1:a=0[v]",
            "-map",
            "[v]",
            "-r",
            str(fps),
            "-pix_fmt",
            "yuv420p",
            str(destination),
        ]
    )

    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg slideshow render failed: {result.stderr.strip()}")
    return destination
