from __future__ import annotations

from pydantic import BaseModel

from ..config import ScenarioConfig


class MeshSummary(BaseModel):
    nx: int
    ny: int
    dx_m: float
    dy_m: float
    cell_count: int


def build_structured_mesh(scenario: ScenarioConfig) -> MeshSummary:
    dx_m = scenario.geometry.length_m / scenario.numerics.nx
    dy_m = scenario.geometry.width_m / scenario.numerics.ny

    return MeshSummary(
        nx=scenario.numerics.nx,
        ny=scenario.numerics.ny,
        dx_m=dx_m,
        dy_m=dy_m,
        cell_count=scenario.numerics.nx * scenario.numerics.ny,
    )
