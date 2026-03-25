# SVWTP Basin Modeling for Launder and Baffle Optimization
## A Plant-Specific Computational Modeling Guide

---

## Plant Configuration: What We're Working With

From the WD-2316R Design Criteria (Montgomery Watson / AGS, Phase 1) and your operational knowledge:

### Basin Geometry

| Parameter | Flocculation Section | Sedimentation Section |
|-----------|---------------------|-----------------------|
| Count | 5 basins | 5 basins |
| Flow range per basin | 5–40 MGD | 5–40 MGD |
| Volume each | ~800,000 gal (107,000 ft³) | ~1,600,000 gal (214,000 ft³) |
| Dimensions (W × L) | 60 ft × ~80 ft | 60 ft × 340 ft |
| Water depth | 11 ft | 11 ft |
| Length:Width | 1.33:1 | 5.67:1 |
| Width:Depth | 5.45:1 | 5.45:1 |

### Existing Internal Features

**Flocculation section:**
- 12 vertical mixers per basin (likely 3 rows of 4, or 4 rows of 3)
- 8 basin inlet orifices per basin
- Tapered mixing energy (decreasing G downstream)

**Sedimentation section:**
- High-rate plate settlers (stainless steel inclined plate)
- Design loading rate: 0.5 gpm/ft²
- Total projected plate area: 76,100 ft² (across all basins)
- Reciprocating sludge scrapers: 2 per basin, each with 3 sections (1×11', 2×23')
- Scraper speed: 5 ft/min forward, 11.5 ft/min return
- Helical screw cross-collectors: 2 per basin
- Existing launders (current configuration to be evaluated)

### Key Aspect Ratios That Drive Model Choices

The sedimentation basin at 60 × 340 × 11 ft has a length-to-depth ratio of 30.9:1 and a width-to-depth ratio of 5.45:1. These ratios have direct consequences for modeling:

- The high L:D ratio (31:1) means the flow is strongly longitudinal — good news, because it means a 2D longitudinal cross-section (length × depth) captures the dominant physics for most baffle and launder questions.
- The moderate W:D ratio (5.45:1) means lateral variations exist but are secondary — you likely have some lateral non-uniformity in flow distribution, but it is not the dominant effect. A 2D model handles most of what you need. Full 3D becomes necessary only when evaluating launders that span part of the width, or when lateral flow maldistribution is itself the question.
- The plate settlers sit within the sedimentation section and fundamentally alter the flow field in the upper portion of the basin. They must be represented in the model, at minimum as a porous zone with anisotropic resistance.

---

## What You Actually Need to Decide (And What Physics Each Decision Requires)

You stated three priorities: launder placement, baffle placement/type, and retrofit evaluation. Each of these requires different physics and different model resolution. Here is the mapping:

### Launder Placement

**The question:** Where should collection launders be positioned in the sedimentation basin to maximize flow uniformity and minimize upwelling velocities that could entrain settled particles?

**The physics that matters:**
- Velocity field in the last 30–60 ft of the basin (near the outlet)
- Upwelling velocity magnitude at the launder openings relative to the critical particle settling velocity
- Horizontal flow distribution across the basin width approaching the launders
- The interaction between plate settler outflow and launder intake geometry

**The physics you can safely ignore:**
- Detailed turbulence structure (mean flow governs launder design)
- Floc breakup/aggregation (particles are already formed by this point)
- Sludge blanket dynamics (relevant to removal efficiency but not launder placement)
- Temperature-driven density currents (secondary effect on launder design specifically)

**Minimum viable model:** 2D RANS (length × depth cross-section) with the plate settler zone represented as a porous medium. This captures vertical upwelling patterns near launders and the interaction with the plate settler outflow. Upgrade to 3D only if you are comparing launders that cover different fractions of the basin width, or evaluating finger launders versus full-width troughs.

### Baffle Placement and Type

**The question:** Where should energy-dissipating baffles be placed between the flocculation and sedimentation sections (and potentially within the sed basin) to minimize short-circuiting and maximize effective settling volume? What type — perforated wall, solid with ports, turning vanes, Stamford-type?

**The physics that matters:**
- Inlet jet momentum from the flocculation section transition
- Energy dissipation rate and how quickly the jet decays to basin-average velocity
- Short-circuiting pathways created by momentum-driven flow
- Dead zone formation behind solid baffles
- Velocity uniformity downstream of the baffle (the whole point)

**The physics you can safely ignore:**
- Detailed floc size distribution (treat particles as passive tracers for hydraulic evaluation)
- Chemical reactions
- Sludge blanket interaction with baffles (unless the baffle is in the sludge zone)

**Minimum viable model:** 2D RANS (length × depth) captures the critical vertical recirculation patterns that baffles are designed to control. The inlet jet typically "dives" toward the bottom of the basin, creating a density current that hugs the floor. A well-placed baffle forces the flow to redistribute vertically. This is primarily a 2D phenomenon in a rectangular basin with L:W > 5. Upgrade to 3D only if you are evaluating baffles that do not span the full width, or if you suspect significant lateral asymmetry in the inlet flow.

### Retrofit Evaluation (Combining Launders + Baffles)

**The question:** What combination of launder configuration and baffle configuration maximizes basin performance across the 5–40 MGD operating range?

