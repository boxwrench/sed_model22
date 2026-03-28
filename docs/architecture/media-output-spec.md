# Media Output Spec

## Purpose

This document defines a narrow, repeatable media-output workflow for `sed_model22`.

The goal is not to build a general motion-design system. The goal is to create a token-efficient, code-first pipeline for:

- deterministic particle-pathline preview output
- static streamline report figures
- voxel-style still outputs
- side-by-side comparison outputs
- cheap preview animations
- future report-ready media exports

This should be implemented as a stripped-down internal media pipeline, not as a full clone of `pyreeler`.

## Design Goal

The media layer should make repeated output generation cheaper in both tokens and engineering effort.

That means:

- stable Python render code
- tiny template files
- deterministic output paths
- explicit proxy/fidelity labels
- minimal per-run prompt customization

Future requests should look like:

- render the `v0.2` design-vs-current still set
- render the `v0.1` test-pair comparison
- render the preview animation for template `x`

They should not require re-describing the entire visual concept each time.

## Scope

### In Scope

- deterministic particle-pathline preview generation from steady solved fields
- static streamline still generation for engineering-facing report use
- template-driven voxel still generation
- template-driven side-by-side comparison pages
- preview-first animation generation from code-rendered frames
- poster frame export
- manifest output for media runs
- deterministic `ffmpeg` assembly
- reuse of existing `sed_model22` scenario, field, and visualization code where practical

### Out of Scope

- stochastic particle styling that implies turbulence
- dye-pulse or scalar-transport animation for the current first visualization pass
- procedural audio
- narration or voice pipelines
- open-ended cinematic tooling
- generalized artistic effect systems
- changing the solver to fit the media output

## Working Rule

The media pipeline must not imply more model fidelity than the solver actually supports.

Required honesty rules:

- particle motion must be deterministic pathline motion through a steady field, not synthetic turbulence
- streamline and particle outputs must be framed as directional screening views, not field-validated transient prediction
- `v0.2` voxel output is currently a `2.5D` presentation of a `2D length x depth` field
- `v0.1` voxel output is currently a `2.5D` presentation of a `2D plan-view` field
- transparent water volumes, extruded width, or extruded depth are display devices, not proof of a real `3D` solve
- proxy-only metrics must stay labeled as proxy outputs
- weak-solver runs must carry credibility warnings in the media output just as they do in the study report

### Particle-Pathline Rules

The first animation method is not open-ended.

It should follow these rules:

- deterministic seeding only
- no stochastic jitter
- stable substeps for particle integration
- visible model-time compression for short previews
- modest particle counts sized for `854 x 480`
- short fading trails
- explicit geometry masking so baffles and walls stay legible
- persistent honesty label in preview output
- muted, practical styling over cinematic effects

For basin-scale preview work, near-real-time drift is the wrong assumption.

Working rule:

- choose model time shown from basin timescales, starting with theoretical detention time
- compress that model time into a short preview duration
- keep the integration stable by using smaller internal substeps than the rendered frame step
- label the compressed time span directly in the preview output

### Streamline Still Rules

Static streamline stills are the report-facing companion to particle previews.

They should:

- use moderate density, not publication-style overfilling
- preserve clear obstacle masking
- favor readable single-hue or restrained sequential palettes
- remain recognizable as engineering figures rather than high-fidelity CFD marketing output

## Token-Efficiency Strategy

### Script These

These steps are stable and should be fully scripted:

- load scenarios or study cases
- run the required solve path
- load existing run artifacts when possible
- render still images
- render side-by-side comparison pages
- render frame sequences
- export poster frames
- assemble preview videos with `ffmpeg`
- write media manifests

### Dependency Rule

Users should not be blocked from generating stills because they do not already have `ffmpeg`.

Implementation rule:

- still-image and comparison output must work without `ffmpeg`
- preview video is optional and should degrade gracefully when `ffmpeg` is missing
- current SVG-based previews also need an SVG-to-PNG rasterization step; if that step is unavailable, the pipeline should still write stills, cards, and the scene manifest and then skip the `.mp4`
- the resolver should check, in order:
  - `SED_MODEL22_FFMPEG`
  - `ffmpeg` on `PATH`
  - `tools/ffmpeg/bin/ffmpeg.exe` inside this repo
  - known local fallback paths
  - `imageio_ffmpeg` when installed

This keeps the repo lightweight while still supporting the common “download `ffmpeg` and drop it in a known folder” workflow.

### Template These

These choices should live in small template files:

- which cases to compare
- which view to use
- which labels to show
- which metric callouts to overlay
- which warning blocks to show
- animation scene order
- output names

### Do Not Re-Prompt By Default

Avoid spending tokens each run on:

- color palette choices
- camera angle selection
- warning language
- comparison layout
- title/subtitle structure
- scene timing for common report outputs

Those should already exist in templates unless a new output type is being designed.

## Repo Shape

### User-Facing Template Area

- `visualizations/templates/`
- `visualizations/templates/v0_2_design_vs_current.yaml`
- `visualizations/templates/v0_1_test_pair.yaml`
- `visualizations/templates/real_basin_placeholder.yaml`

