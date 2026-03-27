# sed_model22

`sed_model22` is an operator-centered basin simulation project for practical comparison of rectangular sedimentation and flocculation basin behavior. The near-term goal is to help plant staff compare what a basin was designed to do versus what it is doing now in a way that is technically honest, operationally legible, and useful for real decisions. Long term, if the approach proves credible, it should become a transparent basin-screening workflow that can be useful beyond one plant and eventually useful across a broader agency or industry context.

## Current Focus

The current implementation is a working V0.1 proof-of-concept baseline:

- research material preserved under `docs/research/`
- canonical project docs under `docs/architecture/`
- Python package skeleton under `src/sed_model22/`
- CLI + YAML scenario workflow for early development
- screening-flow run artifacts for validation, layout generation, and repo smoke tests
- a first real structured-grid hydraulic screening solve

The current `run-hydraulics` command validates a scenario, solves a steady screening-flow field on a structured grid, and writes a reproducible run bundle with field outputs and SVG plots. It is intentionally not full CFD, tracer transport, or solids transport yet.

## Product Direction

The next product step is not a generic solver upgrade for its own sake. It is a practical design-vs-current comparison workflow aimed at a real plant question:

- what did the blocked perforated transition wall change hydraulically
- how does the current basin differ from the design-intent basin
- are there visible changes in redistribution, short-circuiting risk, plate-settler approach conditions, or launder/upwelling risk

The tool should stay understandable to operators, engineers, and non-specialist decision-makers. The target is not physics-perfect modeling. The target is a transparent model that is good enough to change or support a real engineering decision.

## Current Status

As of 2026-03-27, the repo is at a usable first-solver checkpoint with a defined V0.2 product direction:

- schema and scenario structure are explicit enough for real hydraulic runs
- `run-hydraulics` produces `summary.json`, `mesh.json`, `metrics.json`, and `fields.json`
- plot outputs include basin layout and velocity magnitude SVGs
- verification coverage includes schema validation, CLI wiring, empty-basin behavior, and a baffle case
- the next major implementation target is a longitudinal design-vs-current comparison workflow

Current supported solver boundary:

- structured Cartesian grid only
- opposite-side inlet/outlet pairs only
- impermeable walls
- full-depth solid baffles only
- steady screening-flow solve, not full shallow-water or CFD physics

## Repository Layout

- `docs/research/source-notes/`: preserved legacy research and supporting references
- `docs/architecture/`: canonical repo structure, roadmap, and decisions
- `docs/README.md`: documentation hub, dev log, and research primer entrypoint
- `scenarios/`: example YAML scenarios
- `src/sed_model22/`: package code
- `tests/`: smoke tests for config, mesh, and CLI behavior

## Documentation Guide

Start with these:

- `docs/README.md` for the docs hub
- `docs/DEVLOG.md` for project progress
- `docs/IMPLEMENTATION_PLAN.md` for milestone status and pickup tasks
- `docs/V0_2_IMPLEMENTATION_HANDOFF.md` for the detailed executor-facing V0.2 spec
- `docs/research/CANON.md` for the implementation-facing V0.1 basis
- `docs/research/PRIMER.md` for the research table of contents and reading guide

## Quickstart

Use the package directly from source:

```bash
PYTHONPATH=src python3 -m sed_model22 validate scenarios/baseline_rectangular_basin.yaml
PYTHONPATH=src python3 -m sed_model22 run-hydraulics scenarios/baseline_rectangular_basin.yaml
```

Or install it locally later and use the console script:

```bash
python3 -m pip install -e .
sed-model validate scenarios/baseline_rectangular_basin.yaml
```

## Initial Commands

- `validate <scenario>`: validate YAML against the current scenario schema
- `run-hydraulics <scenario>`: materialize a hydraulic run directory with mesh, fields, summary, and SVG artifacts
- `summarize <run_dir>`: print a concise run summary
- `plot <run_dir>`: regenerate the layout and velocity SVGs from the run snapshot

## Immediate Next Step

The next implementation step is to execute the V0.2 handoff: add a longitudinal design-vs-current comparison workflow with porous transition-wall modeling, plate-settler zone representation, tracer/RTD proxy outputs, and a study report that is practical enough to discuss with both operators and non-specialist stakeholders.
