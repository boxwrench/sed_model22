# V0.3 Roadmap

This document defines the next major product step after the current `v0.2` design-versus-current comparison workflow.

The central `v0.3` move is not "more equations" for their own sake. The central move is from proxy-only hydraulic comparison toward a more decision-complete workflow that can connect the current-state flow path to likely removal consequences without pretending the repo is already a full CFD or plant digital twin.

## Product Goal

`v0.3` should answer a more useful question than `v0.2`:

- not only "how did the hydraulics change"
- but also "how might those hydraulic changes affect likely solids escape or removal"

That only becomes credible if the current-state geometry is represented honestly first.

Working rule:

- verified explicit bypass geometry before solids consequence modeling
- modest solids classes before pseudo-transient or 3D ambitions
- preserve the repo's current honesty about screening scope and uncertainty

## Must Have

### 1. Verify and Refine Explicit Current-State Bypass Geometry

The current blocked-wall basin now includes provisional explicit top/bottom bypass openings, but those dimensions still need to be reconciled against the translated intake survey and any field observations.

Required outcome:

- replace the provisional openings with verified current-state geometry
- let the solver route flow through that verified path directly
- update the current-state scenario and study outputs so the dominant hydraulic feature is both explicit and defensible

Why this is first:

- if the bypass path is wrong, then downstream redistribution, launder approach, and later solids conclusions will all be built on the wrong hydraulic picture

### 2. Extend Schema Support Only Where Verified Geometry Demands It

The repo already has baseline `bypass_opening` support. Extend it only if the translated geometry requires more detail than the current provisional openings capture.

Minimum fields should support:

- path type: `over`, `under`, `side`, `serpentine`, or equivalent explicit geometry features
- `x` extent
- `z` extent
- effective opening area or open fraction where needed
- design versus current-state distinction where that matters

This should stay CLI/YAML-first and remain readable to humans.

### 3. Refine Solver Support for Verified Bypass Routing

The longitudinal solver already supports simple explicit bypass openings. The next refinement is to make sure the routing matches the verified current-state path closely enough for the next study baseline.

In scope:

- explicit over/under path representation on the structured `x-z` grid
- updated flow redistribution around the blocked wall
- updated headloss and downstream uniformity response

Out of scope:

- 3D flow
- full transient hydraulics
- CFD-level turbulence closure

### 4. Re-Baseline the Design-vs-Current Study

Once the geometry changes are in, rerun the shipped study at low, typical, and high flow and update the comparison outputs.

Required outputs:

- updated run bundles
- updated comparison report
- updated study media packages
- updated interpretation text where the direction or magnitude of the comparison changes

### 5. Mesh Sensitivity Checks on the Revised Geometry

Add mesh sensitivity smoke checks for the revised `v0.2`/`v0.3` geometry.

At minimum, check stability of:

- transition headloss
- post-transition velocity uniformity index
- launder peak upward velocity proxy
- `t10`, `t50`, and `t90`
- short-circuiting index

The goal is not publication-grade verification. The goal is enough stability to support screening decisions honestly.

## Should Have

### 1. Limited Multi-Class Solids Model

After the bypass geometry is represented explicitly, add a modest solids layer.

Start small:

- 3 to 5 discrete settling classes
- fast-settling flocs
- typical flocs
- slow-settling or "pin" flocs

Prefer transparent class-based transport over a broad, hard-to-defend solids framework.

### 2. Solids-Consequence Outputs

Add study-facing outputs that move beyond pure hydraulic proxies.

Candidate outputs:

- class-specific capture fraction
- class-specific launder escape fraction
- basin-level removal proxy
- case-to-case delta in likely solids escape risk

These should remain labeled as screening outputs unless later validation supports stronger claims.

### 3. Visual Overlays for Solids Consequence

The media/report layer should show not only hydraulic differences but also likely consequence for the slowest-settling material.

This is the first likely leadership-facing visual that becomes closer to:

- "this current-state path is more likely to move vulnerable solids toward the launder"

