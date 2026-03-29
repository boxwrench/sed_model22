# Development Log

This log is meant to stay short, chronological, and implementation-facing. Each entry should capture the repo state change, the reason for it, and the next immediate move.

## 2026-03-28

### Study-Level Media Packaging and Geometry Intake Tightening

What changed:

- tightened the preview-skip path so optional media rendering no longer swallows all exceptions
- added targeted coverage for missing-`ffmpeg` preview skip behavior and near-zero-flow tracer behavior
- added a shared media-layer `visual_scene.json` manifest so stills, HTML comparison pages, and previews consume one presentation contract instead of embedding more presentation logic in the solver
- added `low_fidelity_preview` as a fast run-bundle preview mode for quicker iteration
- upgraded the `v0.2` design-vs-current comparison page into a more leadership-facing artifact with narrative text, executive takeaways, highlighted metrics, and explicit model-boundary language
- wired `compare-study` so each study now writes a study-level `media/` package with one comparison package per flow, including stills, `visual_scene.json`, comparison HTML, and preview artifacts built from the existing run bundles
- cleaned and tightened `templates/intake_geometry_survey.yaml` so basin-local `x/z` coordinates are explicit, ambiguous elevation fields are renamed, bypass-path capture is structured, and encoding artifacts are removed

Why:

- leadership-facing communication now matters enough that study outputs should generate a repeatable visual package instead of leaving comparison media as a detached manual step
- a shared media scene contract is the right next abstraction because it keeps presentation logic in the media layer while preserving the repo's current solver/report honesty boundary
- the geometry intake template needed clearer coordinate semantics before drawing-derived geometry can be translated safely into `v0.2` scenarios

Verification:

- `python -m unittest tests.test_media tests.test_cli -v` passed
- `python -m unittest tests.test_study tests.test_media -v` passed
- `python -m unittest discover -s tests -v` passed with 34 tests

Current interpretation:

- `compare-study` is now a more complete decision-support workflow because it produces both tabular/report outputs and a study-level media package
- the media layer now has a stable scene manifest that can support future renderer changes or interactive HTML work without moving presentation responsibilities into solver code
- the intake template is now safer to use as the front door for real drawing extraction work, but the actual scenario translation still depends on the upcoming geometry details

Next:

- add a study-level landing page that links low, typical, and high flow packages together in one executive view
- start feeding cleaned real-basin geometry into the updated intake template and translate that into refreshed `v0.2` scenarios
- once the real geometry is in place, tune visual annotations and comparison copy against the actual plant questions instead of the placeholder template narrative

## 2026-03-27

### Pathline Preview Acceptance: Use Detention-Scale Time Compression

What changed:

- implemented a first real `v0.1` particle-pathline preview path in the normal media workflow
- added static plan-view streamline SVG output as the paired report-facing still
- tested the first preview in a near-real-time-style stepping mode and confirmed that it was misleadingly sparse for basin-scale interpretation
- reran the preview using compressed model time based on detention-scale duration and got a materially more useful result
- confirmed that the preview becomes decision-useful only when the animation shows basin-scale travel time rather than near-real-time drift

Why:

- the solver and metrics already report detention-scale basin timing, so the preview layer should use that information
- a short animation cannot communicate a several-hour basin story unless model time is compressed aggressively
- the operator-facing question is about routing and circulation pattern, not about visually simulating real-time water motion

Verification:

- `python -m unittest tests.test_media -v` passed
- `python -m unittest tests.test_cli -v` passed
- rendered a `2x` detention-time baseline preview that showed materially better basin routing intuition than the earlier near-real-time attempt

Current interpretation:

- deterministic particle pathlines are now an accepted prototype direction, not just a research recommendation
- detention-based time compression is a hard design rule for short basin previews
- streamline stills remain the stronger static companion figure and should stay paired with the preview path

Next:

- refine seeding, trail density, and guide-path styling against one or two especially legible cases
- write the follow-on spec from the corrected prototype, not from the earlier near-real-time miss
- keep honesty text explicit: compressed model time, steady field, directional screening output

### Visualization Research Decision Locked

What changed:

- reviewed the new visualization research memos and recorded a repo-facing synthesis
- filed the incoming memos under `docs/research/source-notes/` with topic-specific names
- locked the near-term visualization decision:
  - deterministic particle pathlines are the first animation method
  - static streamline stills are the report-facing companion output
  - dye-pulse style visualization remains deferred for now

Why:

- both research passes converged on particle pathlines as the strongest first method under the repo's current constraints
- streamline stills remain the most conventional and defensible engineering-facing figure
- dye-pulse output is still useful later, but it carries more transport-credibility risk than the current repo phase should take on first

Verification:

- docs update only
- no code tests run for this entry

Current interpretation:

- the next visualization coding pass should be tightly bounded
- do not continue broad voxel or preview experimentation first
- build one good particle-pathline preview path and one good streamline-still path before considering more elaborate methods

Next:

- write the small implementation spec for the first particle-pathline plus streamline pass
- pick one or two visually legible test cases for that pass
- keep honesty labels explicit and avoid visual effects that imply turbulence or transient CFD

### Preview Animation Reset and Research Handoff

What changed:

- replaced the earlier SVG-card slideshow dependency with a direct frame-rendered preview path that writes low-resolution preview frames and stitches them with `ffmpeg`
- added a guarded preview-render path with simple runtime selection, timeout monitoring, and frame-count safety limits
- tested two `v0.1` plan-view motion-first preview directions:
  - the existing `alternative_three_baffle_basin` case
  - a new preview-only scenario `scenarios/preview_three_baffle_high_energy.yaml`
- confirmed that the current point-particle animation style is technically functional but visually unconvincing for the basin problem
- recorded that the next correct step is research on better visualization primitives, not more local tuning of the current particle renderer
- recorded that better test models are now the more practical near-term need than more visualization styling work

Why:

- the direct frame-render path removes the immediate `CairoSVG` bottleneck and proves that the repo can generate real preview videos inside the current Python + `ffmpeg` workflow
- the resulting motion still does not read like hydraulically legible water behavior; it reads as synthetic particles over a static field
- that means the current blocker is no longer only tooling. It is representation choice
- the repo needs better test models and a more deliberate visualization-method choice before more animation implementation time is spent

Verification:

- `python -m unittest tests.test_media -v` passed
- `python -m unittest tests.test_cli -v` passed
- rendered visual-only plan-view previews under:
  - `_preview_three_baffle/`
  - `_preview_high_energy/`

Current interpretation:

- the repo can now generate deterministic low-resolution preview videos without relying on SVG rasterization
- the current `v0.1` particle-motion preview is not the right final visual language for basin flow communication
- voxel stills remain useful for geometry/report explanation, but not yet sufficient as the answer for animated flow behavior
- future visualization work should be driven by a short research pass on animation primitives and by better test-model selection

Next:

- perform the visualization research pass before implementing more animation styles
- improve or add test scenarios specifically chosen for visual legibility and hydraulic interpretation
- return to animation only after selecting a more defensible visualization primitive than the current particle overlay
- treat future voxel work mainly as a geometry/explanation layer unless later testing proves it can carry more of the flow-story honestly

### Run-Bundle Media Integration

What changed:

- integrated voxel media into the normal `run-hydraulics` workflow so run bundles now write `media/voxel_isometric.svg` by default
- added a run-media policy switch with `off`, `still_only`, `best_effort_preview`, and `require_preview`
- kept the current default at `best_effort_preview` so preview generation is attempted for the current single-user phase but never allowed to fail the basin run
- added a narrow internal media pipeline for template-driven stills, comparison pages, manifests, and preview-scene assembly
- generated a real `v0.2` run-media bundle and a template-driven `design_spec` vs `current_blocked` comparison artifact for review

Why:

- the repo now has enough output structure that voxel media should stop being a detached proof of concept and start becoming part of the normal run workflow
- the current phase still benefits from automatically attempting richer media output, but the hydraulic run must remain the primary artifact
- the next animation session needs a clean handoff: stable still output, known preview skeleton, and a precise statement of the current blocker

Verification:

- `PYTHONPATH=src python -m unittest discover -s tests -v` passed with 28 tests
- real run-media artifact generated at `runs/media_review/20260327T233109Z_svwtp-current-blocked-wall/`
- template-driven comparison artifact generated at `visualizations/_generated/v0_2_design_vs_current_report_review/`

Current interpretation:

- voxel stills are now part of the normal run-bundle workflow
- preview animation is still best-effort and currently skips `.mp4` generation when SVG rasterization is unavailable
- `ffmpeg` was found on the current machine, so the present blocker is not video stitching; it is the SVG-to-PNG rasterization step
- study-level comparison media is still template-driven rather than automatically attached to `compare-study`

Next:

- start the next session with animation work, not more voxel styling
- decide whether to install/use `CairoSVG` for the current SVG-based preview path or to move the preview frames to direct PNG generation
- once preview rasterization is resolved, wire the first report-facing comparison animation into the study workflow

### Voxel Visualization Proof of Concept

What changed:

- added first-pass voxel-style `2.5D` isometric visualizations for both the `v0.2` design-vs-current comparison and the original `v0.1` test pair
- confirmed that the visual format is useful as a proof of concept for communicating basin differences in a more legible way than tables alone
- recorded that this format is a desired future report output, but is not yet part of the standard repo output set
- recorded that no further visualization changes should be made until the next round of test data is available
- recorded that future visualization work should aim to resemble the real basin more closely, not just a generic extruded grid

Why:

- the comparison views proved useful for quickly reading design-vs-current differences and for checking whether the same visual language still works on the earlier `v0.1` cases
- the project now has evidence that a report-ready visual output can be both practical and transparent without pretending the current solver is already a full `3D` model
- the next meaningful design step depends on the next set of tests and data, not on additional presentational iteration alone

Verification:

- `PYTHONPATH=src python -m unittest discover -s tests -v` passed with 25 tests
- generated comparison artifacts under `visualizations/` for both `v0.2` and the original `v0.1` test pair

Current interpretation:

- keep the voxel/isometric format as a promising report-output direction
- do not treat it as a standard output artifact yet
- hold off on more visual refinement until the next test/data pass is available
- when the format returns, push it toward a closer resemblance to the real basin geometry and features

Next:

- gather the next set of test data
- revisit the visualization once there is better geometry or higher-confidence output worth presenting
- aim for a future report visual that looks recognizably like the real basin while staying explicit about model limitations

### Study Reporting Lesson: Separate Directional Signal from Literal Values

What changed:

- reran the shipped `svwtp_design_vs_current` study and reviewed the generated comparison outputs
- tightened study reporting so it now carries explicit screening cautions when solver credibility is weak or metrics are non-discriminating
- recorded that mixed RTD timing shifts must be reported explicitly instead of being collapsed into a single "earlier" or "later" statement
- recorded that large solver discharge mismatch means absolute velocity-derived `m/s` values are not field-credible, even when directional differences may still be useful
- recorded that saturated settling-threshold exceedance metrics should be called out as non-discriminating instead of being left to imply more meaning than they carry

Why:

- the first real design-vs-current study produced a useful directional signal, but some absolute velocity metrics were clearly not safe to present as literal predicted values
- subsequent studies need a repeatable rule for distinguishing decision-useful comparison signal from proxy-only outputs
- the current basin question is especially sensitive to this because the real current state still has an over-under serpentine bypass path that the present proof-of-concept model does not represent explicitly

Verification:

- `PYTHONPATH=src python -m unittest discover -s tests -v` passed with 22 tests
- `PYTHONPATH=src python -m sed_model22 compare-study scenarios/studies/svwtp_design_vs_current.yaml` produced an updated comparison report with explicit cautions

Current interpretation:

- keep using `v0.2` for practical screening comparisons
- report comparison direction and metric credibility together, not as separate concerns
- treat extreme absolute velocities as proxy outputs when solver mismatch is large
- treat saturated metrics as present-but-not-informative for the current study

Next:

- document the study-reporting rules in the handoff so later work does not repeat the same overstatement risk
- decide whether the next solver-focused pass should target discharge-scaling/metric interpretation, explicit serpentine bypass representation, or both

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
