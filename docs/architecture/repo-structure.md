# Repo Structure

## Purpose

This repository is organized to keep three things separate from the start:

- preserved research material
- canonical project guidance
- runnable source code

That separation is intentional. The simulator will grow, but the supporting literature and design notes should remain easy to trace.

## Directory Responsibilities

- `docs/research/source-notes/`
  - preserved source material from the original project folder
  - reference-only; not the canonical place to define package behavior
- `docs/architecture/`
  - current project decisions
  - the target module boundaries
  - phased simulator roadmap
- `scenarios/`
  - human-authored YAML case definitions
  - examples for manual runs and automated smoke tests
- `src/sed_model22/`
  - importable Python package
  - config, geometry, mesh, solver, metrics, visualization, and transport boundaries
- `tests/`
  - smoke tests for validation, artifact generation, and structural correctness

## Package Boundaries

- `config`
  - scenario schema and YAML loading
- `geometry`
  - rectangular basin geometric helpers
- `mesh`
  - structured Cartesian grid sizing and summary
- `solver`
  - V0.1 hydraulics entrypoint and later solver work
- `metrics`
  - basin-scale engineering metrics
- `viz`
  - layout and result visualization
- `transport`
  - reserved for tracer and solids layers

## Stability Rules

- YAML scenarios are the first stable user interface.
- Run directories are the first stable machine-readable output interface.
- Research notes stay preserved; implementation behavior belongs in package code and architecture docs.
