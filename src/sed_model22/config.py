from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, model_validator


BoundarySide = Literal["west", "east", "south", "north"]
BaffleKind = Literal["full_depth_solid", "curtain_placeholder", "porous_placeholder"]

OPPOSITE_SIDE = {
    "west": "east",
    "east": "west",
    "south": "north",
    "north": "south",
}


class MetadataConfig(BaseModel):
    case_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str | None = None
    stage: Literal["v0.1", "v0.2", "v0.3"] = "v0.1"


class GeometryConfig(BaseModel):
    length_m: float = Field(gt=0)
    width_m: float = Field(gt=0)
    water_depth_m: float = Field(gt=0)


class HydraulicsConfig(BaseModel):
    flow_rate_m3_s: float = Field(gt=0)
    temperature_c: float = 20.0


class OpeningConfig(BaseModel):
    side: BoundarySide
    center_m: float = Field(ge=0)
    span_m: float = Field(gt=0)


class BoundaryBehaviorConfig(BaseModel):
    wall_condition: Literal["impermeable"] = "impermeable"
    baffle_condition: Literal["impermeable"] = "impermeable"


class BedConfig(BaseModel):
    model: Literal["flat"] = "flat"
    slope_x_m_per_m: float = 0.0
    slope_y_m_per_m: float = 0.0

    @model_validator(mode="after")
    def validate_flat_bed(self) -> "BedConfig":
        if self.model == "flat" and (self.slope_x_m_per_m != 0.0 or self.slope_y_m_per_m != 0.0):
            raise ValueError("flat bed model requires zero slope_x_m_per_m and slope_y_m_per_m")
        return self


class BaffleConfig(BaseModel):
    name: str = Field(min_length=1)
    kind: BaffleKind = "full_depth_solid"
    x1_m: float = Field(ge=0)
    y1_m: float = Field(ge=0)
    x2_m: float = Field(ge=0)
    y2_m: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_segment(self) -> "BaffleConfig":
        if self.x1_m == self.x2_m and self.y1_m == self.y2_m:
            raise ValueError("baffle line segment must have non-zero length")
        return self


class NumericsConfig(BaseModel):
    nx: int = Field(default=100, ge=4)
    ny: int = Field(default=30, ge=4)
    solver_model: Literal["steady_screening_potential"] = "steady_screening_potential"
    turbulence_model: Literal["constant_eddy_viscosity"] = "constant_eddy_viscosity"
    eddy_viscosity_m2_s: float = Field(default=1.0e-3, gt=0)
    max_iterations: int = Field(default=2500, ge=10)
    tolerance: float = Field(default=1.0e-6, gt=0)
    relaxation_factor: float = Field(default=1.65, gt=0, lt=2.0)


class OutputsConfig(BaseModel):
    run_root: str = "runs"
    write_layout_svg: bool = True
    write_velocity_svg: bool = True
    write_fields_json: bool = True


class ScenarioConfig(BaseModel):
    metadata: MetadataConfig
    geometry: GeometryConfig
    hydraulics: HydraulicsConfig
    inlet: OpeningConfig
    outlet: OpeningConfig
    boundaries: BoundaryBehaviorConfig = Field(default_factory=BoundaryBehaviorConfig)
    bed: BedConfig = Field(default_factory=BedConfig)
    baffles: list[BaffleConfig] = Field(default_factory=list)
    numerics: NumericsConfig = Field(default_factory=NumericsConfig)
    outputs: OutputsConfig = Field(default_factory=OutputsConfig)

    @model_validator(mode="after")
    def validate_geometry_dependent_fields(self) -> "ScenarioConfig":
        geometry = self.geometry

        self._validate_opening(self.inlet, geometry, "inlet")
        self._validate_opening(self.outlet, geometry, "outlet")

        if self.inlet.side == self.outlet.side:
            raise ValueError("inlet and outlet cannot be on the same side")

        if OPPOSITE_SIDE[self.inlet.side] != self.outlet.side:
            raise ValueError(
                "current v0.1 solver requires inlet and outlet on opposite sides "
                "(west/east or south/north)"
            )

        for baffle in self.baffles:
            for x in (baffle.x1_m, baffle.x2_m):
                if x > geometry.length_m:
                    raise ValueError(f"baffle '{baffle.name}' x-coordinate exceeds basin length")
            for y in (baffle.y1_m, baffle.y2_m):
                if y > geometry.width_m:
                    raise ValueError(f"baffle '{baffle.name}' y-coordinate exceeds basin width")

            if baffle.kind == "full_depth_solid":
                is_vertical = baffle.x1_m == baffle.x2_m
                is_horizontal = baffle.y1_m == baffle.y2_m

                if not (is_vertical or is_horizontal):
                    raise ValueError(
                        f"full-depth solid baffle '{baffle.name}' must be axis-aligned for the v0.1 solver"
                    )

                if is_vertical and not (0.0 < baffle.x1_m < geometry.length_m):
                    raise ValueError(
                        f"vertical full-depth solid baffle '{baffle.name}' must lie inside the basin interior"
                    )
                if is_horizontal and not (0.0 < baffle.y1_m < geometry.width_m):
                    raise ValueError(
                        f"horizontal full-depth solid baffle '{baffle.name}' must lie inside the basin interior"
                    )
        return self

    @staticmethod
    def _validate_opening(opening: OpeningConfig, geometry: GeometryConfig, label: str) -> None:
        extent = geometry.width_m if opening.side in ("west", "east") else geometry.length_m
        lower = opening.center_m - (opening.span_m / 2.0)
        upper = opening.center_m + (opening.span_m / 2.0)

        if lower < 0.0 or upper > extent:
            raise ValueError(
                f"{label} span exceeds the available {opening.side} boundary extent of {extent:.3f} m"
            )


def load_raw_scenario(path: str | Path) -> dict[str, Any]:
    scenario_path = Path(path)
    with scenario_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}

    if not isinstance(payload, dict):
        raise ValueError("scenario root must be a mapping")

    return payload


def load_scenario(path: str | Path) -> ScenarioConfig:
    return ScenarioConfig.model_validate(load_raw_scenario(path))


def dump_scenario_yaml(scenario: ScenarioConfig) -> str:
    return yaml.safe_dump(scenario.model_dump(mode="python"), sort_keys=False)
