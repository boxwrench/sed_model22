# Implementation Plan

This is the working task list for the repo. It should answer two questions quickly:

- what is done
- what should happen next when work resumes

Update this file when a milestone starts, finishes, or changes shape.

For the fastest orientation, read `docs/SESSION_START_CONTEXT.md` first and `docs/ROADMAP.md` second.

## Current Status

Project state:

- repo scaffold is complete
- research notes are organized and indexed
- CLI/config/run-artifact workflow exists
- first real hydraulic screening solve exists
- run-bundle media path, voxel still generation, and preview-video generation exist
- deterministic particle pathlines are the accepted first animation direction
- static streamline stills are the accepted report companion
- study-level media packaging exists for `compare-study`
- a geometry intake template exists under `templates/` for drawing-to-scenario capture
- `v0.1` plan-view and `v0.2` longitudinal workflows both exist
- `v0.3` is now narrowed to explicit bypass hydraulics
- solids consequence modeling is deferred to `v0.4`

Current implementation target:

- start `v0.3` explicit bypass hydraulics on top of the completed M4 credibility baseline
- keep the first interface CLI + YAML
- make outputs useful for plant operations, legible to operators, legible to managers, and suitable for portfolio review
- preserve transparent screening claims rather than implying CFD, calibration, or digital-twin behavior

Latest verification checkpoint:

- `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- latest full-suite checkpoint: 41 passing tests outside sandbox at the latest code checkpoint
- media and CLI subsets were rechecked during preview-animation work on 2026-03-27:
  - `python -m unittest tests.test_media -v`
  - `python -m unittest tests.test_cli -v`

Current risk:

- the shipped `v0.2` design-vs-current study is workflow-valid but numerically weak
- convergence and discharge-balance issues mean the current study remains correctly labeled `weak` under the current quality-tier rules
- current-state bypass geometry is not verified and is still represented by proxy geometry

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

Definition of done:

- repo has a coherent package, docs, scenarios, and tests structure

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

### M4. Credibility Hardening

Status: done

This milestone gated `v0.3`. The baseline hardening work is now in place, and the next active work belongs in bypass hydraulics rather than more generic solver polish.

Tasks:

- [x] add mass-conservation checks
- [x] add an empty rectangular basin verification case
- [x] add a single-baffle verification case
- [x] connect solver outputs to comparison-ready engineering metrics
- [x] add a simple multi-scenario comparison workflow
- [x] document RTD proxy constants and plate-settler conductance minimums in solver code
- [x] add shared color scale for comparison renders
- [x] add solver verification tests against known analytical solutions
  - `v0.1`: mass balance in empty basin, symmetric flow in symmetric basin
  - `v0.2`: uniform conductance gives expected head gradient; perforated baffle reduces downstream velocity
  - target: at least 3 physics-meaningful assertions per solver, runs in under 30 seconds total
  - expected files: `tests/test_solver_verification.py`, `tests/test_longitudinal_solver_verification.py`
- [x] add metrics unit tests with synthetic inputs
  - cover dead zone fraction, velocity uniformity index, and Morrill index
  - fast, isolated, formula-correctness focused
  - expected file: `tests/test_metrics.py`
- [x] add function-level docstrings to solver code
  - name the governing screening equation or proxy being solved
  - state the iteration scheme and convergence criteria
  - expected files: `src/sed_model22/solver/hydraulics.py`, `src/sed_model22/solver/longitudinal.py`, `src/sed_model22/metrics/longitudinal.py`
- [x] add mesh sensitivity smoke checks for the current `v0.2` comparison geometry
  - check transition headloss, post-transition velocity uniformity, launder peak upward velocity, `t10`, `t50`, `t90`, and short-circuiting index
- [x] design and implement run quality tiers
  - add `run_quality_tier`
  - add `quality_reasons`
  - report `credible`, `directional_only`, or `weak`
  - ensure weak runs are visibly labeled in summaries and study reports

Definition of done:

- solvers have basic credibility checks and pass verification tests against known solutions
- metrics are unit-tested with synthetic inputs
- solver code is self-documenting enough to audit without reverse-engineering the physics
- output summaries distinguish credible, directional, and weak runs
- the shipped `v0.2` study cannot silently present weak numerical results as strong conclusions

### v0.3. Explicit Bypass Hydraulics

Status: active

Goal:

- represent the current-state bypass flow path explicitly instead of relying on a lossy blocked-wall proxy

Tasks:

- [ ] verify current-state bypass geometry before encoding it
- [ ] extend scenario schema for explicit bypass-path geometry
- [ ] support over, under, side, or serpentine path descriptions where the verified geometry requires them
- [ ] route flow through the explicit path in the longitudinal solver
- [ ] add study support for design/current/proposed N-way comparisons
- [ ] add `baseline_case_label` while preserving current first-case baseline behavior
- [ ] refresh the current-state scenario and rerun low, typical, and high-flow comparisons
- [ ] update report interpretation after the revised geometry changes direction or magnitude

Definition of done:

- the current-state model represents the dominant real flow path in geometry
- design/current/proposed comparison can be run reproducibly
- outputs remain operator-readable, manager-readable, and quality-tiered

### v0.4. Limited Solids Consequences

Status: later

Goal:

- add class-based settling-risk outputs only after hydraulics and bypass geometry are credible

Tasks:

- [ ] define 3 to 5 transparent settling classes
- [ ] add class-specific capture or escape risk proxies
- [ ] carry solids consequence outputs through run summaries and study reports
- [ ] label solids results as screening consequences, not calibrated removal predictions

Definition of done:

- solids outputs help explain likely operational consequence without claiming calibrated turbidity or finished-water prediction

### Later Operational Expansion

Status: later

Possible tasks:

- [ ] study-level landing page across low, typical, and high flow
- [ ] pseudo-transient flow sweeps
- [ ] interactive review pages using media scene contracts
- [ ] field-informed validation loop
- [ ] external CFD comparison for validation context
- [ ] SCADA or real-time integration only after validation supports it

## Pickup Queue

If work resumes after a break, do these next in order:

1. Verify current-state bypass geometry before encoding it.
2. Extend the scenario schema for explicit bypass-path geometry.
3. Implement explicit bypass routing in the longitudinal solver.
4. Add `baseline_case_label` and N-way design/current/proposed comparison support.
5. Refresh the current-state scenario and rerun low, typical, and high-flow studies.
6. Update interpretation and media/report language against the revised geometry and resulting quality tiers.
7. Defer solids consequence modeling to `v0.4`.
8. Keep `docs/SESSION_START_CONTEXT.md`, `docs/ROADMAP.md`, and this file aligned as the product boundary changes.

## Session Restart Checklist

Before starting the next work block:

1. Read `docs/SESSION_START_CONTEXT.md`.
2. Read `docs/ROADMAP.md`.
3. Read this file.
4. Read `docs/research/CANON.md` only when implementation details require the research basis.
5. Read `docs/V0_3_ROADMAP.md` when planning or implementing bypass hydraulics.
6. Review `templates/intake_geometry_survey.yaml` before translating drawing-derived geometry.
7. Run the current smoke tests:
   - `PYTHONPATH=src python3 -m unittest discover -s tests -v`

## Current Constraints

- The repo should stay custom-Python-first.
- The first interface remains CLI + YAML.
- External solvers are supporting references, not the mainline architecture.
- Avoid adding tracer, solids, or digital-twin behavior beyond the explicit milestone boundary.
- Avoid new media polish until solver credibility and current-state geometry are strong enough.
