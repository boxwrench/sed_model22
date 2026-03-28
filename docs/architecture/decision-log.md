# Decision Log

## Initial Decisions

### 001. Mainline Architecture

The mainline path is a custom Python simulator. External solvers remain future validation or comparison tools, not the core package architecture.

### 002. First Interface

The first user-facing interface is CLI + YAML scenarios. Notebooks and web UI are future layers.

### 003. Repo Shape

Research notes are preserved under `docs/research/` and are no longer mixed with the package namespace.

### 004. Package Layout

The package uses a `src/` layout with stable module boundaries for config, geometry, mesh, solver, metrics, visualization, and future transport work.

### 005. Current Implementation Boundary

`run-hydraulics` now performs a real V0.1 steady screening-flow solve on a structured Cartesian grid. The current boundary is intentionally narrow: opposite-side inlet/outlet pairs, impermeable walls, and full-depth solid baffles only.

### 006. Deferred Physics

Tracer transport, solids transport, density currents, partial-depth baffles, porous baffles, and full CFD/shallow-water fidelity remain explicitly deferred until the current V0.1 solver has stronger verification and comparison support.

### 007. Visualization Method Priority

For the current screening-model phase, the first animation method to pursue is deterministic particle pathlines with fading trails. Static streamline figures remain the preferred report-facing companion output. Dye-pulse style transport visuals remain deferred until their proxy status can be framed clearly enough that they do not imply validated transient transport or higher-fidelity physics than the current model supports.
