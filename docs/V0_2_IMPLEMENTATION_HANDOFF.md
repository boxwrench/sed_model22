# V0.2 Design-vs-Current Basin Comparison Handoff

This document is the implementation handoff for the next major product slice in `sed_model22`.

It is written for another model or engineer to execute with minimal judgment. The intent is to make the work decision-complete, repo-local, and easy to track.

## Purpose

Build a new `v0.2` longitudinal `2D length x depth` hydraulic comparison workflow beside the existing `v0.1` plan-view solver.

The first practical deliverable is a study that compares:

- the original design-spec basin
- the current as-is basin where the diamond-cutout perforated transition wall is now blocked by backer boards

The result should be a transparent screening tool that helps answer:

- what hydraulic changes the blocked wall is causing
- whether the current state increases short-circuiting risk
- whether the current state worsens flow uniformity or launder/upwelling risk
- whether the current state changes residence-time behavior in ways that matter operationally

This is not meant to be a calibrated digital twin yet.

## Progress Tracking

- [x] Install and verify the intended Python environment
- [x] Refactor config loading to support `v0.1` and `v0.2`
- [x] Add longitudinal mesh support
- [x] Add longitudinal steady screening solver
- [x] Add tracer / RTD proxy layer
- [x] Add longitudinal metrics layer
- [x] Make run workflow model-aware
- [x] Add comparison study workflow
- [x] Add longitudinal SVG outputs
- [x] Add plant-specific scenario templates
- [x] Add tests for schema, solver, study workflow, and CLI
- [x] Run the full test suite in the intended environment

## Hard Constraints

- Do not delete or silently repurpose the current `v0.1` solver.
- Preserve backward compatibility for existing `v0.1` scenarios that omit `model_form`.
- Keep the repo custom-Python-first.
- Do not introduce external CFD dependencies.
- Do not implement explicit mixer-blade hydrodynamics, full solids transport, or real water-quality prediction.
- Do not implement PDF or drawing ingestion in this milestone.

## Product Boundary

### In Scope

- a new `longitudinal_v0_2` scenario type
- a new longitudinal structured grid in `x-z`
- a new steady screening-flow solver using conductance/resistance abstractions
- passive tracer transport for RTD-style metrics
- settling-risk proxy metrics based on upward velocity thresholds
- a study YAML format for multi-case, multi-flow comparison
- a new CLI command to run a study and write comparison outputs
- plant-specific design and current scenario templates

### Out of Scope

- 3D flow
- explicit RANS turbulence models
- calibrated solids or turbidity prediction
- field data ingestion or SCADA coupling
- auto-generated geometry from record drawings

## Design Decision

The repo currently has a `v0.1` plan-view screening solver. Do not extend that solver as the main answer to the blocked-wall question.

The new `v0.2` path should instead use a longitudinal `length x depth` cross-section because:

- the basin is strongly longitudinal
- the transition wall affects vertical redistribution
- the plate settler zone alters upper-flow behavior
- launder and upwelling questions are vertical, not mainly plan-view questions

The `v0.2` solver should remain screening-oriented and transparent. It should use the same repo style as `v0.1`: structured grids, deterministic artifacts, explicit assumptions, and simple numerics.

## Research Review Note

An external research memo was reviewed and archived at:

- `docs/research/PERFORATED_BAFFLE_AND_PLATE_SETTLER_MODELING_MEMO.md`

What it changes:

- it strengthens the case that plate settlers should later be represented with a more physically grounded anisotropic porous-zone abstraction
- it strengthens the case that explicit orifice geometry may be needed in a later redesign-focused model when the question becomes hole pattern optimization
- it reinforces the value of future field validation through wall headloss and tracer testing

What it does not change:

- it does not change the current `v0.2` implementation boundary
- it does not justify replacing the current proof-of-concept pass with a 3D RANS / CFD-first implementation
- it does not require exact as-built geometry reconciliation before the current workflow is useful as a proof of concept

Important plant note for future versions:

- the real basin still passes flow when the perforated wall is blocked because the basin has a serpentine over-under path
- therefore, a future higher-confidence current-state model must represent the actual bypass path explicitly
- a future geometry-verification pass should reconcile the exact dimensions, wall details, and active flow path from drawings and field observation

