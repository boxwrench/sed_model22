# Documentation Hub

This folder is the working map for the project. Use it to find the current repo state quickly instead of digging through the full research archive.

## Current Snapshot

The repo is now past pure scaffolding. The active build state is:

- canonical V0.1 implementation basis documented
- scenario schema expanded for explicit boundaries and solver controls
- first real screening-flow hydraulic solver in place
- run artifacts and SVG outputs working
- run bundles now include default voxel media output with best-effort preview assembly
- `v0.1` now has a first accepted particle-pathline preview prototype with paired streamline still output
- V0.2 product direction locked around design-versus-current basin comparison
- V0.3 roadmap now defined around explicit bypass geometry plus modest solids-consequence modeling
- detailed V0.2 executor-facing handoff documented
- token-efficient media-output architecture documented under `architecture/media-output-spec.md`
- verification status: 34 passing tests at the latest code checkpoint

## Start Here

- `DEVLOG.md`
  - the running build history
  - what changed, why it changed, and what comes next
- `IMPLEMENTATION_PLAN.md`
  - the persistent milestone checklist and pickup queue
- `README.md`
  - the broad docs hub and current-state map
- `V0_2_IMPLEMENTATION_HANDOFF.md`
  - the detailed V0.2 implementation spec
  - the current best single document for the next `v0.2` coding push
- `V0_3_ROADMAP.md`
  - the next-fidelity roadmap after the current `v0.2` comparison workflow
  - the current best single document for planning explicit bypass geometry and limited solids work
- `research/CANON.md`
  - the implementation-facing synthesis for V0.1
- `architecture/repo-structure.md`
  - where things belong in the repo
- `architecture/simulation-roadmap.md`
  - the staged implementation path
- `architecture/media-output-spec.md`
  - the token-efficient spec for voxel stills, pathline previews, and paired streamline outputs
- `research/PRIMER.md`
  - the research table of contents and quick-reference guide

## Folder Guide

| Path | Purpose |
| --- | --- |
| `IMPLEMENTATION_PLAN.md` | Active milestone checklist and session restart guide |
| `V0_2_IMPLEMENTATION_HANDOFF.md` | Detailed V0.2 implementation spec and progress checklist |
| `V0_3_ROADMAP.md` | Next-fidelity roadmap for explicit bypass geometry and limited solids consequence work |
| `architecture/` | Canonical project decisions and implementation-facing structure |
| `architecture/media-output-spec.md` | Narrow spec for repeatable voxel and preview media outputs |
| `research/CANON.md` | Current build-stage implementation basis |
| `research/PRIMER.md` | Annotated guide to the research corpus |
| `research/source-notes/` | Preserved original notes, source drafts, reports, and reference assets |

## Current Canonical Reading Order

1. `research/PRIMER.md`
2. `research/CANON.md`
3. `IMPLEMENTATION_PLAN.md`
4. `V0_2_IMPLEMENTATION_HANDOFF.md` when the session is about `v0.2` basin-comparison work
5. `V0_3_ROADMAP.md` when the session is about the next fidelity jump beyond the current `v0.2` comparison workflow
6. `architecture/media-output-spec.md` when the session is about preview or report media
7. `research/source-notes/sed_floc_basin_simulator_master_package.md`
8. `research/source-notes/2D hydraulic simulator.md`
9. `DEVLOG.md`

## Resume Here

If work resumes after a break, read these in order:

1. `DEVLOG.md`
2. `IMPLEMENTATION_PLAN.md`
3. `research/CANON.md`
4. `architecture/media-output-spec.md` if the next session is about voxel/report animation work
