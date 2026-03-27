from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from ..config import LongitudinalScenarioConfig


class LongitudinalMeshSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nx: int
    nz: int
    dx_m: float
    dz_m: float
    cell_count: int


def build_longitudinal_mesh(scenario: LongitudinalScenarioConfig) -> LongitudinalMeshSummary:
    dx_m = scenario.geometry.basin_length_m / scenario.numerics.nx
    dz_m = scenario.geometry.water_depth_m / scenario.numerics.nz

    return LongitudinalMeshSummary(
        nx=scenario.numerics.nx,
        nz=scenario.numerics.nz,
        dx_m=dx_m,
        dz_m=dz_m,
        cell_count=scenario.numerics.nx * scenario.numerics.nz,
    )
