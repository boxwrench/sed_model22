# Canonical V0.1 Basis

This is the implementation-facing synthesis for the current build stage. It is intentionally shorter than the full research archive.

## Current Build Target

The current repo target is a narrow V0.1 hydraulic sandbox:

- rectangular basin plan view
- structured Cartesian grid
- steady or pseudo-steady depth-averaged screening flow
- full-depth solid baffles only
- offline scenario runs through CLI + YAML

This stage is for flow-pattern screening, not high-fidelity CFD.

## Canonical Source Notes

Use these as the primary basis for code decisions:

1. `source-notes/sed_floc_basin_simulator_master_package.md`
2. `source-notes/2D hydraulic simulator.md`
3. `source-notes/2D Basin Simulator_math.md`
4. `source-notes/Minimum viable physics.md`

Use these as supporting references when needed:

- `source-notes/basin_model_fidelity_ladder_and_pilot_project.md`
- `source-notes/basin_simulator_software_stack_and_implementation_flow.md`
- `source-notes/Water_Treatment_Plant_Technical_Specifications.md`

## V0.1 Decisions Locked For Implementation

- first interface is CLI + YAML, not notebook-first and not web-first
- repo remains custom-Python-first
- external solvers stay out of the mainline code path
- inlet and outlet are explicit boundary objects in the scenario schema
- the first implemented solver may be a screening solver so long as it is transparent and reproducible
- current baffle support is limited to full-depth solid, axis-aligned internal baffles

## In Scope

- basin geometry
- inlet/outlet placement and span
- impermeable walls
- impermeable full-depth baffles
- screening of bulk flow paths around obstructions
- run artifacts, field outputs, and simple engineering summaries

## Explicitly Out Of Scope

- tracer transport
- solids classes
- sludge blanket physics
- density currents
- thermal stratification
- partial-depth baffles
- porous/perforated baffles
- real-time SCADA integration
- 3D CFD

## Important Overlap Notes

The archive includes multiple AI-generated passes over similar questions. Keep them because they differ in emphasis:

- `2D hydraulic simulator.md` is the strongest practical implementation note
- `2D Basin Simulator_math.md` is the strongest equations/numerics note
- `Minimum viable physics.md` is the strongest filter on what to postpone

If later work conflicts with this doc, update this file first before changing the solver direction.
