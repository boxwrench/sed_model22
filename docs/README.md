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
   - scoped explicit-bypass hydraulics plan after M4 is complete
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
- verification status: 34 passing tests at the latest code checkpoint outside sandbox
- active risk: the shipped `v0.2` study is workflow-valid but numerically weak until convergence, discharge balance, mesh sensitivity, and quality-tier work are hardened
- active rule: do not begin bypass or solids work until M4 credibility hardening is complete

## Product Sequence

1. M4 credibility hardening.
2. `v0.3` explicit current-state bypass hydraulics.
3. `v0.4` limited solids consequence layer.
4. Later operational expansion.

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
4. `V0_3_ROADMAP.md` only after M4 work is complete or when planning bypass hydraulics
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
5. Continue the M4 pickup queue before touching bypass or solids work.