Working rule:

- `v0.2` is for proving the comparison workflow and the decision-support procedure
- later versions are where geometry verification, explicit bypass representation, and possibly explicit orifice geometry should be added

## Implementation Order

Implement in this order:

1. Install the intended environment:
   - `python -m pip install -e .[dev]`
2. Refactor config loading to support two scenario families plus one study format.
3. Add longitudinal mesh support.
4. Add the longitudinal steady screening solver.
5. Add passive tracer transport and RTD metrics.
6. Add longitudinal engineering metrics.
7. Refactor run materialization so it is model-aware.
8. Add the comparison study runner and CLI command.
9. Add longitudinal plots and the comparison report.
10. Add plant-specific scenarios and study templates.
11. Add tests and run the full suite.

Do not start with plotting or reporting. The schema and solver need to settle first.

## Required File Changes

### Add New Files

- `src/sed_model22/mesh/longitudinal.py`
- `src/sed_model22/solver/longitudinal.py`
- `src/sed_model22/metrics/longitudinal.py`
- `src/sed_model22/study.py`
- `src/sed_model22/viz/longitudinal_svg.py`
- `tests/test_config_v2.py`
- `tests/test_longitudinal_mesh.py`
- `tests/test_longitudinal_solver.py`
- `tests/test_study.py`
- `scenarios/svwtp_design_spec_basin.yaml`
- `scenarios/svwtp_current_blocked_wall_basin.yaml`
- `scenarios/studies/svwtp_design_vs_current.yaml`

### Update Existing Files

- `src/sed_model22/config.py`
- `src/sed_model22/mesh/__init__.py`
- `src/sed_model22/solver/__init__.py`
- `src/sed_model22/metrics/__init__.py`
- `src/sed_model22/run.py`
- `src/sed_model22/cli.py`
- `src/sed_model22/viz/__init__.py`

Only update other files if strictly needed for integration.

## Configuration Model

Refactor `config.py` so it cleanly supports both solver families.

### Required Types

Add:

- `PlanViewScenarioConfig`
- `LongitudinalScenarioConfig`
- `ComparisonStudyConfig`
- `ScenarioConfig = PlanViewScenarioConfig | LongitudinalScenarioConfig`

### Backward Compatibility Rule

Existing `v0.1` YAML files do not declare `model_form`.

When loading a scenario:

- if `model_form` is missing, inject `plan_view_v0_1`
- then validate against the union

This keeps old scenario files working unchanged.

### `PlanViewScenarioConfig`

This is the current schema, with only one new field added:

```yaml
model_form: plan_view_v0_1
```

It should otherwise preserve the current data model and validation rules.

### `LongitudinalScenarioConfig`

This is the new `v0.2` schema.

It must contain these sections:

- `metadata`
- `model_form`
- `geometry`
- `hydraulics`
- `upstream`
- `features`
- `evaluation_stations`
- `performance_proxies`
- `numerics`
- `outputs`

Use this exact shape:

```yaml
metadata:
  case_id: svwtp_design_spec
  title: SVWTP Design Spec Basin
  description: Design-intent longitudinal screening model.
  stage: v0.2

model_form: longitudinal_v0_2

geometry:
  basin_length_m: 103.63
  basin_width_m: 18.29
  water_depth_m: 3.35

hydraulics:
  flow_rate_m3_s: 1.75
  temperature_c: 18.0

upstream:
  inlet_zone_height_m: 1.2
  inlet_zone_center_elevation_m: 2.6
  inlet_orifice_count: 8
  inlet_loss_coefficient: 1.0
  mixing_zone_length_m: 6.0
  mixing_intensity_factor: 1.0

features:
  - kind: perforated_baffle
    name: transition_wall
    x_m: 2.0
    z_bottom_m: 0.0
    z_top_m: 3.35
    open_area_fraction: 0.06
    plate_thickness_m: 0.02
    loss_scale: 1.0
  - kind: plate_settler_zone
    name: plate_zone
    x_start_m: 70.0
    x_end_m: 95.0
    z_bottom_m: 1.9
    z_top_m: 3.2
    plate_angle_deg: 60.0
    plate_spacing_m: 0.05
    plate_thickness_m: 0.002
    resistance_scale: 1.0
    cross_flow_factor: 0.05
  - kind: launder_zone
    name: outlet_launder
    x_start_m: 96.0
    x_end_m: 103.63
    z_m: 3.35
    sink_weight: 1.0

evaluation_stations:
  - name: post_transition
    x_m: 8.0
  - name: plate_inlet
    x_m: 70.0
  - name: launder_zone
    x_m: 100.0

performance_proxies:
  settling_velocity_thresholds_m_per_s: [0.0005, 0.001, 0.002]
  dead_zone_velocity_fraction: 0.10
  tracer_max_time_factor: 4.0
  tracer_target_fraction: 0.995

numerics:
  nx: 120
  nz: 40
  solver_model: steady_screening_longitudinal
  eddy_diffusivity_m2_s: 0.001
  max_iterations: 4000
  tolerance: 0.000001
  relaxation_factor: 1.6
  tracer_cfl: 0.35

outputs:
  run_root: runs
  write_layout_svg: true
  write_velocity_svg: true
  write_fields_json: true
  write_tracer_svg: true
```

### Feature Types

Implement these feature kinds:

- `perforated_baffle`
- `solid_baffle`
- `plate_settler_zone`
- `launder_zone`

#### `solid_baffle`

- vertical internal barrier
- blocks flow completely
- same geometry family as `perforated_baffle`

#### `perforated_baffle`

- vertical internal barrier
- represented as a thin loss interface
- used for the original design wall

#### Current-State Representation Rule

The blocked-wall case is not a different geometric feature. It is the same transition wall with:

- `open_area_fraction: 0.001`
- `loss_scale: 4.0`

This is important because the comparison should isolate hydraulic effect from geometry drift.

#### `plate_settler_zone`

- rectangular porous sub-zone in the upper basin
- anisotropic resistance
- geometry-driven defaults with overridable scaling

#### `launder_zone`

- top-boundary outlet collection region
- defined over an `x` span at elevation `z_m`
- treated as a distributed outlet sink / zero-head zone on the top boundary

### Study Schema

Add a separate YAML format for comparison studies.

Use this exact structure:

```yaml
study_id: svwtp_design_vs_current
title: SVWTP Design vs Current Basin
description: Compare design-intent and blocked-wall current basin at 3 flows.

cases:
  - label: design_spec
    scenario_path: scenarios/svwtp_design_spec_basin.yaml
  - label: current_blocked
    scenario_path: scenarios/svwtp_current_blocked_wall_basin.yaml

flows:
  - label: low
    flow_rate_m3_s: 0.75
  - label: typical
    flow_rate_m3_s: 1.75
  - label: high
    flow_rate_m3_s: 2.80

outputs:
  run_root: runs
  report_name: comparison_report.md
  csv_name: comparison_summary.csv
```

### Validation Rules

For `longitudinal_v0_2`:

- `basin_length_m > 0`
- `basin_width_m > 0`
- `water_depth_m > 0`
- `flow_rate_m3_s > 0`
- all feature coordinates must lie within basin extents
- `perforated_baffle.open_area_fraction` must satisfy `0 < value <= 1`
- `plate_settler_zone.x_start_m < x_end_m`
- `plate_settler_zone.z_bottom_m < z_top_m`
- `launder_zone.z_m <= water_depth_m`
- every `evaluation_stations.x_m` must lie within basin length

For study files:

- at least 2 cases
- at least 1 flow
- every `flow_rate_m3_s > 0`

## Mesh Layer

Create `src/sed_model22/mesh/longitudinal.py`.

### Required Types

- `LongitudinalMeshSummary`
- `build_longitudinal_mesh(scenario: LongitudinalScenarioConfig)`

### Required Fields

- `nx`
- `nz`
- `dx_m`
- `dz_m`
- `cell_count`

### Coordinate Convention