**Minimum viable model:** Run the 2D RANS model at 4–5 flow rates spanning your operating range (5, 10, 20, 30, 40 MGD per basin) for each candidate retrofit configuration. Evaluate using residence time distribution (virtual tracer test), velocity uniformity metrics, and upwelling velocity at launders. This produces a design matrix of maybe 5 flows × 6–10 configurations = 30–50 simulations. At 2D resolution, each runs in minutes. At 3D, each runs in hours — still feasible for a campaign study, but not for interactive optimization.

---

## The 2D RANS Model: Your Workhorse

For 80% of your launder and baffle work, a 2D Reynolds-Averaged Navier-Stokes model on the longitudinal cross-section (length × depth, 420 ft × 11 ft) is the right tool. Here is the complete specification.

### Governing Equations

The 2D incompressible RANS equations in the x (longitudinal) and z (vertical) directions:

**Continuity:**
∂u/∂x + ∂w/∂z = 0

**x-momentum:**
∂u/∂t + u·∂u/∂x + w·∂u/∂z = −(1/ρ)·∂p/∂x + ∂/∂x[(ν + νₜ)·∂u/∂x] + ∂/∂z[(ν + νₜ)·∂u/∂z]

**z-momentum:**
∂w/∂t + u·∂w/∂x + w·∂w/∂z = −(1/ρ)·∂p/∂z + ∂/∂x[(ν + νₜ)·∂w/∂x] + ∂/∂z[(ν + νₜ)·∂w/∂z] − g

where u = longitudinal velocity, w = vertical velocity, ν = kinematic viscosity (~1.0×10⁻⁶ m²/s at 20°C, ~1.5×10⁻⁶ at 5°C), νₜ = turbulent eddy viscosity from the turbulence model, and g = gravitational acceleration.

### Turbulence Closure

**Recommended: k-ω SST (Menter, 1994)**

This model blends k-ω near walls (where it performs well for boundary layers and separated flows) with k-ε in the freestream (where k-ω is sensitive to freestream turbulence values). For basin flows with both wall-bounded regions (floor, baffles) and free shear layers (inlet jet, baffle wakes), SST is superior to standard k-ε.

The two transport equations are:

∂k/∂t + Uj·∂k/∂xj = P̃k − β*·ω·k + ∂/∂xj[(ν + σk·νₜ)·∂k/∂xj]

∂ω/∂t + Uj·∂ω/∂xj = α·S² − β·ω² + ∂/∂xj[(ν + σω·νₜ)·∂ω/∂xj] + 2(1−F₁)·σω₂·(1/ω)·(∂k/∂xj)·(∂ω/∂xj)

where νₜ = a₁·k / max(a₁·ω, S·F₂), with blending functions F₁ and F₂ handling the transition between k-ω (near walls) and k-ε (in freestream).

**Why not standard k-ε:** It overpredicts turbulent mixing in recirculation zones behind baffles, which means it will underestimate dead zone size and overestimate baffle effectiveness. This is exactly the bias you don't want when evaluating retrofit options.

**Why not LES:** For a 420 ft × 11 ft domain at the mesh resolution needed (see below), LES would require ~10× finer mesh and ~100× longer run times. The additional accuracy in turbulence statistics does not translate to better baffle/launder design decisions.

### Representing Plate Settlers as a Porous Zone

The inclined plate settlers cannot be meshed plate-by-plate — they are too thin (typically 2-inch spacing) relative to basin scale. Instead, represent the plate settler zone as an **anisotropic porous medium** using the Darcy-Forchheimer model:

**Momentum sink in porous zone:**
Sᵢ = −(μ/α)·uᵢ − C₂·(½ρ|u|)·uᵢ

where α is the permeability (m²) and C₂ is the inertial resistance factor (1/m). For inclined plate settlers at typical 60° inclination with 2-inch (50 mm) plate spacing:

- Along the plate direction (flow through): α ≈ d²/12 where d = plate spacing = 0.05 m → α ≈ 2.1×10⁻⁴ m², C₂ ≈ 5–20 m⁻¹
- Perpendicular to plates: set resistance ~100× higher (plates block cross-flow)

Calibrate the resistance coefficients so that the pressure drop across the porous zone matches the headloss you measure across your plate settlers at known flow rates. This is the single most important calibration for the sedimentation basin model.

### Domain and Boundary Conditions

**Domain:** 2D rectangle representing the longitudinal cross-section. Total length = 80 ft (floc) + 340 ft (sed) = 420 ft. Height = 11 ft. If you model only the sed basin, length = 340 ft.

**Inlet (left boundary):**
- Velocity: uniform or parabolic profile, magnitude = Q / (W × D) where Q is flow per basin, W = 60 ft, D = 11 ft
- At 40 MGD: Q = 40 × 10⁶ / (7.48 × 60 × 24) = 3,717 ft³/min = 61.95 ft³/s → u_inlet = 61.95 / (60 × 11) = 0.094 ft/s = 0.0286 m/s
- At 5 MGD: u_inlet = 0.094 × (5/40) = 0.012 ft/s = 0.0036 m/s
- Turbulence: k = 1.5 × (0.05 × u_inlet)² ; ω = k^0.5 / (0.09^0.25 × 0.07 × D_hydraulic)
- If modeling the transition from flocculation: use the actual orifice/port configuration as the inlet

