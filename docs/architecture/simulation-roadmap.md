# Simulation Roadmap

## Summary

The repo is structured around staged capability growth. Each stage should reuse the same scenario schema and run artifact pattern unless there is a concrete reason to change them.

## Milestones

### Milestone 0

Repo foundation:

- docs organized
- package scaffold created
- CLI wired
- scenario schema defined
- run artifacts standardized

### Milestone 1

Geometry and mesh:

- rectangular basin geometry helpers
- structured grid sizing
- baffle representation as validated line segments

### Milestone 2

V0.1 hydraulics:

- steady depth-averaged hydraulic core
- initial boundary condition handling
- artifact outputs tied to run directories

### Milestone 3

Metrics and comparison:

- hydraulic screening metrics
- scenario comparison summaries
- stronger visualization outputs

### Milestone 4

Tracer transport:

- conservative tracer layer
- RTD-oriented outputs
- hydraulic efficiency interpretation

### Milestone 5

Simplified solids transport:

- settling proxy terms
- class-based solids representation
- solids escape risk indicators

## Upgrade Rule

Do not move to higher-fidelity modeling until the lower-fidelity layer fails to answer a real engineering question cleanly.