- `x = 0` at the basin inlet end
- `x = basin_length_m` at the outlet end
- `z = 0` at basin floor
- `z = water_depth_m` at water surface

Use cell centers like the current `v0.1` mesh style.

## Solver Layer

Create `src/sed_model22/solver/longitudinal.py`.

### Required Types

- `LongitudinalSolutionSummary`
- `LongitudinalFieldData`

The field object should include at least:

- `x_centers_m`
- `z_centers_m`
- `head`
- `velocity_u_m_s`
- `velocity_w_m_s`
- `speed_m_s`
- `cell_divergence_1_per_s`

### Solver Function

Implement:

- `solve_steady_longitudinal_screening_flow()`

This solver should match the current repo style:

- structured grid
- deterministic numerics
- explicit summary model
- clear supported scope and notes

### Numerical Approach

Use a scalar head-like steady solve plus conductance scaling, similar in spirit to the current `v0.1` potential-flow-like solver.

Algorithm:

1. Initialize a head field that decreases from inlet side to outlet side.
2. Create face-conductance arrays:
   - `x_face_conductance`
   - `z_face_conductance`
3. Default all conductances to `1.0`.
4. Apply upstream inlet loss by scaling the left-boundary conductance across the inlet elevation span.
5. Convert internal features into conductance modifications.
6. Solve the head field by Gauss-Seidel relaxation to convergence.
7. Compute face fluxes and then cell velocities.
8. Scale the velocity field so inlet discharge matches the scenario flow.

### Internal Feature Treatment

#### Upstream Inlet Loss

Use the `upstream` block to define the active inlet elevation span and reduce left-boundary conductance according to:

- `inlet_zone_height_m`
- `inlet_zone_center_elevation_m`
- `inlet_loss_coefficient`

This is a simplified upstream influence representation. Do not model floc mixers explicitly.

#### Solid Baffle

For a `solid_baffle`, set conductance across the corresponding `x` faces to `0.0`.

#### Perforated Baffle

For a `perforated_baffle`, compute the thin-plate loss coefficient using:

```text
k = ([0.707 * (1 - phi)^0.375] + 1 - phi^2)^2 / phi^2
face_conductance = phi / (1 + loss_scale * k)
```

Where:

- `phi = open_area_fraction`
- `loss_scale` is user-defined

Clamp conductance to a minimum such as `1e-6`.

#### Plate Settler Zone

Treat the plate settler as an anisotropic porous zone.

Compute:

```text
void_fraction = plate_spacing_m / (plate_spacing_m + plate_thickness_m)
k_parallel = max(0.02, void_fraction / resistance_scale)
k_perp = max(0.005, k_parallel * cross_flow_factor)
theta = radians(plate_angle_deg)
kx = k_parallel * cos(theta)^2 + k_perp * sin(theta)^2
kz = k_parallel * sin(theta)^2 + k_perp * cos(theta)^2
```

Then scale faces inside the zone using:

- `kx` for `x` conductance
- `kz` for `z` conductance

#### Launder Zone

Treat `launder_zone` cells on the top boundary as outlet boundary cells with head `0.0`.

If multiple launder zones exist later, allow multiple outlet spans.

### Boundary Conditions

- Inlet span on the left boundary: head `1.0`
- Launder span on the top boundary: head `0.0`
- All other boundaries: no-flow unless explicitly active

### Flow Scaling

Scale velocities so the total inlet discharge matches the 2D cross-section flow:

```text
Q_2D = flow_rate_m3_s / basin_width_m
```

Then report total basin flow quantities using basin width.

### Required Summary Metrics in Solver Output

Include at least:

- solver name
- solver status
- solver model
- iterations
- converged
- max head delta
- inlet discharge
- outlet discharge
- mass balance error
- max velocity
- max upward velocity
- blocked / low-conductance face counts
- supported scope
- notes

## Tracer Layer

Tracer is a proxy layer built on the steady velocity field. Do not implement solids transport in this milestone.

### Required Behavior

- step tracer input concentration `1.0` at inlet cells
- explicit upwind advection
- isotropic diffusion using `eddy_diffusivity_m2_s`
- outlet concentration recorded as the average tracer value over launder boundary cells

