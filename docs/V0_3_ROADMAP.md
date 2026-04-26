# V0.3 Roadmap

This document defines the next major product step after the hardened `v0.2` design-versus-current comparison workflow.

`v0.3` is now deliberately narrow: explicit current-state bypass hydraulics. Solids consequence modeling moves to `v0.4`.

## Product Goal

`v0.3` should answer this question more honestly than the current proxy model:

- how does the current-state flow path change hydraulic redistribution when the bypass path is represented explicitly?

The current blocked-wall basin should stop being represented only as a lossy interface if the real basin passes flow through an over/under, side, or serpentine bypass path.

Working rule:

- complete M4 credibility hardening first
- explicit bypass geometry before solids consequence modeling
- preserve transparent screening scope and uncertainty
- keep outputs useful to operators and managers without overstating numerical strength

## Preconditions

Do not start `v0.3` schema or solver work until M4 is complete.

Required M4 items:

- solver verification tests against known analytical or expected screening-solver behavior
- synthetic metrics unit tests
- function-level solver and metrics docstrings
- mesh sensitivity smoke checks on current `v0.2` comparison geometry
- run quality tiers in summaries and reports

## Must Have

### 1. Verified Bypass Geometry Capture

Required outcome:

- verify the current-state bypass path from drawings, field notes, or structured intake records
- record the uncertainty if dimensions are not fully confirmed
- do not encode guessed geometry as verified geometry

Why this is first:

- if the flow path is wrong, downstream redistribution, launder approach, and later solids conclusions will all be built on the wrong hydraulic picture

### 2. Schema Support for Explicit Bypass Features

Add scenario support for explicit bypass-path geometry.

Minimum fields should support:

- path type: `over`, `under`, `side`, `serpentine`, or equivalent explicit feature
- `x` extent
- `z` extent
- effective opening area or open fraction where needed
- notes or confidence fields for unverified dimensions
- design, current-state, and proposed-fix case labels where that matters

This should stay CLI/YAML-first and remain readable to humans.

### 3. Solver Support for Explicit Bypass Routing

The longitudinal solver should move from a wall-loss approximation to a geometry-aware routing representation for the current-state path.

In scope:

- explicit over/under, side, or serpentine path representation on the structured `x-z` grid where feasible
- updated flow redistribution around the blocked wall
- updated headloss and downstream uniformity response
- quality-tier reasons when the path representation is too coarse or the solve is weak

Out of scope:

- 3D flow
- full transient hydraulics
- CFD-level turbulence closure
- solids consequence modeling

### 4. N-Way Study Comparison

Prepare the study layer for design/current/proposed comparisons.

Required behavior:

- add optional `baseline_case_label`
- keep the current first-case baseline default when `baseline_case_label` is omitted
- preserve existing two-case study behavior
- report deltas against the selected baseline

### 5. Re-Baseline the Hydraulic Study

Once geometry changes are in, rerun low, typical, and high-flow comparisons.

Required outputs:

- updated run bundles
- updated comparison report
- updated study media packages if media remains enabled
- updated interpretation text where direction or magnitude changes
- visible `run_quality_tier` and `quality_reasons`

### 6. Mesh Sensitivity Checks on Revised Geometry

Add mesh sensitivity smoke checks for the revised geometry.

At minimum, check stability of:

- transition headloss
- post-transition velocity uniformity index
- launder peak upward velocity proxy
- `t10`, `t50`, and `t90`
- short-circuiting index

The goal is not publication-grade verification. The goal is enough stability to support screening decisions honestly.

## Should Have

### 1. Prescriptive Validation Errors

Wrap raw validation failures with field paths and suggested fixes for common scenario mistakes.

Candidate files:

- `src/sed_model22/cli.py`
- `src/sed_model22/config.py`

### 2. Solver Protocol Boundary

Define a small `SolverProtocol` before adding a third solver path.

Candidate file:

- `src/sed_model22/solver/protocol.py`

### 3. Template Extraction

Extract large HTML templates from Python string literals when touching the report layer.

Candidate destinations:

- `src/sed_model22/templates/`
- `src/sed_model22/media/templates/`

## Later

These are not part of `v0.3`:

- limited multi-class solids consequences, now planned for `v0.4`
- pseudo-transient flow stepping
- plate-settler momentum refinement
- interactive study viewer
- field-informed validation loop
- external CFD comparison

## Recommended Execution Order

1. Complete M4 credibility hardening.
2. Verify bypass geometry using `templates/intake_geometry_survey.yaml` or equivalent structured notes.
3. Extend schema for bypass-path geometry.
4. Implement explicit bypass routing in the longitudinal solver.
5. Add N-way comparison support with `baseline_case_label`.
6. Refresh current-state and proposed scenarios.
7. Re-run low, typical, and high-flow studies.
8. Add mesh sensitivity checks on the revised geometry.
9. Update report interpretation and quality-tier language.

## Definition of V0.3

`v0.3` is complete when the repo provides:

- explicit current-state bypass geometry
- updated hydraulic comparison on that geometry
- design/current/proposed comparison support
- quality-tiered reports that visibly distinguish credible, directional, and weak runs

`v0.3` is not:

- solids consequence modeling
- 3D CFD
- a calibrated digital twin
- full water-quality prediction
- a full transient plant simulator

## Working Constraint

Do not let visual or numerical sophistication outrun representational honesty.

The repo's strength is that it is understandable, inspectable, and explicit about what is proxy versus what is more physically grounded. `v0.3` should preserve that strength while making the current-state comparison materially more decision-useful.