**Outlet (right boundary — launders):**
- Model existing launders as a series of line sinks at their actual positions
- For each launder trough, apply a velocity outlet with flow rate proportional to launder length
- Alternative: model the outlet weir as a pressure outlet at the weir elevation

**Top (free surface):**
- Symmetry boundary (slip wall) — this assumes a flat free surface, which is valid for the very low Froude numbers in sedimentation basins (Fr << 0.01)
- Do not use a VOF free-surface model; it adds massive computational cost for negligible benefit in a basin with 11 ft depth and velocities under 0.1 ft/s

**Bottom (basin floor):**
- No-slip wall with wall functions (y+ ≈ 30–100 for k-ω SST with wall functions)
- If scraper motion matters: add a moving boundary condition at scraper speed (5 ft/min = 0.025 m/s), but this is secondary for launder/baffle evaluation

**Internal features:**
- Baffles: solid wall boundaries (no-slip) for solid baffles; porous zones for perforated baffles
- Plate settlers: anisotropic porous zone as described above
- Sludge hoppers: include the floor profile dipping into hopper geometry

### Mesh Strategy for Your Basin

**Total domain:** 420 ft × 11 ft = 128 m × 3.35 m (in SI units for the solver)

**Base resolution:** Δx = 0.1 m (4 inches), Δz = 0.05 m (2 inches) in the bulk basin → ~1,280 × 67 = ~86,000 cells

**Refinement zones (2× or 4× refinement):**
- Inlet zone: first 20 ft (6 m) of the sed basin — capture jet behavior
- Baffle region: ±5 ft (±1.5 m) around each baffle — capture wake and recirculation
- Plate settler zone: entire porous region — capture flow redistribution
- Launder zone: last 30 ft (9 m) — capture upwelling patterns
- Near all walls: boundary layer refinement (first cell height for y+ ~ 30–50)

**Refined mesh total:** ~150,000–250,000 cells. This runs in 5–15 minutes per steady-state simulation on a modern workstation.

**Mesh sensitivity test:** Run at 1×, 2×, and 4× base resolution. Compare outlet velocity profiles and total pressure drop. When the result changes less than 5% between refinement levels, you are mesh-independent.

### What to Measure in Each Simulation

For every configuration, extract these operationally meaningful metrics:

**1. Residence Time Distribution (RTD)**
Inject a passive scalar tracer at the inlet (step input, concentration = 1.0 at t=0) and monitor concentration at the outlet over time. From the breakthrough curve, compute:
- t₁₀ = time for 10% of tracer to exit (baffling factor = t₁₀/T_theoretical)
- t₅₀ = median residence time
- t₉₀ = time for 90% of tracer to exit
- Morrill Dispersion Index = t₉₀/t₁₀ (ideal plug flow = 1.0; >22 is essentially fully mixed)
- Volumetric efficiency = t₅₀/T_theoretical (fraction of basin volume actually used)

**2. Velocity Uniformity Index (VUI)**
At any cross-section, compute the ratio of average velocity to maximum velocity. Closer to 1.0 = more uniform. Evaluate at: immediately downstream of each baffle, at the plate settler entrance, and at the launder zone.

**3. Upwelling Velocity at Launders**
Extract vertical velocity (w) at the elevation of each launder opening. Compare to the critical settling velocity of your smallest target particle. If w > v_s,critical at any launder, particles will be entrained.

**4. Dead Zone Fraction**
Identify cells where velocity magnitude is less than 10% of the cross-section average velocity. Sum their volume and divide by total basin volume. This quantifies the fraction of your basin doing no useful work.

**5. Short-Circuiting Index**
SCI = t₁₀ / T_theoretical. Values above 0.5 are acceptable. Above 0.7 is good. Your target for retrofit is SCI > 0.7.

---

## Baffle Configurations to Test

Based on the literature and basin geometry, here are the specific baffle configurations worth modeling. For your 60 × 340 × 11 ft sed basin, the critical location is the transition from the flocculation section.

### Configuration 1: Baseline (Existing)
Model whatever is currently installed. This is your reference case. All retrofit options are evaluated relative to this.

### Configuration 2: Perforated Inlet Baffle
- Full-width wall at the floc-sed transition (x = 0 in the sed basin)
- Porosity: 5–8% of cross-sectional area (this is the standard range)
- Orifice distribution: uniform across the wall, with orifices at multiple elevations
- Orifice diameter: 4–8 inches (affects jet length downstream)
- Model as: individual orifice jets (if few, large orifices) or porous zone (if many small orifices)

**What to look for:** A good perforated baffle converts the single inlet jet into many small jets that merge into uniform flow within 2–3 basin depths (22–33 ft) downstream. The orifice velocity should be 1–3 ft/s to provide adequate energy dissipation without breaking floc.

### Configuration 3: Solid Baffle with Bottom Ports
- Solid wall spanning full width, with ports only in the lower 1/3 of the wall
- Port area: 5–8% of cross-section
- Forces flow downward, then along the bottom, then upward — creating plug flow
- Risk: sludge blanket interaction if bottom ports are within the sludge zone