### Time Step

Use:

```text
dt = tracer_cfl * min(dx/max(|u|), dz/max(|w|))
```

Guard against divide-by-zero by applying a positive floor for denominators.

### End Condition

Simulate until either:

- outlet concentration reaches `tracer_target_fraction`
- or elapsed time reaches `tracer_max_time_factor * theoretical_detention_time`

### Required Tracer Outputs

Write `tracer.json` for every `v0.2` run. Include:

- time points
- outlet concentration history
- `t10`
- `t50`
- `t90`

Use interpolation for threshold crossing times.

## Longitudinal Metrics

Create `src/sed_model22/metrics/longitudinal.py`.

### Required Metrics

- `basin_volume_m3`
- `theoretical_detention_time_s`
- `surface_overflow_rate_m_per_d`
- `transition_headloss_m`
- `post_transition_velocity_uniformity_index`
- `jet_redistribution_length_m`
- `plate_inlet_mean_velocity_m_s`
- `plate_inlet_max_velocity_m_s`
- `plate_inlet_upward_velocity_m_s`
- `launder_mean_upward_velocity_m_s`
- `launder_peak_upward_velocity_m_s`
- `dead_zone_fraction`
- `short_circuiting_index`
- `t10_s`
- `t50_s`
- `t90_s`
- `morrill_index`
- `settling_exceedance_fraction_by_threshold`

### Exact Definitions

#### Velocity Uniformity Index

At a station:

```text
VUI = mean(|u|) / max(|u|)
```

Use the longitudinal velocity magnitude along the relevant `x` column.

#### Jet Redistribution Length

Define:

```text
first x where VUI >= 0.80 and remains >= 0.80 for 3 consecutive columns
```

If never achieved, report `None` or the basin length consistently. Pick one policy and use it everywhere.

#### Dead Zone Fraction

```text
fraction of cells where speed < dead_zone_velocity_fraction * basin_mean_speed
```

#### Short-Circuiting Index

```text
t10 / theoretical_detention_time
```

#### Morrill Index

```text
t90 / t10
```

#### Settling Exceedance Fraction

For each threshold `vs`:

```text
fraction of launder-zone boundary cells where upward velocity > vs
```

## Run Workflow

Refactor `src/sed_model22/run.py` so it is model-aware.

### Rule

- `v0.1` runs still call the existing mesh / metrics / solver path
- `v0.2` runs call the new longitudinal mesh / solver / tracer / metrics path

### Required Artifacts for `v0.2`

Write:

- `scenario_snapshot.yaml`
- `mesh.json`
- `metrics.json`
- `summary.json`
- `fields.json`
- `tracer.json`
- `plots/basin_layout.svg`
- `plots/velocity_magnitude.svg`
- `plots/tracer_breakthrough.svg`

Keep the existing run directory structure.

### `summary.json`

For `v0.2`, include:

- scenario metadata
- geometry
- hydraulics
- upstream config
- features
- numerics
- mesh
- metrics
- solver summary

## Study Workflow

Create `src/sed_model22/study.py`.

### Responsibilities

- load the study YAML
- resolve scenario paths
- override scenario flow rate per study flow
- run each `case x flow` combination
- collect metrics into comparison outputs

### Required CLI Command

Add:

```bash
sed-model compare-study scenarios/studies/svwtp_design_vs_current.yaml
```

### Study Behavior

For each case and each flow:

1. load the scenario
2. clone it with the flow override
3. run it through the standard run materialization path
4. collect key metrics into a table

Then create a study output directory under the configured run root and write:

- `comparison_summary.json`
- `comparison_summary.csv`
- `comparison_report.md`

## CSV Output

Write one row per `case x flow`.

Required columns:

- `study_id`
- `case_label`
- `flow_label`
- `flow_rate_m3_s`
- all core comparison metrics

Use deterministic column ordering.

## Markdown Report

`comparison_report.md` must be human-readable and deterministic.

Use this structure:

1. title
2. cases
3. flows
4. model limitations
5. per-flow comparison tables
6. delta summary where delta is:
   - `current_blocked - design_spec`
