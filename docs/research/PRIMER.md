# Research Primer

This is the fast-entry guide to the research corpus. It is not a replacement for the source notes. It is the shortest path to the right note.

## What This Corpus Is Doing

Across the archive, the project converges on the same core idea:

- build an operator-centered simulator for rectangular flocculation and sedimentation basins
- keep the physics only as complex as needed to change a real engineering decision
- start with fast, transparent models
- reserve higher-fidelity CFD and digital twin work for cases where simpler models stop answering the question

The practical target is a staged path:

1. conceptual hydraulics and heuristics
2. 2D hydraulic sandbox
3. tracer and residence-time behavior
4. simplified settling and solids transport
5. future digital-twin and AI-assisted layers

## How To Read The Overlap

Some notes in this archive came from running similar prompts through multiple AI systems or through repeated passes on the same topic. That means overlap is expected.

Treat that overlap as useful signal, not just noise:

- repeated ideas usually indicate the stable core concept
- wording differences often reveal different modeling assumptions or different intended audiences
- one note may be stronger on equations, another on implementation staging, and another on operational framing
- if two notes disagree, that is usually where the real design decision is hiding

So the goal is not to delete every overlap. The goal is to identify:

- the shared backbone of the project
- the unique contribution of each note
- which note should be treated as canonical for implementation
- which notes should remain as alternate perspectives or supporting references

## Five-Minute Reading Path

If you want the fastest orientation, read these in order:

1. `source-notes/sed_floc_basin_simulator_master_package.md`
   - best single overview of scope, variables, outputs, fidelity ladder, and implementation stages
2. `source-notes/2D hydraulic simulator.md`
   - best explanation of the initial simulator target and the physics/numerics behind it
3. `source-notes/Minimum viable physics.md`
   - best argument for what physics matters for decisions and what can wait
4. `source-notes/Water_Treatment_Plant_Technical_Specifications.md`
   - plant/process reference material

## If You Need X, Read Y

| Need | Read this first | Why |
| --- | --- | --- |
| One-document overview of the simulator concept | `source-notes/sed_floc_basin_simulator_master_package.md` | Consolidated project purpose, scope, variables, outputs, fidelity ladder, and implementation flow |
| The first actual build target | `source-notes/2D hydraulic simulator.md` | Defines the V0.1 through V0.3 architecture and the practical 2D model limits |
| The math and numerical architecture | `source-notes/2D Basin Simulator_math.md` | Most explicit numerical-method note in the archive |
| What minimum physics is worth keeping | `source-notes/Minimum viable physics.md` | Strongest decision-oriented framing of model complexity |
| Alternative minimum-physics framing | `source-notes/minphysbasinmod.md` | Similar theme with a more staged implementation and digital-twin expansion path |
| Fidelity ladder and pilot-project framing | `source-notes/basin_model_fidelity_ladder_and_pilot_project.md` | Clean stage definitions and pilot-basin setup guidance |
| Software stack and implementation staging | `source-notes/basin_simulator_software_stack_and_implementation_flow.md` | Toolchain progression from simple Python to advanced stack |
| Full roadmap from physics to AI-assisted operations | `source-notes/AI-Assisted Basin Modeling Roadmap.md` | Broadest roadmap linking basin physics, ROMs, and digital-twin concepts |
| Plant-specific modeling guidance | `source-notes/svwtp_basin_modeling_report.md` | Most concrete plant-configuration and retrofit-oriented modeling advice |
| General sedimentation/flocculation modeling overview | `source-notes/Modeling Sedimentation.md` | Compact cross-cutting summary of approaches and toolchains |
| Operational framework for large-scale basins | `source-notes/Operational Modeling Framework for Large-Scale Sedimentation and Flocculation Basins.md` | Decision framework with retrofit and digital-twin context |
| Future digital-twin requirements | `source-notes/basin_digital_twin_requirements.md` | Clear boundary between current sandbox scope and future online twin scope |
| Raw plant and unit-process data | `source-notes/Water_Treatment_Plant_Technical_Specifications.md` | Detailed capacities, elevations, equipment, and process descriptions |
| Diagrams and reference assets | `source-notes/ref/` and `source-notes/*.svg` | Supporting visuals and structured reference material |