### Configuration 4: Two-Baffle System (Energy Dissipating Inlet)
- First baffle at x = 10–15 ft from floc-sed transition
- Second baffle at x = 30–50 ft
- First baffle: 60% porosity (coarse energy reduction)
- Second baffle: 5–8% porosity (flow distribution)
- This staged approach dissipates inlet energy progressively

### Configuration 5: Turning Vanes at Transition
- If the flow path turns (e.g., over-under between floc and sed sections)
- Curved vanes redirect flow while maintaining uniformity
- Less pressure drop than perforated walls
- More complex to fabricate and install

### Configuration 6: Mid-Basin Intermediate Baffle
- Additional baffle at x = 100–170 ft (at the 30–50% point of the sed basin)
- Redistributes flow that has developed secondary currents
- Most useful when density currents are an issue
- Test with and without: if the inlet baffle alone achieves SCI > 0.7, this is unnecessary

For each configuration, run at minimum 3 flow rates (5 MGD low turndown, 20 MGD average, 40 MGD peak). Report all five metrics from the previous section.

---

## Launder Configurations to Test

Launder placement determines the velocity field at the exit end of the basin. The design goal is to distribute flow collection over a large area to keep upwelling velocities below the critical settling velocity.

### Current Launder Configuration (Baseline)
Document the existing launder locations, lengths, spacing, and weir loading rates. Model as-is.

### Configuration A: End-Wall Launders Only
- All flow collected at the downstream wall
- Highest upwelling velocities (concentrated at one location)
- Simplest construction but worst hydraulic performance
- Useful as the "worst case" reference

### Configuration B: Finger Launders at 1/3 and 2/3 Points
- Two sets of launders extending from the end wall back into the basin
- Launders perpendicular to flow direction, spaced 10–20 ft apart
- Each launder finger: 15–30 ft long
- Distributes flow collection over a larger area
- Reduces maximum upwelling velocity by roughly 50% versus end-wall only

### Configuration C: Full-Length Finger Launders
- Launders extending 60–100 ft from the end wall
- 4–6 parallel launders at 10–15 ft spacing
- Lowest upwelling velocities but highest construction cost
- Evaluate whether the additional length provides diminishing returns

### Configuration D: Submerged Orifice Launders
- Instead of weir-type launders (gravity overflow), use submerged orifice launders
- Orifice launders provide more uniform flow distribution along their length
- Less sensitive to launder leveling (a major field issue with weir launders)
- Require slightly more head but provide better hydraulic control

### Interaction with Plate Settlers
The plate settlers discharge clarified water upward, and this flow must reach the launders without re-entraining settled particles. The launder configuration must be compatible with the plate settler layout:
- Launders should be positioned above or immediately downstream of the plate settler discharge zone
- If plate settlers discharge at elevation z = 8 ft (3 ft below the surface), launders at z = 10 ft (1 ft below surface) work
- The gap between plate settler top and launder bottom must be sufficient to avoid excessive velocities

### Key Design Check
For each launder configuration, compute the weir loading rate:

WLR = Q / L_total

where Q = basin flow and L_total = total launder crest length. For conventional sedimentation:
- Design WLR: 10–20 gpm/ft is typical
- At 40 MGD per basin: Q = 27,778 gpm → need L_total = 1,389–2,778 ft of launder crest
- At 5 MGD: Q = 3,472 gpm → L_total = 174–347 ft

The model will show whether launder length is sufficient by revealing whether upwelling velocities at the launders exceed your target settling velocity.

---

## Python Implementation: Building the 2D Basin Model

For your workflow, I recommend a two-track approach:

**Track 1: Custom Python for rapid parametric studies** — build a 2D finite-volume Navier-Stokes solver tailored to your basin. This runs in minutes, you control every assumption, and you can iterate quickly on baffle/launder configurations.

**Track 2: OpenFOAM for high-fidelity validation** — use OpenFOAM (driftFluxFoam or simpleFoam) for 3D cases and for validating your custom 2D solver against established numerics.

### Track 1: Custom 2D RANS Solver Architecture

The solver uses a staggered grid finite-volume discretization with SIMPLE pressure-velocity coupling. Here is the complete code architecture:

```
svwtp_basin_model/
├── geometry/
│   ├── basin_config.py          # Basin dimensions, baffle locations, launder positions
│   ├── mesh_generator.py        # Structured mesh with local refinement
│   └── porous_zones.py          # Plate settler resistance definition
├── physics/
│   ├── navier_stokes_2d.py      # Momentum + continuity (SIMPLE algorithm)
│   ├── turbulence_kw_sst.py     # k-ω SST model
│   ├── scalar_transport.py      # Passive tracer for RTD computation
│   └── boundary_conditions.py   # Inlet/outlet/wall/symmetry/porous
├── solvers/
│   ├── steady_state.py          # SIMPLE iteration loop
│   ├── transient.py             # PISO or transient SIMPLE for tracer studies
│   └── convergence.py           # Residual monitoring, relaxation control
├── postprocessing/
│   ├── rtd_analysis.py          # RTD from tracer breakthrough
│   ├── velocity_metrics.py      # VUI, dead zones, upwelling velocities
│   ├── visualization.py         # Streamlines, velocity contours, tracer maps
│   └── comparison_table.py      # Side-by-side configuration comparison
├── scenarios/
│   ├── baseline.py              # Current configuration
│   ├── baffle_studies.py        # Baffle parametric sweep
│   ├── launder_studies.py       # Launder parametric sweep
│   └── combined_retrofit.py     # Best baffle + best launder combinations
├── validation/
│   ├── tracer_test_data/        # Field tracer test results for comparison
│   ├── scada_comparison.py      # Compare model predictions to SCADA data
│   └── mesh_sensitivity.py      # Grid convergence study
└── config.yaml                  # All simulation parameters in one place
```