than to:

- "here is a velocity map"

### 4. Formal Run-Quality Tier

Add a formal run-quality or confidence tier and carry it through:

- run summary
- manifests
- comparison report
- study media package

Suggested first tiers:

- `credible`
- `directional_only`
- `weak`

This should encode what the repo already does informally with caution language.

## Later

### 1. Pseudo-Transient Flow Stepping

Allow coarse time-varying flow stepping, such as a diurnal curve with hourly steps.

Why later:

- a steady model with the right current-state geometry is more valuable than a pseudo-transient model with the wrong flow path

### 2. Plate-Settler Momentum Refinement

Move the plate-settler representation toward a more physically grounded resistance model, potentially with Reynolds-dependent behavior inside the plate channels.

Why later:

- it matters
- but the transition-wall/bypass representation is the bigger current uncertainty

### 3. Interactive Study Viewer

Build on the current `visual_scene.json` contract to support interactive HTML review.

This should remain a media-layer feature, not a solver concern.

### 4. Field-Informed Validation Loop

Use whatever becomes available later:

- headloss observations
- tracer observations
- operator observations
- performance trends

to tighten confidence in the screening workflow.

## Pre-V0.3 Engineering Hardening

These items came from a project review (April 2026) and were required before V0.3 solver work began.
They are now complete and remain listed here so the gating logic stays explicit.

**Required before V0.3 schema work starts:**

- Solver verification tests against known analytical solutions (v0.1 and v0.2)
- Metrics unit tests with synthetic inputs (dead zone fraction, uniformity index, Morrill index)
- Function-level docstrings in solver files naming the PDE and iteration scheme
- Mesh sensitivity smoke checks on current v0.2 comparison geometry

**Should-do alongside V0.3 (medium priority):**

- Prescriptive validation error messages — wrap raw Pydantic errors with field path + suggested fix
  (files: `src/sed_model22/cli.py`, `src/sed_model22/config.py`)
- Extract HTML templates from Python string literals to `src/sed_model22/templates/`
  (currently: 864-line operator report in `viz/operator_report.py`, 230-line layout in `media/layouts.py`)
- Define a `SolverProtocol` ABC before a third solver is added
  (file: `src/sed_model22/solver/protocol.py`)
- Refactor `study.py` to support N-way comparison (not just 2 cases)
  — the design-spec / current-state / proposed-fix workflow will need 3 cases

**Backlog (lower priority, after V0.3):**

- `stderr` progress logging at key solver stages (mesh built, converged, artifacts written)
- Rename `operator_report.html` → `engineering_screening_report.html` (content is engineering diagnostics, not operator guidance)
- Parametrized tests across low / typical / high flow rates
- Getting-started guide (`docs/GETTING_STARTED.md`) and metrics reference (`docs/METRICS_REFERENCE.md`)

## Recommended Execution Order

0. Complete pre-V0.3 engineering hardening (see above).
1. Extend schema for bypass-path geometry.
2. Implement explicit bypass-path solver support.
3. Refresh the current-state scenario using the cleaned intake geometry workflow.
4. Re-run design-versus-current studies and visuals.
5. Add mesh sensitivity smoke checks on the revised geometry.
6. Add a limited multi-class solids layer.
7. Add solids comparison metrics and leadership-facing consequence visuals.
8. Only then consider pseudo-transient stepping.

## Definition of V0.3

`v0.3` is complete when the repo provides:

- explicit current-state bypass geometry
- updated hydraulic comparison on that geometry
- limited multi-class solids consequence outputs
- study-level visual outputs that connect hydraulic change to likely removal consequence

`v0.3` is not:

- 3D CFD
- a calibrated digital twin
- full water-quality prediction
- a full transient plant simulator

## Working Constraint

Do not let the visual or numerical sophistication outrun representational honesty.

The repo's strength is that it is understandable, inspectable, and explicit about what is proxy versus what is more physically grounded.

`v0.3` should preserve that strength while making the current-state comparison materially more decision-useful.
