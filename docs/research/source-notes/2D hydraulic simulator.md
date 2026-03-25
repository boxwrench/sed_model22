# Building a 2D hydraulic simulator for rectangular water treatment basins

**A depth-averaged 2D model on a structured Cartesian grid can deliver defensible comparative analysis of baffle configurations in rectangular sedimentation and flocculation basins — provided the modeler respects specific physical limits.** The approach works because these basins have large length-to-depth ratios (8–20:1), very low Froude numbers (Fr ~ 10⁻³), and predominantly horizontal flow when temperature differentials stay below ~0.5 °C. Three staged simulator versions — steady hydraulics, tracer transport, and simplified solids settling — map directly onto increasing equation complexity, each adding one transport equation layer atop the previous. The critical architectural decisions are turbulence closure level, baffle parameterization method, and advection scheme accuracy, because these three choices dominate both runtime and the simulator's ability to discriminate between basin configurations.

---

## 1. Governing equations scale from two to six coupled fields across versions

### Version 0.1 — Steady-state velocity field (2 momentum + 1 continuity equation)

The foundation is the 2D depth-averaged Reynolds-averaged Navier-Stokes system under a rigid-lid approximation. Since basin Froude numbers are extremely small, free-surface variations are negligible (millimeter scale versus meters of depth), and the pressure field replaces the free-surface elevation term.

**Continuity:**

∂U/∂x + ∂V/∂y = 0

**x-momentum:**

U ∂U/∂x + V ∂U/∂y = −(1/ρ) ∂P/∂x + ∂/∂x[ν_eff ∂U/∂x] + ∂/∂y[ν_eff ∂U/∂y] − (g n² |**V**| U) / h^(4/3)

**y-momentum:**

U ∂V/∂x + V ∂V/∂y = −(1/ρ) ∂P/∂y + ∂/∂x[ν_eff ∂V/∂x] + ∂/∂y[ν_eff ∂V/∂y] − (g n² |**V**| V) / h^(4/3)

Here U and V are depth-averaged velocity components, P is pressure, ν_eff = ν + ν_t is the effective viscosity (molecular plus turbulent), h is water depth, and n is Manning's roughness coefficient (**0.012–0.015 s/m^(1/3)** for smooth concrete). The bed friction sink term parameterizes the vertical shear that depth-averaging eliminates.

What this version intentionally neglects: all vertical velocity structure, free-surface dynamics, density effects, transient behavior, and scalar transport. These omissions are acceptable because Version 0.1 exists solely to visualize bulk flow patterns — jet penetration, recirculation zones, dead zones, and velocity uniformity across sections — for rapid geometric screening.

### Version 0.2 — Tracer transport and RTD (add 1 scalar transport equation)

On top of the converged steady velocity field, the transient advection-diffusion equation tracks a conservative tracer:

∂C/∂t + U ∂C/∂x + V ∂C/∂y = ∂/∂x[D_x ∂C/∂x] + ∂/∂y[D_y ∂C/∂y]

The effective dispersion coefficient D_eff = ν_t/Sc_t + D_disp, where the turbulent Schmidt number **Sc_t ≈ 0.7–1.0** and the dispersion contribution from vertical velocity profile non-uniformity follows Elder's formula: D_disp ≈ 5.93 u* h. For typical basin conditions (U ~ 0.005 m/s, h ~ 3 m), D_eff ranges from **10⁻³ to 10⁻¹ m²/s**. A pulse tracer injected at the inlet produces the exit-age distribution E(t) at the outlet, from which all hydraulic efficiency metrics are computed.

### Version 0.3 — Solids settling proxy (add N particle-class transport equations)

For each particle class k with settling velocity v_s,k:

∂C_k/∂t + U ∂C_k/∂x + V ∂C_k/∂y = D_eff (∂²C_k/∂x² + ∂²C_k/∂y²) − (v_s,k / h) C_k

The **settling sink term −(v_s,k / h) C_k** is the depth-averaged representation of vertical particle removal: particles settling at velocity v_s,k through a water column of depth h are removed at rate v_s,k/h. This naturally recovers Hazen's ideal settling theory in the plug-flow limit, where all particles with v_s ≥ Q/A_s (the overflow rate) are fully removed. Using **5–10 particle classes** spanning the floc settling velocity range of 0.1–5 mm/s provides adequate resolution of the particle size distribution. For dilute suspensions typical in potable water treatment (<500 mg/L), the classes are independent and solved sequentially on the pre-computed flow field. Total removal is the weighted sum: η_total = Σ f_k · η_k.