### Key Implementation Components

**Basin configuration (basin_config.py):**

```python
# All dimensions in meters (convert from ft internally)
FT_TO_M = 0.3048
GAL_TO_M3 = 0.003785

class SVWTPBasin:
    """SVWTP sedimentation basin geometry."""

    # Flocculation section
    floc_width = 60 * FT_TO_M      # 18.29 m
    floc_length = 80 * FT_TO_M     # 24.38 m
    floc_depth = 11 * FT_TO_M      # 3.35 m
    floc_volume = 800_000 * GAL_TO_M3  # ~3,028 m³
    n_vertical_mixers = 12
    n_inlet_orifices = 8

    # Sedimentation section
    sed_width = 60 * FT_TO_M       # 18.29 m
    sed_length = 340 * FT_TO_M     # 103.63 m
    sed_depth = 11 * FT_TO_M       # 3.35 m
    sed_volume = 1_600_000 * GAL_TO_M3  # ~6,057 m³

    # Plate settlers (porous zone)
    plate_angle = 60  # degrees from horizontal
    plate_spacing = 0.05  # m (2 inches)
    plate_loading = 0.5  # gpm/ft² design maximum
    plate_area_total = 76_100  # ft² projected across all basins
    plate_area_per_basin = plate_area_total / 5  # ft² per basin

    # Sludge scrapers
    scraper_sections = [11 * FT_TO_M, 23 * FT_TO_M, 23 * FT_TO_M]
    scraper_speed_forward = 5 / 60 * FT_TO_M  # m/s
    scraper_speed_return = 11.5 / 60 * FT_TO_M  # m/s

    # Operating range
    flow_min_mgd = 5
    flow_max_mgd = 40
    n_basins = 5

    def flow_to_velocity(self, q_mgd):
        """Convert MGD to inlet velocity (m/s)."""
        q_m3s = q_mgd * 1e6 * GAL_TO_M3 / 86400
        return q_m3s / (self.sed_width * self.sed_depth)

    def sor_at_flow(self, q_mgd):
        """Surface overflow rate in m/h at given flow."""
        q_m3s = q_mgd * 1e6 * GAL_TO_M3 / 86400
        area_m2 = self.sed_width * self.sed_length
        return q_m3s / area_m2 * 3600

    def detention_time(self, q_mgd, section='sed'):
        """Theoretical detention time in minutes."""
        q_m3s = q_mgd * 1e6 * GAL_TO_M3 / 86400
        if section == 'sed':
            vol = self.sed_volume
        elif section == 'floc':
            vol = self.floc_volume
        else:
            vol = self.sed_volume + self.floc_volume
        return vol / q_m3s / 60
```

**Operating envelope — key numbers for your basin:**

| Flow (MGD) | u_inlet (ft/s) | u_inlet (m/s) | SOR (gpm/ft²) | SOR (m/h) | Det. Time Sed (min) | Det. Time Floc (min) |
|------------|----------------|---------------|----------------|-----------|---------------------|---------------------|
| 5 | 0.012 | 0.0036 | 0.058 | 0.14 | 231 | 115 |
| 10 | 0.023 | 0.0071 | 0.116 | 0.28 | 115 | 58 |
| 20 | 0.047 | 0.0143 | 0.231 | 0.56 | 58 | 29 |
| 30 | 0.070 | 0.0214 | 0.347 | 0.85 | 38 | 19 |
| 40 | 0.094 | 0.0286 | 0.463 | 1.13 | 29 | 14 |

These are very low velocities. At 40 MGD, the mean velocity is under 0.1 ft/s. This means:
- Reynolds number based on depth: Re = u × D / ν ≈ 0.029 × 3.35 / 1e-6 ≈ 97,000 — turbulent, so RANS is appropriate
- Froude number: Fr = u / √(gD) ≈ 0.029 / √(9.81 × 3.35) ≈ 0.005 — free surface effects negligible (confirms symmetry BC is fine)
- At 5 MGD, Re ≈ 12,000 — still turbulent but approaching transitional; the low-Re correction in k-ω SST handles this well

**Mesh generation (mesh_generator.py):**

