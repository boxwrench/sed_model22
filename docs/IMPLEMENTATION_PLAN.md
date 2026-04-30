# Implementation Plan

This is the working task list for the repo. It should answer two questions quickly:

- what is done
- what should happen next when work resumes

Update this file when a milestone starts, finishes, or changes shape.

## Current Status

Project state:

- repo scaffold is complete
- research notes are organized and indexed
- CLI/config/run-artifact workflow exists
- first real hydraulic screening solve exists
- repo also now has an early run-bundle media path, voxel still generation, and first-pass preview-video generation
- the visualization research pass is now in and the first accepted animation direction is deterministic particle pathlines
- static streamline stills are the accepted report companion
- detention-based time compression is now an accepted requirement for short basin previews
- study-level media packaging now exists for `compare-study` outputs
- a geometry intake template now exists under `templates/` for drawing-to-scenario capture
- the next-fidelity direction is now documented in `docs/V0_3_ROADMAP.md`
- the current `v0.2` blocked-wall scenario now uses provisional explicit top/bottom bypass openings instead of a nearly closed perforated-wall proxy
- dye-pulse and more elaborate visualization methods remain deferred until their proxy framing is clearly bounded

Current implementation target:

- dual screening workflows:
  - `v0.1` plan-view hydraulic sandbox
  - `v0.2` longitudinal design-vs-current comparison workflow
- structured Cartesian grid
- YAML scenario input
- CLI-driven workflow

Latest verification checkpoint:

- `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- latest full-suite checkpoint: 34 passing tests on 2026-03-29
- latest full-suite checkpoint on 2026-04-11:
  - `python -m unittest discover -s tests -v`
  - 45 passing tests on the current machine
- latest focused M4 verification checkpoint on 2026-04-11:
  - `python -m unittest tests.test_solver_verification tests.test_longitudinal_solver_verification tests.test_metrics tests.test_mesh_sensitivity -v`
  - 9 passing tests covering solver verification, synthetic metric correctness, and v0.2 mesh-sensitivity smoke checks
- latest explicit-bypass checkpoint on 2026-04-11:
  - `python -m unittest tests.test_config_v2 tests.test_longitudinal_solver tests.test_study tests.test_mesh_sensitivity tests.test_voxel_visualization -v`
  - 18 passing tests covering schema support, explicit bypass routing, study/report wording, mesh-direction stability, and visualization labels
- media and CLI subsets were rechecked during preview-animation work on 2026-03-27:
  - `python -m unittest tests.test_media -v`
  - `python -m unittest tests.test_cli -v`

## Milestones

### M0. Repo Foundation

Status: done

Tasks:

- [x] initialize git repo and basic project structure
- [x] move research archive into `docs/research/source-notes/`
- [x] add `README.md`, `pyproject.toml`, `.gitignore`
- [x] create package skeleton under `src/sed_model22/`
- [x] add CLI scaffold
- [x] add baseline scenario
- [x] add smoke tests

### M1. Research Synthesis

Status: done

Tasks:

- [x] create a canonical synthesis doc for V0.1 implementation assumptions
- [x] record which research notes are implementation-canonical
- [x] capture important disagreements or alternate assumptions across overlapping AI-generated notes
- [x] define explicit V0.1 in-scope vs out-of-scope physics

Definition of done:

- one short canonical doc exists for solver work
- V0.1 scope can be implemented without rereading the full archive

### M2. Scenario Schema Expansion

Status: done

Tasks:

- [x] add explicit inlet configuration to scenario schema
- [x] add explicit outlet configuration to scenario schema
- [x] add wall and baffle boundary behavior fields
- [x] add bed slope or flat-bed assumption field
- [x] add solver control fields for pseudo-time stepping and convergence
- [x] add tests for valid and invalid boundary configurations

Definition of done:

- the YAML schema is sufficient to drive a first hydraulic solve
- boundary assumptions are explicit instead of implied

### M3. Structured Hydraulic Core

Status: done

Tasks:

- [x] define the solver state arrays and data flow
- [x] implement empty-basin structured-grid hydraulic update loop
- [x] implement basic boundary conditions for inflow, outflow, and walls
- [x] support full-depth solid baffles only for the first pass
- [x] write velocity and summary artifacts into the existing run directory structure
- [x] keep the first solver narrow and transparent rather than feature-rich

Definition of done:

- `run-hydraulics` performs a real solve for the simplest supported case
- results can be inspected without changing repo structure again

### M4. Verification and Engineering Metrics

Status: done

Tasks:

- [x] add mass-conservation checks
- [x] add an empty rectangular basin verification case
- [x] add a single-baffle verification case
- [x] add mesh sensitivity smoke checks (v0.2 geometry; prerequisite for V0.3)
- [x] connect solver outputs to comparison-ready engineering metrics
- [x] add a simple multi-scenario comparison workflow
- [x] document RTD proxy constants and plate-settler conductance minimums (solver/longitudinal.py)
- [x] add shared color scale for comparison renders (render_still.py passes shared_vmax)
- [x] add solver verification tests against known analytical solutions
  - v0.1: mass balance in empty basin, symmetric flow in symmetric basin
  - v0.2: uniform conductance → expected head gradient; perforated baffle → reduced downstream velocity
  - target: ≥3 physics-meaningful assertions per solver, runs in <30s total
  - files: tests/test_solver_verification.py, tests/test_longitudinal_solver_verification.py
- [x] add metrics unit tests with synthetic inputs
  - cover dead zone fraction, velocity uniformity index, Morrill index
  - fast, isolated, formula-correctness focused (no full solver run required)
  - file: tests/test_metrics.py
- [x] add function-level docstrings to solver code
  - state the PDE being solved (Laplace ∇²h = 0) and iteration scheme (Gauss-Seidel with SOR)
  - files: src/sed_model22/solver/hydraulics.py, src/sed_model22/solver/longitudinal.py, src/sed_model22/metrics/longitudinal.py

Definition of done:

- solvers have basic credibility checks and pass verification tests against known solutions
- metrics are unit-tested with synthetic inputs
- solver code is self-documenting enough to audit without reverse-engineering the physics
- output summaries can distinguish between simple geometry cases
- at least one comparison-oriented workflow exists for alternative configurations

**M4 is complete.** The hydraulic baseline now has the planned credibility checks required to begin the next geometry-fidelity pass.

### M5. Tracer and Residence-Time Layer

Status: later

Tasks:

- [ ] add passive tracer transport on top of the hydraulic field
- [ ] produce RTD-oriented outputs
- [ ] add hydraulic efficiency and short-circuiting metrics

### M6. Simplified Solids Layer

Status: later

Tasks:

- [ ] add settling proxy terms
- [ ] support a small number of solids classes
- [ ] add simple solids-escape risk indicators

## Pickup Queue

If work resumes after a break, do these next in order:

1. Replace the provisional current-state bypass-opening dimensions with translated intake-survey / field-verified geometry and rerun the shipped design-versus-current study on that revised case.
2. Add the formal run-quality / confidence tier outlined in `docs/V0_3_ROADMAP.md` so directional-only runs are labeled consistently across summaries, reports, and media.
3. Keep improving the study-level media package, especially a flow-level landing page across low / typical / high flow.
4. Start the limited multi-class solids design work defined in `docs/V0_3_ROADMAP.md` once the current-state bypass geometry is verified enough to treat as the hydraulic baseline.
5. Keep `docs/research/CANON.md` and the roadmap docs aligned with the active solver boundary.

## Session Restart Checklist

Before starting the next work block:

1. Read `docs/DEVLOG.md`.
2. Read `docs/research/PRIMER.md`.
3. Read `docs/research/CANON.md`.
4. Read this file.
5. Open the current canonical implementation references:
   - `docs/research/source-notes/sed_floc_basin_simulator_master_package.md`
   - `docs/research/source-notes/2D hydraulic simulator.md`
   - `docs/research/source-notes/Minimum viable physics.md`
6. Read `docs/V0_3_ROADMAP.md` if the next session is about bypass geometry, solids consequence work, or the next fidelity jump.
7. Review `templates/intake_geometry_survey.yaml` before translating new drawing-derived geometry.
8. Run the current smoke tests:
   - `PYTHONPATH=src python3 -m unittest discover -s tests -v`

## Current Constraints

- The repo should stay custom-Python-first.
- The first interface remains CLI + YAML.
- External solvers are supporting references, not the mainline architecture.
- Avoid adding tracer, solids, or digital-twin behavior before the V0.1 hydraulic core is stable.