Typical design overflow rates for conventional water treatment sedimentation are **20–40 m³/m²/day** (0.8–1.7 m/h). Floc apparent densities range from 1010–1100 kg/m³ (versus 2650 kg/m³ for primary clay particles), with Goula et al. (2008) using ρ_floc = 1066 kg/m³ for potable water treatment flocs.

### Turbulence closure — four levels of increasing fidelity

The choice of turbulence model is the single most consequential physics decision, affecting both solution quality and computational cost.

**Constant eddy viscosity** (ν_t = constant, typically **10⁻³ m²/s** for sedimentation basins): zero additional equations, trivial to implement, adequate for initial screening where relative ranking matters more than absolute accuracy. Published work by Imam et al. (1983) and Krebs et al. (1992, 1995) used this approach successfully for comparative studies.

**Smagorinsky-type model** (ν_t = (C_s Δ)² |S̄|, with C_s ≈ 0.1–0.2): provides spatially variable eddy viscosity proportional to local strain rate. Used in TELEMAC-2D and effective for capturing shear-generated turbulence near baffles. No additional transport equations, modest implementation effort.

**Mixing length model** (ν_t = l_m² |∂U/∂y|): depth-limited mixing length l_m ≈ 0.07–0.09 h, with near-wall behavior l_m = κy (κ = 0.41). Elder's depth-averaged value gives ν_t ≈ 0.067 u* h. Appropriate for channel-dominated flows between baffles.

**Depth-averaged k-ε** (Rastogi & Rodi 1978): adds two transport equations for turbulent kinetic energy k and dissipation rate ε, with ν_t = C_μ k²/ε. Standard constants: C_μ = 0.09, C_1ε = 1.44, C_2ε = 1.92, σ_k = 1.0, σ_ε = 1.3. Includes bed-generated production terms unique to depth-averaging. This has been the dominant approach in sedimentation basin CFD since the foundational work of Celik, Adams, Stamou, and Rodi in the 1980s and remains the standard. Typical inlet boundary values: turbulence intensity **5–10%** (k = 1.5(I·U_in)²) and turbulent length scale 0.07 × hydraulic diameter.

For Version 0.1 screening, constant ν_t suffices. For Version 0.2 RTD studies where recirculation zone size directly affects metrics, the Smagorinsky model or k-ε is justified. The k-ε model adds ~50% to implementation effort and ~100% to runtime but significantly improves predictions of flow separation behind baffles.

---

## 2. Baffle representation methods range from trivial to sophisticated

### Solid full-depth baffles align naturally with structured grids

On a Cartesian staggered grid, a grid-aligned full-depth baffle is represented by **setting the normal velocity component to zero** at all cell faces lying on the baffle surface. This is the simplest and most robust approach — no special data structures, no additional parameters. The tangential velocity follows the chosen wall condition (no-slip or free-slip).

For baffles not aligned with grid lines, three options exist in order of increasing complexity. **Blocked-cell (staircase) approximation** marks cells occupied by the baffle as solid, introducing geometric error proportional to cell size and artificial roughness at stepped boundaries. **Immersed boundary methods** add a body force to momentum equations near the boundary — the discrete-forcing (ghost-cell) variant provides sharp boundary representation with second-order accuracy. **Cut-cell approaches** reshape intersected cells to match the actual geometry, providing exact conservation but requiring more complex bookkeeping.

For rectangular basins where around-the-end baffles run parallel to grid lines, the simple zero-flux approach is entirely adequate and should be the default.

### Partial-depth curtain baffles require a resistance parameterization

The fundamental challenge is that a partial-depth baffle — a hanging curtain or underflow wall — creates a depth-varying obstruction that a single depth-averaged velocity cannot resolve. The practical 2D solution is a **localized momentum sink** producing equivalent head loss.

For a submerged opening with area ratio β = A_opening/A_total and discharge coefficient C_d ≈ 0.61 (sharp-edged), the loss coefficient is:

K = (1/(C_d · β))² − 1

This is applied as a drag source term S_x = −K ρ u|u| / (2Δx) in the momentum equation at the baffle location. For example, a baffle extending 60% of the depth (β = 0.4) with C_d = 0.61 gives K ≈ 15.7 — a substantial but physically correct resistance. Calibration against 3D CFD or physical tracer tests is recommended for quantitative work.

### Perforated baffles use Darcy-Forchheimer porous resistance

Perforated distribution baffles are modeled as porous zones with a momentum sink:

S_i = −(μ/K + ½ρ C₂ |u|) u_i

where K is permeability and C₂ is the inertial resistance factor. For thin sharp-edged perforated plates, the **Idelchik correlation** provides the pressure loss coefficient as a function of open area ratio φ:

k = [0.707(1−φ)^0.375 + 1 − φ²]² / φ²

Practical values: φ = 0.40 gives k ≈ 8.0; φ = 0.50 gives k ≈ 3.5; φ = 0.30 gives k ≈ 24. The Forchheimer coefficient f = k/L, where L is the plate thickness. In the 2D implementation, the normal-direction resistance uses these computed values while the tangential resistance should be set **10× higher** to prevent unrealistic lateral flow through the porous zone.

### Turning vanes and guide structures reduce dead zones substantially

Turning vanes at serpentine bends are modeled as thin internal walls partitioning the flow channel. A single turning vane at a 90° bend reduces pressure loss by **50–70%**; 3–5 evenly spaced vanes provide optimal flow uniformity. Wilson and Venayagamoorthy (2010) showed that increasing the number of around-the-end baffles improves the baffling factor from ~0.1 (unbaffled) to 0.7–0.9 (6+ baffles), with optimal channel aspect ratios of 3–6:1. Dead zones form in corners behind baffles due to flow separation; guide vanes at corners significantly reduce these.

---

## 3. Boundary conditions control both stability and physical realism

**Inlet conditions** are specified as velocity inlet: U = Q/(B·H) distributed uniformly across the inlet width. For k-ε models, turbulence boundary values use inlet intensity I = 5–10% and length scale ℓ = 0.07 × inlet hydraulic diameter. Whether the inlet is a full-width slot or a concentrated pipe significantly affects jet penetration and initial mixing; a perforated inlet baffle positioned at **0.06–0.13 of basin length** provides optimal energy dissipation per Tamayol et al. (2008).

**Outlet weirs** follow the Francis formula for suppressed rectangular weirs: Q = 1.84 · L_w · H^(3/2) (SI units). For submerged conditions, the Villemonte correction applies: Q_sub = Q_free · [1 − (H_d/H_u)^1.5]^0.385. Distributed launders with multiple orifices are modeled as line sinks: Q_orifice = C_d · A_o · √(2g·Δh) with C_d = 0.60–0.62. In practice, a uniform distributed outflow weighted by local head is often adequate for the 2D representation.

**Wall conditions** depend on basin geometry. For wide basins (width-to-depth ratio > 5), **free-slip sidewalls combined with Manning bed friction** is appropriate because bed friction dominates. For narrow baffled channels (width-to-depth < 3), no-slip sidewalls with wall functions become important for capturing boundary layers and corner recirculation. Manning's n = 0.012–0.015 for smooth concrete.

The outlet boundary condition most affects stability: zero-gradient (Neumann) conditions can cause instability if recirculation exists at the outlet plane. A pressure-outlet or weir-equation formulation is more robust.

---

## 4. Performance metrics must discriminate between configurations

### RTD-derived indicators provide the core comparison framework

The residence time distribution E(t) is computed by injecting a pulse tracer at the inlet and monitoring flux-weighted outlet concentration:

E(t) = C_out(t) / ∫₀^∞ C_out(t) dt