```python
import numpy as np

class BasinMesh:
    """Structured mesh with local refinement for SVWTP basin."""

    def __init__(self, basin, include_floc=False):
        self.basin = basin
        if include_floc:
            self.L = basin.floc_length + basin.sed_length
            self.floc_sed_boundary = basin.floc_length
        else:
            self.L = basin.sed_length
            self.floc_sed_boundary = 0.0
        self.H = basin.sed_depth

    def generate(self, base_dx=0.1, base_dz=0.05, refine_zones=None):
        """Generate non-uniform structured mesh.

        refine_zones: list of dicts with keys:
            x_start, x_end: longitudinal extent (m)
            z_start, z_end: vertical extent (m)
            factor: refinement factor (2 = double resolution)
        """
        # Build non-uniform x coordinates
        x_coords = self._build_nonuniform_1d(
            0, self.L, base_dx, refine_zones, axis='x'
        )
        z_coords = self._build_nonuniform_1d(
            0, self.H, base_dz, refine_zones, axis='z'
        )

        self.x = x_coords
        self.z = z_coords
        self.nx = len(x_coords) - 1
        self.nz = len(z_coords) - 1

        # Cell centers
        self.xc = 0.5 * (x_coords[:-1] + x_coords[1:])
        self.zc = 0.5 * (z_coords[:-1] + z_coords[1:])

        # Cell sizes
        self.dx = np.diff(x_coords)
        self.dz = np.diff(z_coords)

        return self

    def _build_nonuniform_1d(self, start, end, base_d, zones, axis):
        """Build 1D coordinate array with local refinement."""
        # Start with uniform mesh
        n_base = int(np.ceil((end - start) / base_d))
        coords = np.linspace(start, end, n_base + 1)

        if zones is None:
            return coords

        # Insert refined points in specified zones
        for zone in zones:
            x0 = zone.get(f'{axis}_start', start)
            x1 = zone.get(f'{axis}_end', end)
            factor = zone.get('factor', 2)
            refined_d = base_d / factor
            zone_coords = np.arange(x0, x1, refined_d)
            coords = np.unique(np.sort(np.concatenate([coords, zone_coords])))

        return coords

    def default_refinement_zones(self):
        """Standard refinement for SVWTP sed basin."""
        return [
            # Inlet zone
            {'x_start': 0, 'x_end': 6.0, 'factor': 4},
            # Plate settler zone (estimate location)
            {'x_start': 70, 'x_end': 95, 'factor': 2},
            # Launder/outlet zone
            {'x_start': 95, 'x_end': self.L, 'factor': 4},
            # Near bottom (sludge zone)
            {'z_start': 0, 'z_end': 0.5, 'factor': 2},
            # Near surface (launder zone)
            {'z_start': self.H - 0.5, 'z_end': self.H, 'factor': 2},
        ]
```

**RTD Analysis (rtd_analysis.py):**

```python
import numpy as np
from scipy.integrate import cumulative_trapezoid

class RTDAnalyzer:
    """Compute RTD metrics from tracer breakthrough curve."""

    def __init__(self, time, concentration):
        """
        time: array of time values (seconds)
        concentration: array of tracer concentration at outlet (0 to 1 for step input)
        """
        self.t = np.asarray(time)
        self.c = np.asarray(concentration)

        # Normalize if needed
        if self.c.max() > 1.01:
            self.c = self.c / self.c.max()

    @property
    def t10(self):
        """Time for 10% breakthrough (seconds)."""
        return np.interp(0.10, self.c, self.t)

    @property
    def t50(self):
        """Median residence time (seconds)."""
        return np.interp(0.50, self.c, self.t)

    @property
    def t90(self):
        """Time for 90% breakthrough (seconds)."""
        return np.interp(0.90, self.c, self.t)

    def baffling_factor(self, t_theoretical):
        """t10/T — key metric for CT compliance."""
        return self.t10 / t_theoretical

    def morrill_index(self):
        """t90/t10 — dispersion indicator. Ideal plug = 1.0."""
        return self.t90 / self.t10

    def volumetric_efficiency(self, t_theoretical):
        """t50/T — fraction of basin volume effectively used."""
        return self.t50 / t_theoretical

    def dead_zone_fraction(self, t_theoretical):
        """Estimated dead volume = 1 - volumetric efficiency."""
        return 1.0 - self.volumetric_efficiency(t_theoretical)

    def tanks_in_series(self, t_theoretical):
        """Equivalent N for CSTRs-in-series model."""
        # From variance of RTD
        # E(t) = dF/dt where F(t) = C(t) for step input
        e_t = np.gradient(self.c, self.t)
        mean_t = np.trapz(self.t * e_t, self.t)
        var_t = np.trapz((self.t - mean_t)**2 * e_t, self.t)
        sigma_theta_sq = var_t / mean_t**2
        return 1.0 / sigma_theta_sq if sigma_theta_sq > 0 else float('inf')

    def summary(self, t_theoretical):
        """Print all metrics."""
        return {
            't10_min': self.t10 / 60,
            't50_min': self.t50 / 60,
            't90_min': self.t90 / 60,
            'baffling_factor': self.baffling_factor(t_theoretical),
            'morrill_index': self.morrill_index(),
            'volumetric_efficiency': self.volumetric_efficiency(t_theoretical),
            'dead_zone_fraction': self.dead_zone_fraction(t_theoretical),
            'tanks_in_series_N': self.tanks_in_series(t_theoretical),
        }
```

**Configuration comparison (comparison_table.py):**

