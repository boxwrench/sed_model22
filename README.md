# sed_model22

`sed_model22` is an operator-centered basin simulation project for practical comparison of rectangular sedimentation and flocculation basin behavior. The near-term goal is to help plant staff compare what a basin was designed to do versus what it is doing now in a way that is technically honest, operationally legible, and useful for real decisions. Long term, if the approach proves credible, it should become a transparent basin-screening workflow that can be useful beyond one plant and eventually useful across a broader agency or industry context.

## Current Focus

The current implementation now carries two practical screening workflows:

- research material preserved under `docs/research/`
- canonical project docs under `docs/architecture/`
- Python package and CLI workflow under `src/sed_model22/`
- `v0.1` plan-view hydraulic screening for basin-layout and operator-facing checks
- `v0.2` longitudinal `length x depth` screening for design-vs-current comparison
- deterministic run artifacts for validation, review, and comparison reporting

The current `run-hydraulics` command is model-aware. It validates a scenario, runs either the `v0.1` plan-view or `v0.2` longitudinal screening path, and writes a reproducible run bundle with field outputs, SVG plots, and a voxel-style media bundle. The current `compare-study` command runs case-by-flow comparisons and writes JSON, CSV, and Markdown comparison artifacts. This remains a screening tool, not full CFD, full transient transport, or solids transport.

## Product Direction

The next product step is not a generic solver upgrade for its own sake. It is a practical design-vs-current comparison workflow aimed at a real plant question:

- what did the blocked perforated transition wall change hydraulically
- how does the current basin differ from the design-intent basin
- are there visible changes in redistribution, short-circuiting risk, plate-settler approach conditions, or launder/upwelling risk

The tool should stay understandable to operators, engineers, and non-specialist decision-makers. The target is not physics-perfect modeling. The target is a transparent model that is good enough to change or support a real engineering decision.

## Current Status

As of 2026-03-27, the repo is at a usable first-solver checkpoint with a defined V0.2 product direction:

- schema and scenario structure support both `v0.1` scenarios and `v0.2` comparison scenarios
- `run-hydraulics` produces reproducible run bundles for both model forms
- run bundles now include a default voxel still and best-effort preview-media bundle under `media/`
- `v0.1` now also includes a first accepted particle-pathline preview prototype plus paired streamline still output
- `v0.2` outputs include longitudinal fields, RTD proxy artifacts, and comparison-study reporting
- plot outputs include layout, velocity magnitude, tracer breakthrough, and the existing operator report path for `v0.1`
- shipped scenarios include an SVWTP design-spec vs blocked-wall study for low, typical, and high flow screening

Current supported solver boundary:

- structured Cartesian grid only
- steady deterministic screening-flow solve, not full shallow-water or CFD physics
- `v0.1`: opposite-side inlet/outlet pairs and full-depth solid baffles only
- `v0.2`: conductance-based perforated-baffle, plate-settler, and launder proxy representation
- RTD behavior in `v0.2` is currently a deterministic proxy layer, not explicit transient transport
- short preview animations may use compressed model time for readability and must label that explicitly

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
- `validate-study <study>`: validate a comparison study YAML file
- `run-hydraulics <scenario>`: materialize a hydraulic run directory with mesh, fields, summary, SVG artifacts, and run media
- `run-hydraulics --media-policy {off,still_only,best_effort_preview,require_preview}`: control voxel and preview generation; current default is `best_effort_preview`
- `summarize <run_dir>`: print a concise run summary
- `plot <run_dir>`: regenerate the layout and velocity SVGs from the run snapshot
- `compare-study <study>`: run a case-by-flow study and write comparison outputs

## Immediate Next Step

The immediate next step is to keep tightening the practical `v0.2` screening workflow around the real basin question: design-spec versus current-state behavior, especially the hydraulic effect of the blocked transition wall, while staying explicit about what is still a proxy and what belongs in later higher-fidelity versions.