## Canonical vs Overlapping Notes

Use these as the current canonical set for day-to-day work:

| Status | File | Role |
| --- | --- | --- |
| Canonical | `source-notes/sed_floc_basin_simulator_master_package.md` | Single best concept package |
| Canonical | `source-notes/2D hydraulic simulator.md` | Main design note for the first simulator implementation |
| Canonical | `source-notes/Minimum viable physics.md` | Main argument for decision-oriented minimum physics |
| Canonical | `source-notes/Water_Treatment_Plant_Technical_Specifications.md` | Main plant/process reference |
| Supporting | `source-notes/2D Basin Simulator_math.md` | More formal mathematical/numerical version of the 2D simulator idea |
| Supporting | `source-notes/basin_model_fidelity_ladder_and_pilot_project.md` | Short, clear fidelity-stage note |
| Supporting | `source-notes/basin_simulator_software_stack_and_implementation_flow.md` | Short, clear tooling-stage note |
| Supporting | `source-notes/svwtp_basin_modeling_report.md` | Plant-specific retrofit and configuration guidance |
| Future-state | `source-notes/basin_digital_twin_requirements.md` | Not the immediate build target, but important later |
| Overlapping draft | `source-notes/minphysbasinmod.md` | Covers similar ground to `Minimum viable physics.md` with a longer implementation arc |
| Overlapping draft | `source-notes/Modeling Sedimentation.md` | Condensed overview with broad topic coverage |
| Overlapping draft | `source-notes/Operational Modeling Framework for Large-Scale Sedimentation and Flocculation Basins.md` | Similar decision/fidelity framing with large-scale operational emphasis |
| Overlapping draft | `source-notes/AI-Assisted Basin Modeling Roadmap.md` | Broad roadmap and digital-twin bridge; useful for long-range direction |
| Overlapping draft | `source-notes/sed_floc_basin_simulator_sandbox.md` | Earlier or alternate sandbox framing of the simulator concept |

Important reading note:

- `Overlapping draft` does not mean low value
- it means the file covers territory that also appears elsewhere
- keep these notes when they add a distinct angle, implementation detail, or emphasis that the canonical note does not capture

## Annotated Table of Contents

### Core simulator definition

| File | What it gives you | Best use |
| --- | --- | --- |
| `source-notes/sed_floc_basin_simulator_master_package.md` | Consolidated project purpose, scope, variables, outputs, fidelity ladder, software stack, and implementation steps | Use this to explain the project to someone new or to re-anchor the scope |
| `source-notes/sed_floc_basin_simulator_sandbox.md` | Alternate framing of the sandbox concept with phased capability growth | Use when comparing earlier wording of the simulator idea |
| `source-notes/basin_model_fidelity_ladder_and_pilot_project.md` | Clean explanation of Levels 0-4 and the recommended pilot fidelity target | Use when deciding how far to model for a specific question |
| `source-notes/basin_simulator_software_stack_and_implementation_flow.md` | Stack progression from starter Python to advanced engineering setup | Use when deciding tooling and implementation sequence |

### Physics and numerical modeling

| File | What it gives you | Best use |
| --- | --- | --- |
| `source-notes/2D hydraulic simulator.md` | Practical specification for a depth-averaged hydraulic simulator, including model limitations and baffle representation tradeoffs | Use as the main implementation reference for the current repo |
| `source-notes/2D Basin Simulator_math.md` | More formal equations, discretization choices, grid strategy, and pseudocode | Use when implementing the first real solver core |
| `source-notes/Minimum viable physics.md` | Decision-driven breakdown of which physics matter most and when simple calibrated models beat complex uncalibrated ones | Use when deciding what not to model yet |
| `source-notes/minphysbasinmod.md` | Similar minimum-physics framing with staged Python, ML, and digital-twin expansion | Use for long-range architecture and learning-path context |
| `source-notes/Modeling Sedimentation.md` | Short cross-domain survey of formulations, tools, surrogates, and digital twin architecture | Use when you want a compact broad refresher |

