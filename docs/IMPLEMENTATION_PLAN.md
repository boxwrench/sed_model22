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

Status: in progress

Tasks:

- [x] add mass-conservation checks
- [x] add an empty rectangular basin verification case
- [x] add a single-baffle verification case
- [ ] add mesh sensitivity smoke checks
- [x] connect solver outputs to comparison-ready engineering metrics
- [x] add a simple multi-scenario comparison workflow

Definition of done:

- the first solver has basic credibility checks
- output summaries can distinguish between simple geometry cases
- at least one comparison-oriented workflow exists for alternative configurations

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

1. Build or refine better test models chosen for hydraulic and visualization legibility, not just basic solver coverage.
2. Refine the accepted particle-pathline preview with detention-based time compression, better seeding, and cleaner presentation styling.
3. Keep static streamline still export aligned as the paired report-facing figure.
4. Add mesh sensitivity smoke checks against the current V0.1 solver.
5. Add more comparison-oriented engineering metrics and scenario summaries.
6. Keep `docs/research/CANON.md` aligned with whatever the next solver boundary becomes.

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
6. Run the current smoke tests:
   - `PYTHONPATH=src python3 -m unittest discover -s tests -v`

## Current Constraints

- The repo should stay custom-Python-first.
- The first interface remains CLI + YAML.
- External solvers are supporting references, not the mainline architecture.
- Avoid adding tracer, solids, or digital-twin behavior before the V0.1 hydraulic core is stable.
