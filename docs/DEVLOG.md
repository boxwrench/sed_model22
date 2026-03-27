# Development Log

This log is meant to stay short, chronological, and implementation-facing. Each entry should capture the repo state change, the reason for it, and the next immediate move.

## 2026-03-27

### V0.2 Product Direction and Handoff

What changed:

- locked the repo's next major target as a practical design-spec versus current-state basin comparison workflow
- defined the concrete first question around the blocked perforated transition wall and its hydraulic consequences
- added `docs/V0_2_IMPLEMENTATION_HANDOFF.md` as the explicit executor-facing V0.2 implementation spec
- updated the project README and docs language to describe the work as a practical decision-support tool, not just a solver experiment
- made the repo narrative more legible for operators, engineers, and non-specialist decision-makers while keeping the technical implementation boundary explicit

Why:

- the project has moved past proof-of-concept curiosity and now has a real plant-facing question to answer
- the next implementation step needed to be framed around a decision-useful product, not only around solver fidelity
- the repo documentation needed to communicate both practical usefulness and long-term ambition without turning into marketing language

Verification:

- docs update only
- no code tests run for this entry

Next:

- generate a targeted research memo on perforated-baffle and plate-settler modeling fidelity
- execute the V0.2 handoff in code
- keep the implementation practical, legible, and useful to operations while preserving technical honesty

### Research Review: Keep Current V0.2 Boundary

What changed:

- reviewed and archived the research memo at `docs/research/PERFORATED_BAFFLE_AND_PLATE_SETTLER_MODELING_MEMO.md`
- recorded that the memo is informative for future fidelity decisions but does not change the current `v0.2` proof-of-concept pass
- captured the important plant note that the blocked-wall current state still allows flow through a serpentine over-under path

Why:

- the research is useful, but the current pass is primarily about proving the workflow and decision-support procedure
- jumping to a 3D CFD-first approach would break the intended speed, scope, and transparency boundary for the current build
- future versions need a more exact current-state geometry and bypass-path representation than the current proof-of-concept requires

Verification:

- docs update only
- no code tests run for this entry

Current interpretation:

- keep `v0.2` as the current low-fidelity comparison workflow
- use the research memo to guide later fidelity upgrades, not to reset the present milestone
- treat explicit orifice geometry, exact dimensions, and full bypass-path reconstruction as later-version work

Next:

- finish stabilizing the current `v0.2` implementation
- capture the real current-state over-under flow path and wall details for a later geometry-verification pass
- decide later whether the next fidelity jump is explicit orifice geometry, stronger porous-zone calibration, or field validation first

## 2026-03-25

### V0.1 Screening Solver Checkpoint

What changed:

- completed the transition from scaffold-only hydraulics to a real steady screening-flow solve
- wired the run pipeline to write `fields.json` plus layout and velocity SVG outputs
- expanded schema tests to match the richer inlet/outlet and solver-control model
- added solver tests for empty-basin behavior, baffle-induced transverse flow, and placeholder-baffle handling
- refreshed README and docs status text to describe the repo as a real first-solver checkpoint

Why:

- the repo needed to move from architecture-only work to actual executable basin behavior
- the schema changes needed to be exercised by a real solver, not just validation code
- the docs needed to stop describing the project as scaffold-only

Verification:

- `PYTHONPATH=src python3 -m unittest discover -s tests -v` passed with 10 tests

Current boundary:

- steady screening-flow only
- structured Cartesian grid only
- opposite-side inlet/outlet pairs only
- impermeable walls and full-depth solid baffles only

Next:

- add mesh sensitivity smoke checks
- add scenario-comparison metrics
- decide whether the next step is tracer transport or a more physical hydraulic core

## 2026-03-24

### Repository Bootstrap

What changed:

- initialized the folder as a git repository on `main`
- moved the original research bundle into `docs/research/source-notes/`
- created the top-level project structure for `docs/`, `src/`, `scenarios/`, and `tests/`
- added `pyproject.toml`, `.gitignore`, and a root `README.md`
- created the `sed_model22` package skeleton with modules for config, geometry, mesh, solver, metrics, visualization, transport, and run management
- added a CLI with `validate`, `run-hydraulics`, `summarize`, and `plot`
- added a baseline YAML scenario and smoke tests

Why:

- the repo was a flat document bundle with no package boundary
- the project needed a stable structure before solver work starts
- the first useful interface is CLI + YAML scenarios, not a notebook or UI

Verification:

- `python3 -m unittest discover -s tests -v` passed
- `PYTHONPATH=src python3 -m sed_model22 validate scenarios/baseline_rectangular_basin.yaml` passed

### Research Navigation Layer

What changed:

- added `docs/README.md` as the documentation hub
- added `docs/research/PRIMER.md` as the research table of contents and quick-reference guide
- updated the root `README.md` to point at the docs hub, dev log, and research primer

Why:

- the research set is broad and partially overlapping
- the repo needed a fast way to answer “which doc should I read for this question?”
- future implementation work needs a canonical reading path instead of repeatedly scanning the full archive

Current canonical references:

- `docs/research/source-notes/sed_floc_basin_simulator_master_package.md`
- `docs/research/source-notes/2D hydraulic simulator.md`
- `docs/research/source-notes/Minimum viable physics.md`
- `docs/research/source-notes/Water_Treatment_Plant_Technical_Specifications.md`

### Persistent Implementation Plan

What changed:

- added `docs/IMPLEMENTATION_PLAN.md`
- defined milestones from repo foundation through hydraulics, verification, tracer, and solids
- added a pickup queue for the next session
- added a session restart checklist so work can resume without rebuilding context

Why:

- the repo needs a stable task list between work sessions
- the next steps are clear enough to structure now
- implementation work should be resumable without rereading the full archive

### Canonical V0.1 Basis

What changed:

- added `docs/research/CANON.md` as the implementation-facing V0.1 synthesis
- expanded the scenario schema to include explicit inlet, outlet, boundary, bed, and solver-control sections
- updated the baseline scenario and added an empty-basin verification scenario

Why:

- solver work needed a tighter implementation basis than the broader research primer
- the previous schema was too thin for a real hydraulic run
- the repo needed a clean implementation boundary before the first actual flow solution

Next at that time:

- implement the first real hydraulic solve against the new schema
- add verification cases for the new solver
- update the docs once scaffold-only language no longer applies