These files should stay small and readable.

They should define:

- output type
- input scenarios or study rows
- selected visual scene sequence
- labels
- output names

### Package Code Area

- `src/sed_model22/media/pathlines.py`
- `src/sed_model22/media/streamlines.py`
- `src/sed_model22/media/render_still.py`
- `src/sed_model22/media/render_preview.py`
- `src/sed_model22/media/scenes.py`
- `src/sed_model22/media/layouts.py`
- `src/sed_model22/media/ffmpeg.py`
- `src/sed_model22/media/manifest.py`

This package should stay narrow.

It is a basin-media exporter, not a general animation framework.

## Preferred Output Types

### Type 1: Single-Case Voxel Still

Use for:

- one case overview
- report figures
- operator review

### Type 2: Side-by-Side Comparison

Use for:

- design vs current
- verification pair comparisons
- before/after studies

This is the current highest-value output.

### Type 3: Preview Animation

Use for:

- report companion media
- manager/stakeholder review
- quick narrative walkthrough of the comparison

The first version should be cheap and simple.

### Type 5: Particle Pathline Preview

Use for:

- showing dominant flow path
- showing recirculation and dead/slow regions
- showing short-circuiting directionally without claiming transient CFD

This is now the preferred first animation type.

### Type 6: Streamline Report Still

Use for:

- engineering-facing reports
- side-by-side design/current comparison pages
- technical review where a conventional flow-topology figure is needed

### Type 4: Poster Frame

Use for:

- report cover image
- study index image
- artifact gallery

## Animation Skeleton

The first reusable preview template should be fixed and simple:

1. title card
2. geometry and label frame
3. particle-pathline motion frame
4. comparison or metric callout frame
5. proxy/fidelity warning card
6. end frame

Do not start with moving cameras, complex timelines, or decorative transitions.

The point is legibility, not spectacle.

## First Visualization Slice

The next visualization implementation pass should be intentionally small.

Build in this order:

1. deterministic particle-pathline preview for existing solved fields
2. static streamline still export for report use
3. only then decide whether existing voxel outputs remain as optional geometry context

Do not make dye-pulse animation part of this first slice.

It remains a later option because it carries more transport-credibility risk than particle pathlines and streamlines do in the current repo phase.

Accepted prototype result:

- the first pathline preview became meaningfully legible only after switching from near-real-time stepping to detention-based time compression
- this is now a design rule, not an optional polish detail

## Relationship To PyReeler

The reusable idea from `pyreeler` is:

- code-generated frames
- preview-first workflow
- deterministic media export
- `ffmpeg` assembly
- poster and manifest outputs

What should be reused in spirit:

- build a cheap preview first
- keep render logic scriptable and repeatable
- keep outputs deterministic
- keep export pipeline portable

What should not be copied:

- audio stack
- open-ended creative workflow
- experimental effect vocabulary
- film-specific narrative tooling

## First Implementation Slice

Do not build the full media system first.

The first useful implementation slice is:

1. one template-driven still renderer
2. one template-driven comparison page
3. one cheap preview animation assembled from existing stills and overlays
4. one media manifest format

That is enough to prove the architecture.

## Current Status

As of 2026-03-27, the first slice is partly implemented:

- template-driven voxel still rendering exists
- template-driven comparison HTML output exists
- preview cards and scene manifests exist
- run bundles now write voxel media by default through `run-hydraulics`
- preview generation is attempted under `best_effort_preview` but is non-fatal by design
- `v0.1` now also has a first pathline-preview prototype plus static streamline still output
- the pathline prototype is useful only when the preview shows compressed detention-scale model time, not near-real-time drift

Current interpretation:

- the direct PNG/PPM frame path works for the current plan-view pathline prototype
- the main next issue is not basic render feasibility; it is polish, tuning, and choosing the best demonstration cases
- voxel stills remain useful as geometry context, but they are no longer the only viable motion path

## Next Session Start Point

If the next thread is specifically about animation work, start here:

1. keep detention-based time compression as a hard rule for short previews
2. refine particle seeding, trail length, and guide-path styling against one or two clearly legible plan-view cases
3. keep static streamline still export paired with the preview so report and animation outputs stay consistent
4. use voxel outputs as optional geometry context, not as the primary flow-story output
5. only after the pathline preview is visually stable, decide whether `compare-study` should auto-emit comparison animation or expose it as a follow-on media step

## Near-Term Visual Direction

Current voxel/isometric outputs are acceptable as proof of concept.

Future work should move toward a closer resemblance to the real basin:

- more recognizable structural proportions
- more realistic transition-wall depiction
- more basin-specific plate-zone and launder positioning
- eventual explicit representation of the serpentine bypass path when the solver supports it

Do not refine the visual style further until the next test/data pass provides the basis for a more realistic view.

## Hand-Off Rule

This document should make later implementation cheap to delegate.

If a later model is asked to build this system, the ask should be:

- implement the media-output spec in `docs/architecture/media-output-spec.md`
- keep the pipeline narrow and deterministic
- optimize for repeatable report outputs, not open-ended creative tooling