From the cumulative distribution F(t) = ∫₀ᵗ E(t') dt', the key indices are extracted:

**Baffling factor t₁₀/τ** (where τ = V/Q is nominal detention time) is the primary regulatory metric. The US EPA classification assigns: unbaffled = 0.1, poor = 0.3, average = 0.5, superior = 0.7, perfect plug flow = 1.0. Well-designed baffled basins target **t₁₀/τ ≥ 0.5–0.7**. Teixeira and Siqueira (2008) evaluated 14 hydraulic indices and recommended t₁₀ as the single best short-circuiting indicator due to its correlation with physical performance and statistical reproducibility.

**Morrill Index** Mo = t₉₀/t₁₀ characterizes the spread of the RTD. Perfect plug flow gives Mo = 1.0; an ideal CSTR gives Mo = 22. Values below 2.0 indicate good plug-flow character. Published values for rectangular sedimentation basins range from **3.2 to 6.1** for typical configurations.

**Effective volume ratio** e = t_mean/τ quantifies dead-zone fraction: if e = 0.7, approximately 30% of basin volume is stagnant. Dead zones can also be mapped spatially from the velocity field by flagging cells where |u| < 5–10% of mean velocity.

**Persson hydraulic efficiency index** λ = e · (1 − 1/N) combines volumetric utilization and flow uniformity into a single metric, where N = t_mean²/σ² is the equivalent number of tanks-in-series. Classification: good (λ > 0.75), satisfactory (0.50–0.75), poor (≤ 0.50).

### Solids removal proxies connect hydraulics to treatment

For discrete settling, removal efficiency integrates over the RTD: η = ∫₀^∞ E(t) · min(1, v_s·t/H) dt. This accounts for the actual distribution of residence times rather than assuming ideal plug flow. The effective overflow rate accounting for dead zones is v_c,eff = Q/(A_s · e), which for a basin with 30% dead zones is **43% higher** than the nominal value — a substantial performance penalty.

For comparing baffle configurations, a composite scorecard using t₁₀/τ, Morrill Index, effective volume ratio, and the Persson index provides robust discrimination. Single metrics can be deceptive; a configuration might improve t₁₀ while worsening dead-zone fraction, for instance.

---

## 5. Some simplifications are safe for design screening; others are treacherous

### Safe simplifications for comparative baffling studies

**2D depth-averaging** is defensible when the basin has L:H > 8–10, the inlet spans the full width, temperature differentials are below ~0.5 °C, and no over/under baffles create dominant vertical flow. Stamou et al. (1989) and Goula et al. (2008) validated 2D approaches for primary rectangular clarifiers under these conditions.

**Rigid-lid approximation** is universally safe for sedimentation basins: free-surface variations are millimeters when Froude numbers are O(10⁻³).

**Steady-state flow assumption** is valid when inflow rate and temperature change slowly compared to the hydraulic residence time (typically 1–4 hours). The velocity field equilibrates within 2–5 residence times from initial conditions.

**Constant eddy viscosity** is acceptable for initial screening where the goal is ranking configurations, not predicting absolute performance. Results should be interpreted as qualitative.

**Ignoring wind** is always safe for covered or indoor basins. Stamou and Gkesouli (2015) showed wind reduced settling efficiency from 72.5% to 68.1% for uncovered basins — a significant but not dominant effect.

### Dangerous simplifications that produce misleading conclusions

**Ignoring density currents** is the single most dangerous simplification. Goula et al. (2008b) demonstrated that **a temperature difference of just 1 °C** between influent and tank contents is sufficient to generate a density current. Gerges and McCorquodale (1998) showed effects at 0.2 °C from surface cooling alone. Density currents create bottom-hugging short-circuit paths and surface return flows that a depth-averaged model cannot represent. During seasonal temperature transitions, this effect dominates basin performance.

**Mono-disperse particle settling** masks the differential removal that discriminates between designs. Real floc distributions span orders of magnitude (5 μm colloids to 300+ μm macro-flocs). Al-Sammarraee and Chan (2009) used 13 particle classes and showed large particles settle near the inlet while small particles redistribute with recirculation — behavior invisible to a single settling velocity. **Always use at least 5 particle classes.**

**First-order upwind advection** introduces artificial diffusion proportional to cell size that directly undermines the simulator's purpose: it makes different designs appear more similar than they are by smearing concentration gradients. This is worst when flow is at **45° to grid lines**. The minimum acceptable scheme is second-order upwind or a TVD limiter (Van Leer, Superbee).

**Neglecting floc shear sensitivity** can mislead when comparing inlet configurations. Flocs break up at shear rates G > 100–500 s⁻¹, and alum/polyaluminum chloride flocs show **irreversible breakup** with limited re-growth. Inlet velocities must stay below ~0.15 m/s to prevent breakup.

### When 2D depth-averaging breaks down entirely

The 2D assumption fails when any of these conditions exist: temperature differentials > 0.5 °C, over/under baffle configurations requiring vertical flow resolution, significant wind shear on uncovered basins, sludge blanket dynamics with non-Newtonian rheology, or inlet jets with strong vertical momentum. For around-the-end (horizontal serpentine) baffling in a covered basin with controlled temperature, 2D remains defensible.

---

## 6. Validation builds credibility through staged evidence

### Mesh convergence is non-negotiable

Richardson extrapolation with three grids at refinement ratio r ≥ 1.3 (e.g., Δx = 1.0, 0.5, 0.25 m) establishes discretization error bounds. The Grid Convergence Index GCI = F_s · |ε₁₂| / (r^p − 1), where p is the observed convergence order and F_s = 1.25 for three-grid studies. Target **GCI < 5%** for t₁₀ and mean velocity. Mass balance verification (tracer mass in = mass out within 1%) and temporal convergence for RTD simulations are essential checks.

The parameters that dominate uncertainty, in order: grid resolution (affects numerical diffusion and RTD shape), turbulence model choice (affects recirculation zone size), inlet velocity profile assumption (affects jet penetration), and turbulent Schmidt number (affects tracer dispersion). Wall roughness and outlet conditions are secondary.

### Published datasets provide quantitative benchmarks

Several experimental datasets exist for rectangular sedimentation basin validation. **Lyn and Rodi (1990)** provide laser-Doppler velocimetry measurements in a model settling tank — the most widely cited validation case. **Adams and Rodi (1990)** measured flow-through curves for various inlet arrangements. **Stamou, Adams, and Rodi (1989)** provide numerical and experimental data for primary rectangular clarifiers. **Goula et al. (2008)** validated CFD against real potable water treatment plant settling efficiency. **Rebhun and Argaman (1965)** published pilot-basin F(t) curves with flow decomposition into plug, mixed, and dead fractions. **Shahrokhi et al. (2012)** provide ADV velocity measurements with different baffle numbers.

Comparison with the tanks-in-series model fitted to the simulated RTD provides a single-parameter (N) validation check. Typical values: unbaffled N ≈ 1–3, moderately baffled N ≈ 3–8, well-baffled serpentine N ≈ 8–20+. The Hazen ideal settling efficiency provides a theoretical upper bound; the ratio η_CFD/η_Hazen (typically **0.3–0.7 unbaffled, 0.6–0.9 baffled**) quantifies non-ideal flow impact.

### A four-phase credibility strategy

Phase 1 (verification) confirms the code solves equations correctly: analytical benchmarks (Poiseuille flow, Stokes settling), mesh convergence, mass conservation. Phase 2 (qualitative validation) checks that flow patterns match expected physics: inlet jet deflection, corner recirculation, boundary layer growth. Phase 3 (quantitative benchmarking) compares RTD metrics against published ranges and tanks-in-series fits. Phase 4 (sensitivity analysis) documents which inputs most affect outputs and reports uncertainty bands.

---

## 7. Custom Python versus established solvers — a pragmatic comparison

### Path A: Python custom solver delivers transparency and scripting

A 2D Navier-Stokes solver built on NumPy/SciPy using the **projection (fractional step) method** on a staggered MAC grid is the most tractable custom approach. The algorithm: (1) compute intermediate velocity from momentum equations ignoring pressure, (2) solve the pressure Poisson equation ∇²p = (ρ/Δt)∇·u* using SciPy sparse solvers, (3) correct velocity to enforce divergence-free field. Baffles are trivially implemented by zeroing normal velocities at internal cell faces.

Performance is adequate: SciPy's sparse direct solver handles the Poisson equation for a **200 × 60 grid (12,000 cells, representing a 100 m × 30 m basin at 0.5 m resolution) in 5–50 ms per solve**. With explicit time stepping (CFL-limited Δt ~ 0.1–1 s), reaching pseudo-steady state requires 1,000–10,000 time steps, giving total runtimes of **1–30 minutes** on a laptop. Iterative solvers (conjugate gradient) and algebraic multigrid (PyAMG) provide further acceleration.

Total implementation requires approximately **800–1,500 lines of Python**: ~500 lines for the core solver, ~150 for boundary conditions and baffles, ~150 for tracer transport, ~200 for post-processing. Development time: 2–4 weeks for an experienced Python developer with CFD knowledge, 4–8 weeks learning from Lorena Barba's "CFD Python: 12 Steps to Navier-Stokes" course. The SIMPLE algorithm is an alternative for steady-state problems, requiring typical under-relaxation factors of α_velocity = 0.5–0.7, α_pressure = 0.3.

The primary advantages are complete transparency (every discretization visible), native Python scripting for parametric automation (trivial to loop over 50 baffle configurations), and zero installation complexity. The primary limitations are no built-in turbulence model (elevated constant ν_t is the practical workaround), structured-grid restriction (baffles must align with grid lines), and pure Python performance ceiling (~100–1000× slower than compiled code, though NumPy vectorization closes much of this gap).

### Path B: Established solvers trade transparency for capability

**OpenFOAM** is the strongest technical candidate. The `simpleFoam` solver handles steady RANS; `pimpleFoam` handles transient. A 2D setup uses a single cell in z with `empty` boundary conditions. The `createBaffles` utility generates zero-thickness internal walls. Full k-ε and k-ω SST turbulence modeling is built in. Direct precedent exists: Hatari Labs published a settling tank tutorial using `driftFluxFoam`, and multiple published studies use OpenFOAM for sedimentation optimization. PyFoam and foamlib enable Python-driven parametric studies. For the target basin problem, runtime is **seconds to minutes**. The learning curve is significant (1–3 weeks to first result, 3–4 weeks for full parametric workflow), and the file-based case setup on Linux can be intimidating.

**Delft3D** offers the best native baffle support through its **thin dam feature** — specified by grid coordinates, blocking velocity components along grid lines. The structured curvilinear grid is natural for rectangular basins. 3D sigma layers can resolve vertical flow if needed. Sediment transport is integrated. Scripting via text-based input files is workable but less elegant than Python. Time to first result: 1–2 weeks.

**HEC-RAS 2D** is free and widely used but designed for rivers and floodplains, not engineered basins. Internal structures are possible through SA/2D connections, but the workflow is awkward for parametric baffling studies. Limited Python scripting via COM interface. Not recommended as the primary platform.

**TELEMAC-2D** offers finite element solving with a Python API (TelApy) and has been used for reservoir sedimentation, but the steep learning curve (Fortran compilation, complex dependencies) and unstructured triangular mesh make it over-engineered for simple rectangular basins.

**SRH-2D** from the Bureau of Reclamation includes sediment transport and obstruction modules, but depends on the SMS GUI (Aquaveo) for full functionality, limiting automation. No official technical support.

### The recommended hybrid strategy

Start with a **custom Python solver** for Version 0.1 and early Version 0.2 — the transparency, learning value, and scripting convenience are unmatched for rapid baffle screening. Graduate to **OpenFOAM** for validation, turbulence-resolved studies, and Version 0.3 refinement. Use OpenFOAM's 2D capability to cross-validate the Python solver's results on selected configurations, building confidence in the simpler tool. Consider **Delft3D** if shallow-water dynamics or integrated sediment transport become priorities.

| Criterion | Custom Python | OpenFOAM | Delft3D |
|---|---|---|---|
| Time to first baffle comparison | 2–4 weeks | 2–3 weeks | 1–2 weeks |
| Parametric scripting ease | ★★★★★ | ★★★★ | ★★★ |
| Turbulence modeling | Constant ν_t only | Full RANS/LES | k-ε, mixing length |
| Baffle flexibility | Grid-aligned only | Any geometry | Thin dams (grid-aligned) |
| Runtime (100m × 30m, 0.5m grid) | 1–30 min | Seconds–minutes | Minutes |
| Vertical flow resolution | No | Yes (3D) | Yes (sigma layers) |
| Learning value | ★★★★★ | ★★★★ | ★★★ |
| Long-term maintainability | Self-maintained | Community-maintained | Deltares-maintained |

---

## 8. Failure modes cluster into numerical, conceptual, and workflow categories

### Numerical failure modes and their mitigations

**CFL violation** is the most common crash cause in explicit schemes. For shallow-water equations, the gravity wave speed √(gh) ≈ 3–5 m/s dominates over flow velocity (~0.01 m/s), requiring Δt ≤ Δx/√(gh). At Δx = 0.5 m and h = 3 m, this gives Δt ≤ 0.09 s — 200,000 steps to simulate one hour. The fix: implicit time integration for steady-state, which removes the CFL restriction entirely for stability (though accuracy still benefits from CFL < 5–10).

**Pressure-velocity decoupling** on collocated grids produces checkerboard pressure oscillations. Rhie-Chow momentum interpolation is the standard remedy, adding a pressure-gradient correction to face velocities. On staggered grids, this problem does not exist — another argument for the MAC arrangement in custom solvers.

**Numerical diffusion from first-order upwind** is arguably the most insidious failure because it silently degrades the tool's ability to discriminate between designs. Detection: if results change substantially with grid refinement, numerical diffusion dominates. Mitigation: use QUICK, second-order upwind, or TVD schemes (Van Leer, Superbee) as the minimum standard. The ERCOFTAC Best Practice Guidelines explicitly require at least second-order accuracy.

### Conceptual failure modes are harder to detect

**Excessive physics complexity** creates models with many uncertain parameters and diminishing returns. A model calibrated with 10+ parameters may reproduce historical data perfectly but fail under new conditions. The practical decision framework: Level 1 (constant ν_t, single particle class) for screening 10+ configurations; Level 2 (k-ε, 5–10 particle classes) for comparing 3–5 shortlisted designs; Level 3 (3D, full physics) for final validation of 1–2 candidates.

**Poor geometry parameterization** makes design exploration impractical. If changing a baffle position requires manual re-meshing, the tool fails its primary purpose. Solution: parameterize key dimensions from the start — baffle count, spacing, gap width, and position as input variables that automatically regenerate the computational grid.

**Weak metric design** can render the simulator useless for decision-making. A single metric like "removal efficiency" may not discriminate between configurations. The recommended scorecard (t₁₀/τ, Morrill Index, effective volume ratio, Persson index) provides multi-dimensional comparison that resists degenerate cases where one metric improves while another degrades.

**Skipping mesh convergence** leaves all results with unknown discretization error. This is the most common credibility gap in engineering CFD. The three-grid Richardson extrapolation procedure takes modest additional computational effort but provides quantitative error bounds. Following the AIAA G-077-1998 and ASME V&V 20-2009 standards transforms results from "simulation output" to "engineering evidence."

### Runtime failure is a design-tool killer

If each scenario takes hours rather than minutes, iterative exploration dies. The decoupled approach — solve the steady velocity field once, then run multiple tracer/particle simulations on it — is the key acceleration strategy. For Version 0.3, Goula et al. (2008) demonstrated that solving each particle class independently on a pre-computed flow field eliminates the need to re-solve hydrodynamics for each particle size. Combined with coarse-grid screening followed by fine-grid refinement of promising candidates, this keeps the design exploration loop within the target runtime of seconds to minutes per scenario.

---

## Conclusion

The three-version architecture maps cleanly onto equation complexity: **2+1 fields for velocity visualization, +1 for tracer RTD, +N for particle classes**. The critical insight is that most discriminating power for baffle comparison comes from Version 0.2's RTD metrics, not from Version 0.3's settling predictions — because short-circuiting indicators like t₁₀/τ and the Morrill Index are far more sensitive to geometric changes than settling efficiency, which is buffered by the particle size distribution.

The most underappreciated risk is numerical diffusion masquerading as physical mixing: a first-order scheme on a coarse grid can make a poorly baffled basin look nearly as good as a well-baffled one, defeating the simulator's purpose entirely. Using TVD advection schemes and performing grid convergence studies are not academic luxuries but functional requirements.

For the custom Python path, the staggered-grid projection method with SciPy sparse solvers is computationally tractable at the target resolution (12,000 cells in 1–30 minutes), and the ~1,200-line codebase is maintainable by a single engineer. The hybrid strategy — Python for rapid screening, OpenFOAM for validation and advanced physics — provides both the transparency needed for learning and the capability needed for defensible engineering conclusions. The key is to resist the temptation to add physics complexity before exhausting the insights available from simpler models validated against known benchmarks.