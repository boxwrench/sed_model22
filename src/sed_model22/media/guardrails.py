from __future__ import annotations

import time
from dataclasses import dataclass


class RenderTimeoutError(RuntimeError):
    """Raised when preview rendering exceeds its safety budget."""


@dataclass(frozen=True)
class RenderBudget:
    width: int
    height: int
    frame_count: int
    complexity: float = 1.0
    max_wall_time_s: float = 180.0


def estimate_render_time_seconds(budget: RenderBudget) -> float:
    megapixels = (budget.width * budget.height) / 1_000_000.0
    return budget.frame_count * megapixels * 0.085 * max(0.5, budget.complexity)


def check_render_safety(budget: RenderBudget) -> tuple[bool, float, str]:
    estimate = estimate_render_time_seconds(budget)
    issues: list[str] = []
    if budget.frame_count <= 0:
        issues.append("frame_count must be positive")
    if budget.frame_count > 240:
        issues.append(f"frame_count ({budget.frame_count} > 240)")
    if budget.width * budget.height > 1280 * 720:
        issues.append("preview resolution exceeds 720p")
    if estimate > budget.max_wall_time_s:
        issues.append(f"estimated time ({estimate:.1f}s > {budget.max_wall_time_s:.1f}s budget)")
    if issues:
        return False, estimate, "Reduce " + ", ".join(issues)
    return True, estimate, "Parameters look good."


class RenderMonitor:
    def __init__(self, total_frames: int, timeout_seconds: float) -> None:
        self.total_frames = total_frames
        self.timeout_seconds = timeout_seconds
        self.start_time: float | None = None

    def start(self) -> None:
        self.start_time = time.time()

    def check_frame(self, frame_num: int) -> None:
        if self.start_time is None:
            self.start()
        elapsed = time.time() - self.start_time
        if elapsed > self.timeout_seconds:
            raise RenderTimeoutError(
                f"preview render timeout after {elapsed:.1f}s at frame {frame_num}/{self.total_frames}"
            )

    def progress_str(self, frame_num: int) -> str:
        if self.start_time is None:
            return "0% | 0.0s elapsed | ETA unavailable"
        elapsed = time.time() - self.start_time
        completed = max(1, frame_num + 1)
        avg = elapsed / completed
        eta = avg * max(0, self.total_frames - completed)
        pct = 100.0 * completed / max(1, self.total_frames)
        return f"{pct:.0f}% ({completed}/{self.total_frames}) | {elapsed:.1f}s elapsed | {eta:.1f}s ETA"