```python
import pandas as pd

class RetrofitComparison:
    """Compare multiple baffle/launder configurations."""

    def __init__(self):
        self.results = []

    def add_result(self, config_name, flow_mgd, metrics_dict):
        """Add one simulation result."""
        row = {'configuration': config_name, 'flow_mgd': flow_mgd}
        row.update(metrics_dict)
        self.results.append(row)

    def to_dataframe(self):
        return pd.DataFrame(self.results)

    def rank_configurations(self, metric='baffling_factor', ascending=False):
        """Rank configurations by chosen metric, averaged across flows."""
        df = self.to_dataframe()
        ranked = (df.groupby('configuration')[metric]
                    .mean()
                    .sort_values(ascending=ascending))
        return ranked

    def robustness_score(self, metrics=None, weights=None):
        """Score each config on multiple metrics across all flows.

        Returns a score where higher = better.
        """
        if metrics is None:
            metrics = ['baffling_factor', 'volumetric_efficiency']
            weights = [0.6, 0.4]

        df = self.to_dataframe()
        scores = {}
        for config in df['configuration'].unique():
            cfg_data = df[df['configuration'] == config]
            score = 0
            for metric, weight in zip(metrics, weights):
                # Normalize each metric to 0-1 range across all configs
                all_vals = df[metric]
                normalized = (cfg_data[metric].mean() - all_vals.min()) / (all_vals.max() - all_vals.min() + 1e-10)
                score += weight * normalized
            scores[config] = score

        return pd.Series(scores).sort_values(ascending=False)
```

### Track 2: OpenFOAM for 3D Validation and Complex Geometry

When you need 3D — specifically for launder configurations where lateral flow distribution matters — use OpenFOAM. Here is the setup specific to your basin.

**Case directory structure:**

```
svwtp_sed_basin/
├── 0/                          # Initial conditions
│   ├── U                       # Velocity field
│   ├── p                       # Pressure
│   ├── k                       # Turbulent kinetic energy
│   ├── omega                   # Specific dissipation rate
│   └── tracer                  # Passive scalar for RTD
├── constant/
│   ├── transportProperties     # Fluid properties
│   ├── turbulenceProperties    # k-omega SST selection
│   └── polyMesh/               # Mesh files
├── system/
│   ├── controlDict             # Time stepping, output control
│   ├── fvSchemes                # Discretization schemes
│   ├── fvSolution              # Solver settings, SIMPLE parameters
│   ├── blockMeshDict           # Mesh generation
│   ├── snappyHexMeshDict       # Optional: complex geometry meshing
│   └── topoSetDict             # Define plate settler porous zone
└── run.sh                       # Job submission script
```

**Key OpenFOAM settings for your basin:**

Solver: simpleFoam (steady-state) for baseline flow field, then scalarTransportFoam or a custom tracer solver for RTD.

Turbulence: kOmegaSST in turbulenceProperties.

For the porous zone (plate settlers), define in the fvOptions file:

```
plateSettlers
{
    type            explicitPorositySource;
    active          true;
    explicitPorositySourceCoeffs
    {
        selectionMode   cellZone;
        cellZone        plateSettlerZone;
        type            DarcyForchheimer;
        d   (1e6 1e4 1e6);    // 1/m² — high resistance perpendicular to plates
        f   (100 10 100);      // 1/m  — inertial resistance
        coordinateSystem
        {
            type    cartesian;
            origin  (0 0 0);
            e1      (0.866 0 0.5);     // along plate direction (60° from horizontal)
            e2      (0 1 0);           // lateral (spanwise)
        }
    }
}
```

Calibrate d and f so that pressure drop matches measured headloss.

**Python-OpenFOAM integration:**

Use PyFoam or write simple Python scripts to:
1. Generate blockMeshDict parametrically (vary baffle positions, launder locations)
2. Run OpenFOAM cases in batch
3. Parse log files for convergence
4. Read results using VTK/pyvista for post-processing

```python
import subprocess
import os

class OpenFOAMRunner:
    """Manage OpenFOAM simulations for SVWTP basin studies."""

    def __init__(self, base_case_dir, results_dir):
        self.base_case = base_case_dir
        self.results_dir = results_dir

    def create_case(self, config_name, modifications):
        """Clone base case and apply modifications."""
        case_dir = os.path.join(self.results_dir, config_name)
        subprocess.run(['cp', '-r', self.base_case, case_dir])

        # Apply modifications (baffle position, launder config, flow rate)
        for file_path, replacements in modifications.items():
            full_path = os.path.join(case_dir, file_path)
            with open(full_path, 'r') as f:
                content = f.read()
            for old, new in replacements.items():
                content = content.replace(old, new)
            with open(full_path, 'w') as f:
                f.write(content)

        return case_dir

    def run_case(self, case_dir, solver='simpleFoam', np=4):
        """Run OpenFOAM case."""
        cmd = f'cd {case_dir} && mpirun -np {np} {solver} -parallel'
        subprocess.run(cmd, shell=True, check=True)

    def extract_rtd(self, case_dir):
        """Extract tracer breakthrough from OpenFOAM probes."""
        probe_file = os.path.join(case_dir, 'postProcessing',
                                  'probes', '0', 'tracer')
        data = np.loadtxt(probe_file, skiprows=1)
        return data[:, 0], data[:, 1]  # time, concentration
```

---

## Validation Using Your Available Data

You mentioned access to real-time and historical data. Here is how to use it:

### Validation Level 1: Hydraulic Validation (No New Tests Required)

Compare model-predicted headloss across the basin to measured headloss from your SCADA system. Most plants record upstream and downstream water levels — the difference is the total headloss. If the model matches measured headloss within ±20%, the hydraulics are reasonably calibrated.

