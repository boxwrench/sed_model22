from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass

from .ffmpeg import resolve_ffmpeg_path


PORTABLE_ENCODER_ORDER = (
    "h264_qsv",
    "h264_nvenc",
    "h264_amf",
    "h264_videotoolbox",
    "libx264",
)


@dataclass(frozen=True)
class RenderRuntime:
    profile: str
    ffmpeg_path: str
    encoder: str
    workers: int
    video_args: tuple[str, ...]


def detect_render_runtime(
    ffmpeg_path: str | None = None,
    workers: int | None = None,
) -> RenderRuntime:
    resolved_ffmpeg = resolve_ffmpeg_path(ffmpeg_path)
    if not resolved_ffmpeg:
        raise FileNotFoundError("ffmpeg was not found")

    profile = _detect_profile()
    encoder = _pick_encoder(resolved_ffmpeg, profile)
    chosen_workers = max(1, workers) if workers is not None else _conservative_worker_limit(profile)
    return RenderRuntime(
        profile=profile,
        ffmpeg_path=resolved_ffmpeg,
        encoder=encoder,
        workers=chosen_workers,
        video_args=tuple(_encoder_args(encoder)),
    )


def encoder_smoke_test(
    ffmpeg_path: str,
    encoder: str,
    *,
    width: int = 320,
    height: int = 180,
    fps: int = 15,
    seconds: float = 0.25,
) -> bool:
    command = [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        f"testsrc2=size={width}x{height}:rate={fps}",
        "-t",
        str(seconds),
        "-c:v",
        encoder,
        "-f",
        "null",
        "-",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    return result.returncode == 0


def smoke_test_workers(workers: int) -> bool:
    worker_count = max(1, int(workers))
    return worker_count <= 1


def _pick_encoder(ffmpeg_path: str, profile: str) -> str:
    if profile == "INTEL_QSV":
        order = ("h264_qsv", "libx264")
    elif profile == "NVIDIA_NVENC":
        order = ("h264_nvenc", "libx264")
    elif profile == "AMD_AMF":
        order = ("h264_amf", "libx264")
    elif profile == "APPLE_SILICON":
        order = ("h264_videotoolbox", "libx264")
    else:
        order = PORTABLE_ENCODER_ORDER

    for encoder in order:
        if encoder_smoke_test(ffmpeg_path, encoder):
            return encoder
    return "libx264"


def _detect_profile() -> str:
    system = platform.system()
    if system == "Darwin" and platform.machine() == "arm64":
        return "APPLE_SILICON"
    if system == "Windows":
        vendor = _detect_windows_gpu_vendor()
        if vendor == "intel":
            return "INTEL_QSV"
        if vendor == "nvidia":
            return "NVIDIA_NVENC"
        if vendor == "amd":
            return "AMD_AMF"
    return "SAFE_MODE"


def _detect_windows_gpu_vendor() -> str | None:
    powershell = shutil.which("powershell")
    if not powershell:
        return None
    result = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-Command",
            "(Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name) -join \"`n\"",
        ],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    if result.returncode != 0:
        return None
    names = result.stdout.lower()
    if "intel" in names:
        return "intel"
    if "nvidia" in names:
        return "nvidia"
    if "amd" in names or "radeon" in names:
        return "amd"
    return None


def _conservative_worker_limit(profile: str) -> int:
    override = os.environ.get("SED_MODEL22_RENDER_WORKERS")
    if override:
        try:
            return max(1, int(override))
        except ValueError:
            pass
    logical = max(1, os.cpu_count() or 1)
    if profile == "SAFE_MODE":
        return 1
    return max(1, min(4, logical - 2))


def _encoder_args(encoder: str) -> list[str]:
    if encoder == "h264_nvenc":
        return ["-c:v", encoder, "-preset", "p5", "-cq", "24", "-b:v", "0"]
    if encoder == "h264_qsv":
        return ["-c:v", encoder, "-preset", "veryfast", "-global_quality", "24"]
    if encoder == "h264_amf":
        return ["-c:v", encoder, "-quality", "balanced", "-qp_i", "24", "-qp_p", "26"]
    if encoder == "h264_videotoolbox":
        return ["-c:v", encoder, "-b:v", "2M"]
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "24"]
