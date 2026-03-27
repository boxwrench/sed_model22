from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator


BoundarySide = Literal["west", "east", "south", "north"]
BaffleKind = Literal["full_depth_solid", "curtain_placeholder", "porous_placeholder"]
FeatureKind = Literal["perforated_baffle", "solid_baffle", "plate_settler_zone", "launder_zone"]

OPPOSITE_SIDE = {
    "west": "east",
    "east": "west",
    "south": "north",
    "north": "south",
}


class MetadataConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str | None = None
    stage: Literal["v0.1", "v0.2", "v0.3"] = "v0.1"


class LongitudinalMetadataConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str | None = None
    stage: Literal["v0.2"] = "v0.2"


class GeometryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    length_m: float = Field(gt=0)
    width_m: float = Field(gt=0)
    water_depth_m: float = Field(gt=0)


class LongitudinalGeometryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    basin_length_m: float = Field(gt=0)
    basin_width_m: float = Field(gt=0)
    water_depth_m: float = Field(gt=0)


class HydraulicsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    flow_rate_m3_s: float = Field(gt=0)
    temperature_c: float = 20.0


class OpeningConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    side: BoundarySide
    center_m: float = Field(ge=0)
    span_m: float = Field(gt=0)


class BoundaryBehaviorConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    wall_condition: Literal["impermeable"] = "impermeable"
    baffle_condition: Literal["impermeable"] = "impermeable"


class BedConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: Literal["flat"] = "flat"
    slope_x_m_per_m: float = 0.0
    slope_y_m_per_m: float = 0.0

    @model_validator(mode="after")
    def validate_flat_bed(self) -> "BedConfig":
        if self.model == "flat" and (self.slope_x_m_per_m != 0.0 or self.slope_y_m_per_m != 0.0):
            raise ValueError("flat bed model requires zero slope_x_m_per_m and slope_y_m_per_m")
        return self


class BaffleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

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
    model_config = ConfigDict(extra="forbid")

    nx: int = Field(default=100, ge=4)
    ny: int = Field(default=30, ge=4)
    solver_model: Literal["steady_screening_potential"] = "steady_screening_potential"
    turbulence_model: Literal["constant_eddy_viscosity"] = "constant_eddy_viscosity"
    eddy_viscosity_m2_s: float = Field(default=1.0e-3, gt=0)
    max_iterations: int = Field(default=2500, ge=10)
    tolerance: float = Field(default=1.0e-6, gt=0)
    relaxation_factor: float = Field(default=1.65, gt=0, lt=2.0)


class OutputsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_root: str = "runs"
    write_layout_svg: bool = True
    write_velocity_svg: bool = True
    write_fields_json: bool = True
    write_tracer_svg: bool = False


class PlanViewScenarioConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_form: Literal["plan_view_v0_1"] = "plan_view_v0_1"
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
    def validate_geometry_dependent_fields(self) -> "PlanViewScenarioConfig":
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


class PerforatedBaffleFeatureConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["perforated_baffle"]
    name: str = Field(min_length=1)
    x_m: float = Field(ge=0)
    z_bottom_m: float = Field(ge=0)
    z_top_m: float = Field(gt=0)
    open_area_fraction: float = Field(gt=0, le=1)
    plate_thickness_m: float = Field(gt=0)
    loss_scale: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_geometry(self) -> "PerforatedBaffleFeatureConfig":
        if self.z_bottom_m >= self.z_top_m:
            raise ValueError("perforated_baffle z_bottom_m must be below z_top_m")
        return self


class SolidBaffleFeatureConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["solid_baffle"]
    name: str = Field(min_length=1)
    x_m: float = Field(ge=0)
    z_bottom_m: float = Field(ge=0)
    z_top_m: float = Field(gt=0)
    plate_thickness_m: float = Field(default=0.02, gt=0)
    loss_scale: float = Field(default=1.0, gt=0)

    @model_validator(mode="after")
    def validate_geometry(self) -> "SolidBaffleFeatureConfig":
        if self.z_bottom_m >= self.z_top_m:
            raise ValueError("solid_baffle z_bottom_m must be below z_top_m")
        return self


class PlateSettlerZoneFeatureConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["plate_settler_zone"]
    name: str = Field(min_length=1)
    x_start_m: float = Field(ge=0)
    x_end_m: float = Field(gt=0)
    z_bottom_m: float = Field(ge=0)
    z_top_m: float = Field(gt=0)
    plate_angle_deg: float = Field(ge=0, le=90)
    plate_spacing_m: float = Field(gt=0)
    plate_thickness_m: float = Field(gt=0)
    resistance_scale: float = Field(gt=0)
    cross_flow_factor: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_geometry(self) -> "PlateSettlerZoneFeatureConfig":
        if self.x_start_m >= self.x_end_m:
            raise ValueError("plate_settler_zone x_start_m must be below x_end_m")
        if self.z_bottom_m >= self.z_top_m:
            raise ValueError("plate_settler_zone z_bottom_m must be below z_top_m")
        return self


class LaunderZoneFeatureConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["launder_zone"]
    name: str = Field(min_length=1)
    x_start_m: float = Field(ge=0)
    x_end_m: float = Field(gt=0)
    z_m: float = Field(ge=0)
    sink_weight: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_geometry(self) -> "LaunderZoneFeatureConfig":
        if self.x_start_m >= self.x_end_m:
            raise ValueError("launder_zone x_start_m must be below x_end_m")
        return self


FeatureConfig = Annotated[
    PerforatedBaffleFeatureConfig
    | SolidBaffleFeatureConfig
    | PlateSettlerZoneFeatureConfig
    | LaunderZoneFeatureConfig,
    Field(discriminator="kind"),
]


class EvaluationStationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    x_m: float = Field(ge=0)


class PerformanceProxiesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    settling_velocity_thresholds_m_per_s: list[float] = Field(min_length=1)
    dead_zone_velocity_fraction: float = Field(gt=0)
    tracer_max_time_factor: float = Field(gt=0)
    tracer_target_fraction: float = Field(gt=0, le=1)

    @model_validator(mode="after")
    def validate_thresholds(self) -> "PerformanceProxiesConfig":
        if any(value <= 0.0 for value in self.settling_velocity_thresholds_m_per_s):
            raise ValueError("settling_velocity_thresholds_m_per_s must contain positive values")
        return self


class LongitudinalNumericsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nx: int = Field(default=72, ge=4)
    nz: int = Field(default=24, ge=4)
    solver_model: Literal["steady_screening_longitudinal"] = "steady_screening_longitudinal"
    eddy_diffusivity_m2_s: float = Field(default=1.0e-3, gt=0)
    max_iterations: int = Field(default=4000, ge=10)
    tolerance: float = Field(default=1.0e-6, gt=0)
    relaxation_factor: float = Field(default=1.6, gt=0, lt=2.0)
    tracer_cfl: float = Field(default=0.35, gt=0)


class LongitudinalOutputsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_root: str = "runs"
    write_layout_svg: bool = True
    write_velocity_svg: bool = True
    write_fields_json: bool = True
    write_tracer_svg: bool = True


class LongitudinalScenarioConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_form: Literal["longitudinal_v0_2"] = "longitudinal_v0_2"
    metadata: LongitudinalMetadataConfig
    geometry: LongitudinalGeometryConfig
    hydraulics: HydraulicsConfig
    upstream: "UpstreamConfig"
    features: list[FeatureConfig] = Field(default_factory=list)
    evaluation_stations: list[EvaluationStationConfig] = Field(default_factory=list)
    performance_proxies: PerformanceProxiesConfig
    numerics: LongitudinalNumericsConfig = Field(default_factory=LongitudinalNumericsConfig)
    outputs: LongitudinalOutputsConfig = Field(default_factory=LongitudinalOutputsConfig)

    @model_validator(mode="after")
    def validate_geometry_dependent_fields(self) -> "LongitudinalScenarioConfig":
        geometry = self.geometry

        if self.upstream.inlet_zone_height_m <= 0.0:
            raise ValueError("inlet_zone_height_m must be positive")

        zone_bottom = self.upstream.inlet_zone_center_elevation_m - (self.upstream.inlet_zone_height_m / 2.0)
        zone_top = self.upstream.inlet_zone_center_elevation_m + (self.upstream.inlet_zone_height_m / 2.0)
        if zone_bottom < 0.0 or zone_top > geometry.water_depth_m:
            raise ValueError("upstream inlet zone must lie within the water depth")

        for feature in self.features:
            if isinstance(feature, (PerforatedBaffleFeatureConfig, SolidBaffleFeatureConfig)):
                if not (0.0 < feature.x_m < geometry.basin_length_m):
                    raise ValueError(f"feature '{feature.name}' x_m must lie inside the basin interior")
                if feature.z_bottom_m < 0.0 or feature.z_top_m > geometry.water_depth_m:
                    raise ValueError(f"feature '{feature.name}' vertical span must lie within the water depth")
            elif isinstance(feature, PlateSettlerZoneFeatureConfig):
                if feature.x_start_m < 0.0 or feature.x_end_m > geometry.basin_length_m:
                    raise ValueError(f"plate_settler_zone '{feature.name}' must lie within basin length")
                if feature.z_bottom_m < 0.0 or feature.z_top_m > geometry.water_depth_m:
                    raise ValueError(f"plate_settler_zone '{feature.name}' must lie within water depth")
            elif isinstance(feature, LaunderZoneFeatureConfig):
                if feature.x_start_m < 0.0 or feature.x_end_m > geometry.basin_length_m:
                    raise ValueError(f"launder_zone '{feature.name}' must lie within basin length")
                if feature.z_m > geometry.water_depth_m:
                    raise ValueError(f"launder_zone '{feature.name}' z_m must not exceed the water depth")

        for station in self.evaluation_stations:
            if not (0.0 <= station.x_m <= geometry.basin_length_m):
                raise ValueError(f"evaluation station '{station.name}' x_m must lie within the basin length")

        if any(value <= 0.0 for value in self.performance_proxies.settling_velocity_thresholds_m_per_s):
            raise ValueError("settling velocity thresholds must be positive")

        return self


class UpstreamConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    inlet_zone_height_m: float = Field(gt=0)
    inlet_zone_center_elevation_m: float = Field(ge=0)
    inlet_orifice_count: int = Field(ge=1)
    inlet_loss_coefficient: float = Field(ge=0)
    mixing_zone_length_m: float = Field(ge=0)
    mixing_intensity_factor: float = Field(gt=0)


LongitudinalScenarioConfig.model_rebuild()


class StudyCaseConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1)
    scenario_path: str = Field(min_length=1)


class StudyFlowConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1)
    flow_rate_m3_s: float = Field(gt=0)


class ComparisonStudyOutputsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_root: str = "runs"
    report_name: str = "comparison_report.md"
    csv_name: str = "comparison_summary.csv"


class ComparisonStudyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    study_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str | None = None
    cases: list[StudyCaseConfig] = Field(min_length=2)
    flows: list[StudyFlowConfig] = Field(min_length=1)
    outputs: ComparisonStudyOutputsConfig = Field(default_factory=ComparisonStudyOutputsConfig)

    @model_validator(mode="after")
    def validate_labels(self) -> "ComparisonStudyConfig":
        case_labels = [case.label for case in self.cases]
        flow_labels = [flow.label for flow in self.flows]

        if len(set(case_labels)) != len(case_labels):
            raise ValueError("study case labels must be unique")
        if len(set(flow_labels)) != len(flow_labels):
            raise ValueError("study flow labels must be unique")
        return self


ScenarioConfig = PlanViewScenarioConfig | LongitudinalScenarioConfig

ScenarioConfigAdapter = TypeAdapter(ScenarioConfig)
StudyConfigAdapter = TypeAdapter(ComparisonStudyConfig)


def load_raw_scenario(path: str | Path) -> dict[str, Any]:
    scenario_path = Path(path)
    with scenario_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}

    if not isinstance(payload, dict):
        raise ValueError("scenario root must be a mapping")

    if "model_form" not in payload:
        payload = {**payload, "model_form": "plan_view_v0_1"}

    return payload


def load_scenario(path: str | Path) -> ScenarioConfig:
    return ScenarioConfigAdapter.validate_python(load_raw_scenario(path))


def dump_scenario_yaml(scenario: ScenarioConfig) -> str:
    return yaml.safe_dump(scenario.model_dump(mode="python"), sort_keys=False)


def load_raw_study(path: str | Path) -> dict[str, Any]:
    study_path = Path(path)
    with study_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}

    if not isinstance(payload, dict):
        raise ValueError("study root must be a mapping")

    return payload


def load_study(path: str | Path) -> ComparisonStudyConfig:
    return StudyConfigAdapter.validate_python(load_raw_study(path))


def dump_study_yaml(study: ComparisonStudyConfig) -> str:
    return yaml.safe_dump(study.model_dump(mode="python"), sort_keys=False)