### Validation Level 2: Tracer Test (Recommended — One-Time Effort)

Run a lithium chloride tracer test on one basin at one flow rate. This provides the gold-standard RTD for model validation.

**Protocol:**
1. Choose a steady-state flow rate (your most common operating flow)
2. Inject a known mass of LiCl at the basin inlet as a slug
3. Sample effluent at 5-minute intervals for 2–3× the theoretical detention time
4. Analyze for lithium by ICP-OES or flame photometry
5. Plot the breakthrough curve
6. Compute t₁₀, t₅₀, t₉₀, Morrill Index, baffling factor

**Model validation:** Run the identical tracer injection in the model. Compare the model RTD curve to the measured RTD curve. The model should match:
- t₁₀ within ±15%
- t₅₀ within ±10%
- General shape of the breakthrough curve

If it does not match, adjust: (1) turbulent diffusion coefficient, (2) porous zone resistance for plate settlers, (3) inlet boundary condition profile. In that order.

### Validation Level 3: Turbidity Profile (Ongoing)

If you have turbidity probes at multiple points in the basin (or can install temporary probes), compare measured turbidity profiles to model-predicted solids concentration profiles. This validates the settling component (not just the hydraulics).

### Validation Level 4: SCADA Correlation (Continuous)

Build a dataset of:
- Flow rate (from SCADA)
- Influent turbidity (from online turbidimeter)
- Effluent turbidity (from online turbidimeter)
- Temperature (from SCADA)
- Coagulant dose (from SCADA)

Plot effluent turbidity versus flow rate at different temperatures. The model should reproduce this relationship. If the model can predict effluent turbidity versus flow within ±0.3 NTU at low turbidity and ±20% at high turbidity, it is operationally useful.

---

## Phased Implementation Roadmap

### Phase 1 (Weeks 1–4): Geometry and Baseline

**Goal:** Get the 2D model running for the existing basin configuration.

1. Build SVWTPBasin configuration from design drawings
2. Generate 2D mesh for the sed basin (340 ft × 11 ft cross-section)
3. Implement steady-state SIMPLE solver with k-ω SST
4. Run baseline at 3 flow rates (10, 20, 40 MGD)
5. Compute velocity fields, streamlines, dead zone fractions
6. Run transient tracer simulation at one flow rate
7. Compute baseline RTD metrics

**Deliverable:** Velocity contour plot and RTD curve for the existing configuration. If you have tracer test data, compare immediately.

### Phase 2 (Weeks 5–8): Baffle Parametric Study

**Goal:** Identify the best baffle configuration for your basin.

1. Implement baffle representations (solid wall, perforated wall as porous zone)
2. Run Configurations 1–6 from the baffle section above
3. Run each at 3 flow rates (5, 20, 40 MGD)
4. Compute all 5 metrics for each case
5. Build comparison table and rank configurations
6. Identify top 2 candidates for 3D validation (if needed)

**Deliverable:** Configuration comparison table with robustness scores. Clear recommendation for baffle type and position with supporting data.

### Phase 3 (Weeks 9–12): Launder Optimization

**Goal:** Identify the best launder configuration.

1. Implement launder representations as line sinks at specified positions
2. Run Configurations A–D from the launder section above
3. Focus on upwelling velocity at launder locations
4. Evaluate interaction with plate settlers
5. Check weir loading rates at all flows
6. Compare configurations

**Deliverable:** Launder recommendation with upwelling velocity maps.

### Phase 4 (Weeks 13–16): Combined Optimization and 3D Validation

**Goal:** Confirm the best combination works in 3D and across the full operating range.

1. Take top baffle + top launder combination
2. Build 3D OpenFOAM model of the basin
3. Run at 5 flow rates (5, 10, 20, 30, 40 MGD)
4. Validate 3D results against 2D results
5. Check for lateral non-uniformity that the 2D model missed
6. If tracer test is available, validate against field data
7. Document results and retrofit recommendation

**Deliverable:** Final retrofit recommendation with full 2D and 3D supporting analysis. Design parameters for the recommended configuration (baffle porosity, orifice size, launder length, spacing, weir height).

---

## What Success Looks Like

For this project to produce a useful retrofit recommendation, the model needs to demonstrate:

1. **Measurable improvement over baseline:** The recommended configuration should improve baffling factor by at least 0.1 (e.g., from 0.5 to 0.6) and/or reduce dead zone fraction by at least 10 percentage points.

2. **Robustness across operating range:** The recommendation should work well at 5 MGD turndown AND 40 MGD peak, not just at the design flow. Many basin retrofits optimize for one flow and degrade at others.

3. **Constructibility:** The recommended baffles and launders must be physically installable in a basin that is 60 ft wide, 11 ft deep, with existing plate settlers and reciprocating scrapers. Any baffle that interferes with scraper travel is dead on arrival.

4. **Operator confidence:** The model results must be presented with visible assumptions, stated limitations, and comparison to field data. An operator should be able to look at the velocity contour plot and say "that matches what I see in the basin."

The model is not a black box that produces a recommendation. It is a transparent tool that shows the physics of why one configuration works better than another. That is the OCWPE principle, and it applies to this project exactly as it applies to everything else you're building.