Distinct contributions in this cluster:

- `2D hydraulic simulator.md` is strongest on the practical first build
- `2D Basin Simulator_math.md` is strongest on equations and discretization choices
- `Minimum viable physics.md` is strongest on what to exclude for now
- `minphysbasinmod.md` is strongest on staged growth from hydraulics toward AI-assisted operations

### Roadmaps and operational framing

| File | What it gives you | Best use |
| --- | --- | --- |
| `source-notes/AI-Assisted Basin Modeling Roadmap.md` | Broad roadmap from CFD to reduced-order models and AI-assisted decision support | Use for long-term ambition and staging logic |
| `source-notes/Operational Modeling Framework for Large-Scale Sedimentation and Flocculation Basins.md` | Operations and retrofit framing for large-scale basins, including 2DV and digital-twin direction | Use when focusing on operational decision confidence |
| `source-notes/basin_digital_twin_requirements.md` | Future-state requirements for live data, governance, forecasting, and operator workflow integration | Use only after the offline simulator core is stable |

Distinct contributions in this cluster:

- `AI-Assisted Basin Modeling Roadmap.md` is the broadest long-range vision
- `Operational Modeling Framework for Large-Scale Sedimentation and Flocculation Basins.md` is stronger on practitioner and retrofit framing
- `basin_digital_twin_requirements.md` is stronger on the future online-system requirements than on the current sandbox build

### Plant-specific reference material

| File | What it gives you | Best use |
| --- | --- | --- |
| `source-notes/Water_Treatment_Plant_Technical_Specifications.md` | Detailed plant capacity, hydraulic profile, process units, equipment, instrumentation, and design notes | Use as the baseline plant data reference |
| `source-notes/svwtp_basin_modeling_report.md` | Plant-specific geometry, retrofit questions, launder and baffle optimization framing, and suggested minimum model fidelity | Use when the repo work turns toward a specific facility or retrofit campaign |
| `source-notes/ref/Treatment_Plant_Specifications.md` | Supporting structured plant reference note | Use as a secondary data check |
| `source-notes/ref/Treatment_Plant_Specifications.csv` | Tabular reference data | Use for extracting structured values into code later |
| `source-notes/ref/Hydraulic_Profile.md` | Supporting hydraulic reference note | Use when tracing elevations and process flow levels |
| `source-notes/ref/Process_Flow_Diagram.md` | Supporting process sequence reference | Use when mapping simulation boundaries to actual plant flow path |

### Visual and external-format assets

| File | What it gives you | Best use |
| --- | --- | --- |
| `source-notes/svwtp_basin_cross_section_modeling_zones.svg` | Cross-section modeling visual | Use for geometry discussions and future docs |
| `source-notes/ref/flow.png` | Reference process visual | Use as a quick visual reminder |
| `source-notes/ref/svp capacity.png` | Reference capacity visual | Use when discussing plant capacity |
| `source-notes/ref/svpprofile.png` | Reference profile visual | Use for profile context |
| `source-notes/Critical Review_ Flocculation and Settling Dynamics Beyond Classical Discrete Particle Assumptions (1).docx` | External-format research draft | Convert or summarize later if it becomes a primary reference |
| `source-notes/Minimum-Fidelity Modeling for Rectangular Sedimentation and Flocculation Basin Optimization_ A Technical Roadmap for Practitioner Implementation.docx` | External-format roadmap draft | Convert or summarize later if it becomes a primary reference |
| `source-notes/Operational Modeling Framework for Large-Scale Sedimentation and Flocculation Basins.pdf` | PDF companion to the markdown note | Use only if the markdown is missing needed detail |

## Suggested Working Set for This Repo

For current implementation work, keep these open:

- `source-notes/sed_floc_basin_simulator_master_package.md`
- `source-notes/2D hydraulic simulator.md`
- `source-notes/2D Basin Simulator_math.md`
- `source-notes/Minimum viable physics.md`
- `source-notes/Water_Treatment_Plant_Technical_Specifications.md`

Everything else is supporting context unless the task specifically shifts to plant-specific retrofits, digital-twin architecture, or long-range AI-assisted operations.