7. interpretation bullets that explicitly state:
   - more or less headloss
   - better or worse uniformity
   - earlier or later RTD breakthrough
   - higher or lower launder upwelling risk
   - higher or lower settling-threshold exceedance

Do not make the report vague. It should say what changed and in which direction.

## Plotting

Create `src/sed_model22/viz/longitudinal_svg.py`.

### Required Plots

- `x-z` layout plot
- `x-z` velocity magnitude heatmap
- tracer breakthrough curve line plot

Update `viz/__init__.py` to export both the current `v0.1` helpers and the new `v0.2` helpers.

Do not break existing `v0.1` plotting functions.

## CLI Changes

Update `src/sed_model22/cli.py`.

### Keep Existing Commands

- `validate`
- `run-hydraulics`
- `summarize`
- `plot`

### Add

- `compare-study`

### Flow Override

Add:

```text
--flow-rate-m3-s
```

to `run-hydraulics`.

This is needed so study runs can override flow without rewriting scenario files.

### Validation Command Policy

Preferred approach:

- keep `validate` for scenarios only
- add `validate-study` for study files

If unified validation is easy and clean, it is acceptable, but do not complicate the CLI for little gain.

### Summarize Output

For `v0.2`, print:

- case
- stage
- model form
- detention time
- headloss across transition wall
- post-transition VUI
- jet redistribution length
- launder peak upward velocity
- short-circuiting index
- Morrill index

For `v0.1`, preserve current behavior.

## Plant-Specific Scenarios

Create:

- `scenarios/svwtp_design_spec_basin.yaml`
- `scenarios/svwtp_current_blocked_wall_basin.yaml`
- `scenarios/studies/svwtp_design_vs_current.yaml`

### First-Pass Scenario Policy

Use the same basin geometry in both design and current files.

The only required initial delta is the transition wall opening:

- design case:
  - `open_area_fraction: 0.06`
  - `loss_scale: 1.0`
- current case:
  - `open_area_fraction: 0.001`
  - `loss_scale: 4.0`

Keep plate settler and launder features identical between the two cases for the first study.

## Testing

Add these test files:

- `tests/test_config_v2.py`
- `tests/test_longitudinal_mesh.py`
- `tests/test_longitudinal_solver.py`
- `tests/test_study.py`

Keep all existing test files intact.

### Required Test Cases

- `v0.1` baseline scenario still validates
- `v0.1` baseline still runs through the CLI
- `v0.2` scenario validates
- study file validates
- perforated-wall conductance decreases as open area decreases
- blocked-wall case produces more transition headloss than design case
- plate-settler zone changes the upper-zone velocity pattern
- launder-zone discharge conserves mass within tolerance
- tracer metrics are finite and ordered: `t10 < t50 < t90`
- `compare-study` writes JSON, CSV, Markdown, and individual run bundles
- `compare-study` works from the CLI

### Acceptance Criteria

Implementation is complete only when all of the following are true:

- old scenarios still run unchanged
- new `v0.2` scenarios validate and run
- the study command generates all required study outputs
- the report clearly shows a difference between design and blocked-wall cases
- tests pass in the intended environment

## Recommended Development Notes

- Keep the `v0.2` code path separate enough that it does not pollute `v0.1` logic with many conditional branches.
- Prefer adding new models and dispatch functions over deeply branching existing functions.
- Reuse the current artifact structure and naming conventions where possible.
- Keep all output deterministic and text-friendly.
- Document assumptions in solver summaries and reports.
- Use concise comments only where the numeric logic is not self-evident.

## Environment Note

The current local shell may not have all declared dependencies installed. At minimum, `PyYAML` was previously missing during test execution.

Do not treat local missing dependencies as a code bug until the intended environment is installed with:

```bash
python -m pip install -e .[dev]
```

## Definition of Done

The work is done when:

- `v0.1` remains backward compatible
- `v0.2` longitudinal scenarios run successfully
- `compare-study` produces comparison artifacts for the SVWTP design-vs-current study
- the design case and blocked-wall case show meaningful metric differences
- the full automated test suite passes in the intended environment
