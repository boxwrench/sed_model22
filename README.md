# sed_model22

`sed_model22` is an operator-centered basin screening project for practical comparison of rectangular sedimentation and flocculation basin behavior. The near-term goal is to help plant staff compare design-intent and current-state basin behavior in a way that is technically honest, operationally legible, and useful for real decisions.

The project is a transparent screening workflow. It is not a CFD replacement, calibrated digital twin, real-time operations system, or full solids-transport model.

## Start Here

Read these first:

1. `docs/SESSION_START_CONTEXT.md` for fast restart context, current risks, commands, and the next safe work.
2. `docs/ROADMAP.md` for the canonical product roadmap by usable plateau.
3. `docs/IMPLEMENTATION_PLAN.md` for the active engineering pickup queue.
4. `docs/V0_3_ROADMAP.md` only after M4 hardening is complete or when planning explicit bypass hydraulics.

## Current Focus

The repo currently carries two screening workflows:

- `v0.1` plan-view hydraulic screening for simple basin-layout checks
- `v0.2` longitudinal `length x depth` screening for design-vs-current comparison

The active focus is M4 credibility hardening:

- solver verification tests
- synthetic metrics unit tests
- solver and metrics docstrings
- mesh sensitivity smoke checks
- formal run quality tiers such as `credible`, `directional_only`, and `weak`

Do not start bypass schema work, bypass solver work, or solids consequence modeling until M4 is complete.

## Product Direction

The roadmap is organized around usable plateaus:

1. credible repo foundation
2. usable `v0.2` hydraulic comparison
3. explicit current-state bypass hydraulics in `v0.3`
4. operational screening package
5. limited solids consequences in `v0.4`
6. later validation and expansion

Each plateau should produce something useful for plant operations, legible to experienced operators, understandable to managers, defensible to engineering reviewers, and strong enough to serve as a portfolio artifact.

## Current Status

As of the latest documentation checkpoint:

- schema and scenario structure support both `v0.1` and `v0.2` scenarios
- `run-hydraulics` produces reproducible run bundles for both model forms
- `compare-study` runs case-by-flow comparisons and writes JSON, CSV, Markdown, and media artifacts
- shipped scenarios include a design-intent versus current-state `v0.2` study at low, typical, and high flow
- the latest full test checkpoint is 34 passing tests outside sandbox
- the shipped `v0.2` study is workflow-valid but numerically weak, so its conclusions should remain visibly bounded until quality tiers and M4 hardening support stronger claims

Current supported solver boundary:

- structured Cartesian grids only
- steady deterministic screening-flow solves
- `v0.1`: opposite-side inlet/outlet pairs and full-depth solid baffles
- `v0.2`: conductance-based perforated-baffle, plate-settler, and launder proxy representation
- RTD behavior in `v0.2` is a deterministic proxy layer, not explicit validated transient transport
- preview animations may use compressed model time and must label that explicitly

## Repository Layout

- `docs/SESSION_START_CONTEXT.md`: first-read restart context
- `docs/ROADMAP.md`: canonical product roadmap
- `docs/IMPLEMENTATION_PLAN.md`: active milestone checklist
- `docs/research/`: preserved research and supporting references
- `docs/architecture/`: durable architecture and product decisions
- `scenarios/`: example YAML scenarios and studies
- `templates/`: structured intake templates
- `src/sed_model22/`: package code
- `tests/`: smoke and unit tests

## Quickstart

PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m sed_model22 validate scenarios/baseline_rectangular_basin.yaml
python -m sed_model22 run-hydraulics scenarios/baseline_rectangular_basin.yaml --media-policy off
python -m sed_model22 compare-study scenarios/studies/svwtp_design_vs_current.yaml
python -m unittest discover -s tests -v
```

POSIX shells:

```bash
PYTHONPATH=src python -m sed_model22 validate scenarios/baseline_rectangular_basin.yaml
PYTHONPATH=src python -m sed_model22 run-hydraulics scenarios/baseline_rectangular_basin.yaml --media-policy off
PYTHONPATH=src python -m sed_model22 compare-study scenarios/studies/svwtp_design_vs_current.yaml
PYTHONPATH=src python -m unittest discover -s tests -v
```

## CLI Commands

- `validate <scenario>`: validate YAML against the current scenario schema
- `validate-study <study>`: validate a comparison study YAML file
- `run-hydraulics <scenario>`: materialize a hydraulic run directory with mesh, fields, summary, SVG artifacts, and optional media
- `run-hydraulics --media-policy {off,still_only,low_fidelity_preview,best_effort_preview,require_preview}`: control voxel and preview generation
- `summarize <run_dir>`: print a concise run summary
- `plot <run_dir>`: regenerate run SVG outputs
- `compare-study <study>`: run a case-by-flow study and write comparison outputs plus study-level media packages

## Immediate Next Step

Finish M4 credibility hardening, then add formal quality tiers so weak runs cannot be mistaken for strong engineering conclusions. Explicit current-state bypass hydraulics comes next in `v0.3`; solids consequence modeling waits for `v0.4`.
