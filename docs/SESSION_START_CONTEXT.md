# Session Start Context

Read this first when starting a new session. It is the shortest repo-local summary of intent, current state, risks, and the next safe work.

## Product Intent

`sed_model22` is an operator-centered basin screening workflow. It is meant to help plant staff and reviewers compare rectangular sedimentation and flocculation basin conditions with transparent assumptions, reproducible artifacts, and honest limitations.

It is not a CFD replacement, a calibrated digital twin, a real-time operations system, or a full solids-transport model.

The product has to remain:

- useful for plant operations and practical discussion
- legible to experienced operators
- understandable to managers
- defensible to engineering reviewers
- strong enough to serve as a portfolio artifact

## Audiences

- Seasoned operators who understand the basin and need outputs that match operational intuition.
- Managers who need concise value, risk, and decision context without overstated claims.
- Engineering reviewers who need transparent assumptions, reproducible runs, and clear solver limits.
- Portfolio reviewers who need to see disciplined product thinking and credible engineering judgment.

## Current Repo State

- `v0.1` exists as a plan-view screening workflow for simple rectangular basin layout checks.
- `v0.2` exists as a longitudinal `length x depth` design-vs-current workflow with comparison-study outputs.
- The current code checkpoint has 41 passing tests outside the sandboxed environment.
- The CLI and YAML workflow are the main interface.
- The shipped `v0.2` design-vs-current study is workflow-valid and now visibly quality-tiered, but it is still numerically weak: the current study can demonstrate artifact generation and comparison structure, yet its conclusions should still be read as `weak` under the current solver diagnostics.

## Active Rule

M4 credibility hardening is complete. `v0.3` explicit bypass hydraulics is now the active workstream.

Do not start solids consequence modeling until `v0.3` bypass hydraulics is complete.

No new media polish, visual ambition, or stronger product claims should outrun solver credibility.

## Current Milestone Sequence

1. `v0.3` explicit current-state bypass hydraulics.
2. `v0.4` limited solids consequence layer.
3. Later operational expansion.

## Repo Map

Key docs:

- `docs/ROADMAP.md`: canonical product roadmap by usable plateaus.
- `docs/IMPLEMENTATION_PLAN.md`: active engineering pickup queue.
- `docs/V0_3_ROADMAP.md`: scoped `v0.3` bypass-hydraulics plan.
- `docs/V0_2_IMPLEMENTATION_HANDOFF.md`: historical `v0.2` implementation handoff.
- `docs/architecture/decision-log.md`: durable product and architecture decisions.
- `docs/research/CANON.md`: implementation-facing research synthesis.
- `docs/research/PRIMER.md`: research archive guide.

Scenarios and studies:

- `scenarios/baseline_rectangular_basin.yaml`: simple `v0.1` baseline.
- `scenarios/verification_empty_basin.yaml`: empty-basin verification case.
- `scenarios/svwtp_design_spec_basin.yaml`: shipped `v0.2` design-intent scenario.
- `scenarios/svwtp_current_blocked_wall_basin.yaml`: shipped `v0.2` current-state proxy scenario.
- `scenarios/studies/svwtp_design_vs_current.yaml`: shipped design-vs-current study.
- `templates/intake_geometry_survey.yaml`: structured geometry capture template for future bypass work.

Source modules:

- `src/sed_model22/config.py`: scenario and study schemas.
- `src/sed_model22/cli.py`: CLI commands.
- `src/sed_model22/run.py`: run-bundle materialization.
- `src/sed_model22/study.py`: comparison-study workflow.
- `src/sed_model22/solver/hydraulics.py`: `v0.1` plan-view solver.
- `src/sed_model22/solver/longitudinal.py`: `v0.2` longitudinal solver.
- `src/sed_model22/metrics/`: engineering metrics.
- `src/sed_model22/media/` and `src/sed_model22/viz/`: report and visual artifacts.

Tests:

- `tests/test_solver.py`: `v0.1` solver coverage.
- `tests/test_solver_verification.py`: `v0.1` verification coverage against expected behavior.
- `tests/test_longitudinal_solver.py`: `v0.2` solver coverage.
- `tests/test_longitudinal_solver_verification.py`: `v0.2` verification coverage against expected behavior.
- `tests/test_metrics.py`: synthetic metrics coverage.
- `tests/test_mesh_sensitivity.py`: `v0.2` mesh-sensitivity smoke checks.
- `tests/test_study.py`: comparison-study workflow coverage.
- `tests/test_cli.py`: command behavior.

## Commands

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

Expected runtime:

- validation: under a second
- single run with `--media-policy off`: a few seconds
- full unit suite: normally under 30 seconds outside sandbox
- full study with media defaults: slower and renderer-dependent

## Do Not Do Next

- Do not add solids modeling before `v0.3` bypass hydraulics are done.
- Do not add new media polish as the main task.
- Do not make stronger design/current claims than the current `run_quality_tier` supports.
- Do not imply CFD, real-time SCADA coupling, calibration, or validated water-quality prediction.
- Do not treat the current blocked-wall scenario as verified explicit bypass geometry.

## Fast Pickup Checklist

1. Read this file.
2. Read `docs/ROADMAP.md`.
3. Read `docs/IMPLEMENTATION_PLAN.md`.
4. Run `python -m unittest discover -s tests -v` with `PYTHONPATH=src`.
5. Confirm the current study still lands in the expected quality tier after any solver or schema change.
6. Continue `v0.3` explicit bypass hydraulics: verified geometry capture, schema support, explicit routing, and design/current/proposed comparison support.
