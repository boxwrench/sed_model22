# Product Roadmap

This is the canonical roadmap for `sed_model22`. It is organized around usable plateaus so the repo remains valuable even if later expansion stops.

Each plateau should produce something useful for plant operations, legible to experienced operators, understandable to managers, defensible to engineering reviewers, and strong enough to serve as a portfolio artifact.

## Plateau 1: Credible Repo Foundation

Goal: clean docs, passing tests, explicit limitations, and reproducible runs.

Status: done.

Value:

- a readable repo that future contributors can restart quickly
- preserved research context without burying the implementation path
- CLI/YAML workflow that creates deterministic run artifacts
- explicit model boundary: screening hydraulics, not CFD or a digital twin

Exit criteria:

- `docs/SESSION_START_CONTEXT.md` is the first read for new sessions
- `docs/ROADMAP.md` is the canonical product roadmap
- tests pass in the intended environment
- docs avoid overstated operational or scientific claims

## Plateau 2: Usable `v0.2` Hydraulic Comparison

Goal: a credible design-vs-current screening report with quality-tier labels and manager/operator-readable outputs.

Status: achieved as a bounded screening plateau.

Current value:

- `v0.2` longitudinal workflow exists
- design/current comparison study exists
- low, typical, and high-flow study runs can produce comparison artifacts

Current gap:

- the shipped study is workflow-valid but numerically weak because convergence and discharge-balance problems still make the current comparison `weak`
- output artifacts now carry formal `run_quality_tier` and `quality_reasons`

Required work:

- keep the quality-tier classification wired through run summaries and study reports as the solver evolves
- ensure weak runs continue to visibly say `directional_only` or `weak`
- keep manager-facing outputs useful while refusing unsupported certainty

## Plateau 3: Explicit Current-State Bypass Hydraulics

Goal: a design/current/proposed comparison that represents the real flow path, not only a lossy wall proxy.

Target version: `v0.3`.

Status: active workstream.

Required work:

- verify current-state bypass geometry from drawings or field notes before encoding it
- extend the YAML schema for explicit bypass features
- route flow through the explicit over/under, side, or serpentine path on the longitudinal grid
- rerun design/current/proposed comparisons at low, typical, and high flow
- add N-way study comparison support while preserving the current first-case default behavior

Out of scope:

- solids consequence modeling
- 3D CFD
- real-time operations claims

## Plateau 4: Operational Screening Package

Goal: repeatable low/typical/high-flow outputs that operators can use for practical discussion, shift planning, and engineering review.

Required work:

- make the study report easy to scan by flow condition and case
- expose the key hydraulic risks in language that operators and managers can both read
- preserve detailed engineering artifacts for reviewers
- keep CLI/YAML as the main interface

Possible artifacts:

- study-level landing report across low, typical, and high flow
- consistent quality-tier badges
- concise operator/manager interpretation blocks
- reproducible artifact directories for each case and flow

## Plateau 5: Limited Solids Consequence Layer

Goal: class-based settling-risk outputs only after hydraulics are credible.

Target version: `v0.4`.

Required work:

- add 3 to 5 transparent settling classes
- estimate class-specific capture or escape risk from the hydraulic field
- report solids consequences as screening outputs, not calibrated performance prediction
- keep uncertainty visible in run summaries, reports, and media

Out of scope:

- calibrated turbidity prediction
- broad solids chemistry modeling
- claims that bypass hydraulics alone predict finished-water outcomes

## Plateau 6: Later Expansion

Possible future work:

- field validation from headloss, tracer observations, operator observations, or performance trends
- pseudo-transient flow sweeps such as hourly or diurnal flow conditions
- interactive review pages using the existing media scene contracts
- external CFD comparison for validation and calibration context
- SCADA or real-time integration only after validation supports it

## Interface State And Planned Changes

Study schema:

- add `baseline_case_label` for N-way comparisons
- preserve current first-case baseline behavior when the field is omitted

Run summary:

- already includes `run_quality_tier`
- already includes `quality_reasons`

Report behavior:

- manager-facing outputs should still show value and interpretation
- weak runs must visibly say `directional_only` or `weak`
- numerical detail should support the conclusion, not hide solver limitations

## Product Guardrails

- CLI/YAML remains the main interface for now.
- Do not add SCADA, real-time operations, or calibrated digital-twin claims before validation exists.
- Do not overbuild visuals before solver credibility and current-state geometry are strong enough.
- Preserve usable plateaus: each stage should stand on its own.
