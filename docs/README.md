# Documentation Hub

This folder is the working map for the project. Use it to find the current repo state quickly instead of digging through the full research archive.

## Start Here

1. `SESSION_START_CONTEXT.md`
   - shortest restart context for a new session
   - product intent, current status, risks, commands, and pickup checklist
2. `ROADMAP.md`
   - canonical product roadmap organized by usable plateaus
3. `IMPLEMENTATION_PLAN.md`
   - active engineering milestone checklist and pickup queue
4. `V0_3_ROADMAP.md`
   - scoped explicit-bypass hydraulics plan for the active `v0.3` workstream
5. `architecture/decision-log.md`
   - durable product and architecture decisions

## Current Snapshot

The repo is past pure scaffolding. The active build state is:

- canonical `v0.1` implementation basis documented
- `v0.1` plan-view hydraulic screening workflow implemented
- `v0.2` longitudinal design-vs-current workflow implemented
- run artifacts, SVG outputs, and study-level media packages working
- deterministic particle pathlines accepted as the first animation direction
- static streamline stills accepted as the report companion
- verification status: 41 passing tests at the latest code checkpoint outside sandbox
- active risk: the shipped `v0.2` study is workflow-valid, visibly quality-tiered, and still numerically weak because the current-state geometry is still proxy-based
- active rule: begin `v0.3` bypass hydraulics work, but keep solids work deferred until `v0.3` is complete

## Product Sequence

1. `v0.3` explicit current-state bypass hydraulics.
2. `v0.4` limited solids consequence layer.
3. Later operational expansion.

Each stage should produce something useful for plant operations, legible to experienced operators, understandable to managers, defensible to engineering reviewers, and suitable as a portfolio artifact.

## Folder Guide

| Path | Purpose |
| --- | --- |
| `SESSION_START_CONTEXT.md` | First-read restart context for new sessions |
| `ROADMAP.md` | Canonical product roadmap by usable plateau |
| `IMPLEMENTATION_PLAN.md` | Active milestone checklist and pickup queue |
| `V0_2_IMPLEMENTATION_HANDOFF.md` | Historical detailed `v0.2` implementation spec |
| `V0_3_ROADMAP.md` | Explicit bypass hydraulics roadmap for `v0.3` |
| `architecture/` | Canonical project decisions and implementation-facing structure |
| `architecture/media-output-spec.md` | Narrow spec for repeatable voxel and preview media outputs |
| `research/CANON.md` | Current build-stage implementation basis |
| `research/PRIMER.md` | Annotated guide to the research corpus |
| `research/source-notes/` | Preserved original notes, source drafts, reports, and reference assets |

## Canonical Reading Order

1. `SESSION_START_CONTEXT.md`
2. `ROADMAP.md`
3. `IMPLEMENTATION_PLAN.md`
4. `V0_3_ROADMAP.md` for the active bypass-hydraulics workstream
5. `research/CANON.md` when the implementation needs the research basis
6. `architecture/media-output-spec.md` when the session is about preview or report media
7. `DEVLOG.md` for chronological project history
8. `research/PRIMER.md` for the broader research archive

## Resume Here

If work resumes after a break:

1. Read `SESSION_START_CONTEXT.md`.
2. Read `ROADMAP.md`.
3. Read `IMPLEMENTATION_PLAN.md`.
4. Run the full test suite with `PYTHONPATH=src`.
5. Continue the `v0.3` bypass-hydraulics pickup queue before touching solids work.
