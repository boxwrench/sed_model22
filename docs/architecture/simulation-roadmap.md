# Simulation Roadmap

The canonical product roadmap is `docs/ROADMAP.md`. This architecture note summarizes the implementation-facing solver sequence.

## Summary

The repo grows through usable plateaus. Each stage should preserve the same scenario and run-artifact pattern unless there is a concrete reason to change them.

The active rule is strict: complete M4 credibility hardening before starting bypass or solids work.

## Implementation Sequence

### Foundation

Status: done.

- docs organized
- package scaffold created
- CLI wired
- scenario schema defined
- run artifacts standardized

### V0.1 Plan-View Hydraulics

Status: implemented.

- rectangular basin geometry helpers
- structured plan-view grid
- steady screening hydraulic core
- basic boundary condition handling
- simple artifact outputs tied to run directories

### V0.2 Longitudinal Hydraulic Comparison

Status: implemented but needs credibility hardening.

- longitudinal `length x depth` grid
- design/current comparison workflow
- conductance-based proxy features for perforated walls, plate settlers, and launders
- RTD-style proxy outputs
- comparison-study artifacts

Current risk:

- shipped comparison runs are workflow-valid but can be numerically weak
- reports need formal quality tiers before they can support stronger conclusions

### M4 Credibility Hardening

Status: active.

- solver verification tests
- synthetic metrics unit tests
- solver and metrics docstrings
- mesh sensitivity smoke checks
- run quality tiers and quality reasons

### V0.3 Explicit Bypass Hydraulics

Status: gated by M4.

- verified current-state bypass geometry
- schema support for explicit bypass features
- solver routing through explicit bypass geometry
- design/current/proposed N-way study comparison
- low, typical, and high-flow re-baseline

### V0.4 Limited Solids Consequences

Status: later.

- 3 to 5 transparent settling classes
- class-specific capture or escape risk proxies
- screening consequence labels, not calibrated removal prediction

### Later Expansion

Status: later.

- operational study package refinements
- pseudo-transient flow sweeps
- interactive review pages
- field-informed validation
- external CFD comparison
- real-time integration only after validation supports it

## Upgrade Rule

Do not move to higher-fidelity modeling until the lower-fidelity layer fails to answer a real engineering question cleanly, and do not let outputs imply stronger confidence than the solver quality tier supports.
