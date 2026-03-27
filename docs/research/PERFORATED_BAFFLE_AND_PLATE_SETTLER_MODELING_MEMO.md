# Modeling abstractions for a sedimentation basin comparison tool

## Executive Summary

- **The blocked transition wall almost certainly degrades basin performance.** A perforated wall's primary function is to distribute flow uniformly across the basin cross-section and into the plate settlers; blocking it with backer boards eliminates that function and likely creates short-circuiting, dead zones, and uneven settler loading.
- **A first-pass 3D RANS model with simplified geometry is the right tool** for comparing the original (open) vs. current (blocked) wall configurations. It is technically defensible, computationally practical, and produces the metrics that drive the decision.
- **Model the 8 orifices as resolved openings in a solid wall, not as a porous jump.** Eight orifices is too few to homogenize into a distributed resistance—each orifice creates a distinct jet that controls the downstream flow field. The porous-jump abstraction is valid only when hole count exceeds ~50.
- **Model the plate settlers as an anisotropic porous zone.** This captures the flow-redistribution and flow-straightening effect of the settler pack without resolving individual plates. The key coefficient is the viscous resistance along the plates: D = 12/w² where w is plate spacing.
- **The blocked wall should be modeled as a solid boundary.** This is the cleanest, most conservative representation and provides maximum contrast for the comparison.
- **Decision-useful outputs are flow uniformity at the settler entrance, RTD-derived short-circuiting indices (t₁₀/T, Morrill Index), dead zone fraction, and plate-settler approach velocity distribution.** These translate directly to treatment risk and are understandable by non-specialists.
- **Confidence in this approach is high.** The literature strongly supports every element. The main uncertainty is whether the blocked wall has leakage paths (gaps, deterioration after ~10 years) that a "perfectly solid" model would miss.
- **A tracer test and headloss measurement across the wall are the highest-value field data** for later model validation.

---

## Bottom-line recommendation for a first practical model

Build a **3D steady-state RANS CFD model** (k-ω SST turbulence) of one full basin at design flow (~40 MGD). Use three geometric abstractions:

| Basin element | Modeling abstraction | Rationale |
|---|---|---|
| **Original perforated wall (open)** | Solid wall with **8 discrete orifice openings** at documented positions | 8 orifices is too few for porous-jump homogenization; jet locations control the entire downstream flow field |
| **Current wall (backer boards)** | **Solid wall boundary** (no openings) | Represents the intended condition; add small leakage gaps in a sensitivity run only if field inspection finds deterioration |
| **Plate settlers** | **Anisotropic porous zone** (Darcy resistance) | Captures flow redistribution and straightening without plate-by-plate resolution; analytically derived coefficients |
| **Launders** | Distributed mass sinks or pressure outlet faces at documented launder locations | Captures the effect of launder placement on upflow velocity distribution |

Run both configurations with identical boundary conditions. Compare RTD curves (virtual tracer), velocity uniformity at settler entrance, and dead zone fractions. This model can be built and run in **1–2 weeks** with standard CFD tools (ANSYS Fluent, OpenFOAM, or FiPy/FEniCS per the existing project toolchain) and provides a technically defensible basis for the open-vs-blocked decision.

---

## System context and why it matters

This basin system—**60 ft wide × 340 ft long × 11 ft water depth**, fed by a 60 ft × 80 ft × 25 ft flocculation basin at **~40 MGD per basin** (160 MGD plant)—is a large, shallow rectangular sedimentation basin with high-rate inclined plate settlers. The aspect ratios are important: the length-to-depth ratio of **31:1** makes the basin highly sensitive to inlet flow distribution, and the width-to-depth ratio of **5.5:1** means lateral (cross-basin) flow effects are significant and cannot be ignored.

The perforated transition wall between the flocculation and sedimentation zones exists for a specific hydraulic reason: **it converts the concentrated flow from 8 inlet orifices into a distributed, low-velocity curtain** entering the settling zone. Without it, the 8 jets from the inlet orifices penetrate deep into the basin, creating preferential flow paths that bypass the plate settlers and reduce effective settling volume. The wall was blocked with backer boards approximately 10 years ago with no surviving documentation explaining why. The project goal is to determine whether restoring the original perforations would improve basin hydraulic performance—and to do so with a model that is both technically defensible and practically understandable.

The internal project framework confirms a Python-driven toolchain approach using FiPy or FEniCS, with the goal of identifying the **minimum physics** required for retrofit decisions. The framework's staged implementation plan (2D plan-view → 2D vertical → optimization) is sound, but the research below shows that the 8-orifice inlet and 5.5:1 width-to-depth ratio likely require **3D treatment** even at the screening stage.

---

## Perforated baffle modeling

### The literature strongly supports porous-interface abstractions—but not for 8 orifices

The "porous jump" boundary condition (ANSYS Fluent) or Darcy-Forchheimer momentum source (OpenFOAM, FiPy) is the standard CFD abstraction for perforated plates. The approach is well-validated in peer-reviewed water treatment literature. Kizilaslan, Demirel, and Aral (2018, 2020) used Darcy-Forchheimer porous baffles in OpenFOAM-based contact tank models and validated against experimental tracer studies with good agreement. Li, Davidson, and Peng (2023) demonstrated a novel Darcy-Forchheimer model for perforated plates with excellent experimental agreement. Alrawashdeh et al. (2020) directly compared porous-media CFD against exact-geometry CFD for perforated plates and found **~10–12% velocity error and ~12% pressure-drop error**—acceptable for screening.

The key equation for the pressure drop is straightforward. For turbulent flow through a perforated plate, the viscous (Darcy) term is negligible and the inertial loss dominates:

**ΔP = K · ½ρv²**

where K is the Idelchik loss coefficient, a function of the open-area ratio f and edge geometry. For sharp-edged orifices at high Reynolds number, the simplified form is K ≈ [(1−f)/f]² × correction factors from Idelchik's Handbook of Hydraulic Resistance (Chapter 8, Diagram 8-4).

### When aggregate open-area fraction is enough and when it is not

Malavasi et al. (2012) performed the definitive experimental study on this question, testing perforated plates with **3 to 52 holes**. The key finding: the pressure-loss coefficient decreases as hole count increases at constant open-area ratio, and this effect is **most pronounced at low hole counts**. For plates with fewer than ~15 holes, individual hole location, size, and elevation materially affect both pressure drop and downstream flow patterns. The reason is physics: few large orifices create discrete, spatially separated jets whose penetration depth, interaction, and lateral spreading dominate the basin flow field. A uniform porous resistance cannot capture these structures.

| Hole count | Recommended approach | Confidence |
|---|---|---|
| >50–100 | Porous jump / porous zone (excellent) | Very high |
| ~15–50 | Porous jump acceptable for screening; resolve for detail | High |
| <15 | **Resolve individual orifices** | High |
| 3–8 | **Must resolve individual orifices** | Very high |

**For this basin's 8 orifices, resolving individual openings is strongly recommended even for the first-pass model.** Each orifice in a 60 ft × 11 ft wall controls flow into a large fraction of the cross-section. The vertical position of orifices determines whether flow enters as a surface jet, mid-depth jet, or bottom jet—this fundamentally controls the velocity field, recirculation patterns, and settling zone performance. The computational cost of meshing 8 rectangular openings is trivial compared to the information lost by homogenizing them.

### Best abstractions for the two wall configurations

**Original perforated wall (open):** Model the transition wall as a solid wall (no-slip boundary) with **8 discrete openings at their documented locations** (elevation, lateral position, and dimensions from record drawings). No special porous boundary condition is needed—the loss coefficient is inherently captured by the flow contraction and expansion through each orifice. Each opening needs ~5–10 mesh cells across its smallest dimension.

**Current blocked wall (backer boards):** Model as a **completely solid wall** (no-slip boundary). This is the cleanest comparison. If field inspection reveals gaps, deterioration, or incomplete coverage after 10 years of service, run a sensitivity case with small leakage openings at those locations. A distributed low-porosity porous jump (<5% open area) could represent diffuse seepage, but this is speculative without field data.

**When a porous jump becomes the right choice:** If the project later evaluates a redesigned wall with many uniformly distributed ports (>50), the porous-jump abstraction becomes ideal for parametric optimization of open-area ratio. Typical sedimentation inlet wall open-area ratios in the literature range from **3–6%** for uniform flow distribution (Kawamura, 2000; Crittenden et al., 2012), though the project's internal framework references **~40%** for energy dissipation without jetting—a significant difference. The appropriate value depends on whether the goal is laminar flow equalization (low %) or active energy dissipation (high %).

---

## Plate settler / lamella modeling

### Anisotropic porous zone is the right basin-scale abstraction

Most published CFD studies of plate settlers resolve individual plates explicitly (Tarpagkou & Pantokratoras, 2014; Abeyratne et al., 2023; Takata & Kurose, 2017), which is computationally expensive and unnecessary for a basin-scale comparison model. The anisotropic porous zone approach is well-established in CFD practice for analogous geometries (tube banks, heat exchangers, structured packing) and captures the essential basin-scale physics: **flow alignment along plate channels, distributed pressure drop, suppression of cross-flow, and promotion of velocity uniformity** at the plate entrance.

No published paper was found that specifically validates a porous-zone model against a plate-resolved model for lamella settlers in water treatment. However, the physics is exact for the along-plate direction (Poiseuille flow between parallel plates), and the approach is recommended in ANSYS Fluent documentation and standard CFD practice guides (SimScale Knowledge Base).

### Deriving resistance coefficients from plate geometry

For laminar flow between parallel plates (the design regime for plate settlers, Re < 500–800), the **viscous (Darcy) term dominates** and the Forchheimer inertial term is negligible.

**Along-plate direction (low resistance):** D₁ = 12/w², where w is the plate-to-plate spacing. For typical spacings:

| Plate spacing | D₁ (viscous resistance) |
|---|---|
| 2 inches (50.8 mm) | **4,650 m⁻²** |
| 2.5 inches (63.5 mm) | 2,976 m⁻² |
| 3 inches (76.2 mm) | 2,067 m⁻² |

**Normal-to-plate direction (high resistance):** D₂ = 1,000 × D₁. This blocks cross-flow perpendicular to the plate channels. ANSYS documentation recommends limiting anisotropy to 2–3 orders of magnitude for numerical stability.

**Spanwise direction:** D₃ ≈ D₁ for plates without side walls (flow can move laterally along plate width).

**Inertial resistance:** Set to zero for all directions (laminar flow regime).

**Direction vectors** must be aligned with the plate inclination angle θ (typically 55–60° from horizontal): e₁ = (cos θ, sin θ, 0) along plates, e₂ = (−sin θ, cos θ, 0) normal to plates.

**Zone porosity:** ε = w/(w + t), where t is plate thickness. For stainless steel plates (t ≈ 3–5 mm) with 50–75 mm spacing, ε ≈ 0.93–0.96.

### What the porous zone captures and what it misses

The porous zone captures **flow redistribution** (the primary basin-scale effect), **velocity uniformity at the plate entrance**, and **suppression of large-scale recirculation**—exactly what matters for comparing two inlet configurations. The head loss through the plates themselves is extremely small (fractions of a millimeter at design velocities), confirming that the plates' hydraulic role is primarily **flow straightening**, not significant pressure drop.

What the porous zone cannot predict: individual channel flow profiles, particle trajectories within plates, sludge sliding dynamics, the Boycott effect, or settling efficiency. These require plate-resolved simulation and are not needed for the open-vs-blocked screening decision.

---

## Metrics that matter most

### Tier 1 metrics drive the decision

**Flow uniformity at the plate settler entrance** is the single most directly impacted metric. The perforated wall's primary purpose is to distribute flow uniformly; blocking it changes this fundamentally. Compute the coefficient of variation (CV = σ/μ) of velocity across the settler entrance face. Thresholds: **CV < 0.10 is good; CV > 0.25 is poor.**

**Plate settler approach velocity distribution** is the most performance-relevant downstream consequence. Uneven approach velocities mean some plate channels see excessive loading (risk of carryover) while others are underutilized. Standard design loading is **0.2–0.5 gpm/ft² of projected area** (0.3 gpm/ft² is the common design point). Velocity beneath plates should be **< 10 mm/s**.

**RTD-derived short-circuiting indices** have regulatory significance and strong literature backing. The key indices are:

- **Baffling factor (t₁₀/T):** The EPA standard. A perforated inlet baffle configuration qualifies as "superior baffling" (BF ≈ **0.7**); blocking the wall likely degrades this to "poor" or "average" (BF ≈ 0.3–0.5). Computed from a virtual tracer test in the CFD model.
- **Morrill Dispersion Index (t₉₀/t₁₀):** Values < 2.0 indicate effective plug flow; > 2.0 is poor. Teixeira and Siqueira (2008) identified this as one of the best mixing indicators after evaluating 14 hydraulic efficiency indices.
- **Dead zone fraction (1 − τ/T):** Tells stakeholders what fraction of their basin investment is doing nothing. Under 15% is good; **over 30% indicates poor design**.

### Tier 2 metrics add supporting evidence

Headloss across the wall (directly measurable, easy to validate), upwelling velocity near launders (determines floc carryover risk; should not exceed **3–5 mm/s**), settling-risk proxies (fraction of flow where upward velocity exceeds the critical particle settling velocity), and energy dissipation rate in the transition zone (velocity gradients G should taper from flocculation values of 10–70 s⁻¹ to near-zero in the settling zone; inlet velocities > **0.5 ft/s risk floc breakup**).

### Communicating results to non-specialists

Frame results as: (1) "X% of the basin is doing nothing" (dead zone fraction), (2) "The open wall gives us 38% more effective use of the basin" (baffling factor comparison), (3) "Some plate channels are getting 3× their design loading" (approach velocity distribution), and (4) side-by-side velocity heat maps at the settler entrance. Avoid presenting raw CFD fields without operational translation.

---

## What matters now vs. later

**Now (screening model):** The question is binary—does restoring the perforated wall materially improve basin hydraulics? This requires only **relative comparison** between configurations, not absolute performance prediction. Single-phase steady-state RANS with virtual tracer is sufficient. The model does not need to predict effluent turbidity or particle removal.

**Later (design model):** If the screening model shows significant benefit and the utility commits to a retrofit, the question becomes "what perforation pattern should we install?" This requires resolving individual perforations parametrically, validated particle tracking, and field-calibrated boundary conditions—a fundamentally different level of effort.

**The screening model is not a throwaway.** It establishes the velocity field, mesh, and boundary conditions that the design model builds upon. Investing in a clean 3D setup now pays forward directly.

---

## Recommended fidelity ladder

### V0.2 — Hand calculations and design check (hours, no software)

Calculate surface overflow rate, theoretical detention time, orifice velocities through the 8 ports at design flow, and plate settler loading rate. Estimate baffling factor from EPA's table (0.7 for perforated inlet, 0.3 for blocked). Compute Idelchik headloss for the perforated wall. This establishes baseline expectations and catches gross errors before any CFD runs.

### V1.0 — 3D RANS screening model (1–2 weeks)

The recommended first model. Steady-state, single-phase, k-ω SST turbulence. 8 resolved orifices for the open wall; solid wall for blocked. Anisotropic porous zone for plate settlers. Virtual tracer test for RTD. Outputs: velocity contours, RTD curves, baffling factor, Morrill Index, dead zone fraction, velocity CV at settler entrance. This model answers the screening question with high confidence.

### V2.0 — Detailed 3D model for retrofit design (2–4 weeks, after field data)

Individual perforations resolved parametrically. Multiple open-area ratios (5–15%), hole sizes (2–6 inches), and distribution patterns tested. Calibrated against tracer test and headloss measurements. Lagrangian particle tracking with representative floc size classes (≥5 classes, apparent density ~1020–1070 kg/m³). This model answers "what perforation pattern should we build?"

### V3.0 — High-fidelity validated model (4–8 weeks, regulatory-grade)

Full multiphase (Euler-Lagrange) with two-way coupling. Coupled flocculation-settling if floc breakup is a concern. Transient simulation for density current analysis (seasonal temperature effects). LES turbulence for the transition zone if jet mixing optimization is needed. This level is justified only for capital projects **>$2M** or regulatory compliance demonstrations.

---

## Data collection priorities

**Priority 1 — Water level differential across the wall.** Install staff gauges or pressure transducers upstream and downstream. Accuracy needed: ±0.01 ft (differential head may be only 0.05–0.5 ft for open perforations). Measure at multiple flow rates. **Cost: minimal. Value: very high.** This is the single most important boundary condition for model calibration.

**Priority 2 — Tracer test.** Sodium fluoride is the standard tracer for potable water (NSF/ANSI 60 approved). Pulse injection at the 8 inlet orifices. Monitor at the launder effluent and at least one mid-basin point. Sample every 1–2 minutes initially, extending to 5-minute intervals after the peak. Continue for ≥3× theoretical detention time. Follow the Teefy (1996) AWWA Research Foundation protocol. If possible, test both configurations (open vs. blocked). This provides the definitive RTD validation dataset.

**Priority 3 — Flow split between parallel basins.** Verify existing flow meters and measure simultaneous flow to each basin at constant total plant flow. Maldistribution between basins directly affects individual basin loading and model boundary conditions.

**Priority 4 — Velocity observations.** Acoustic Doppler Velocimeter (ADV) point measurements at 9–12 locations: downstream of inlet orifices, between wall and settlers, in the launder approach zone. Each measurement should be ≥60 seconds for stable time-averaged statistics. This directly validates the CFD velocity field.

**Priority 5 — Visual inspection of backer boards.** After 10 years, assess condition: are there gaps, missing boards, warping, or deterioration? This determines whether the "solid wall" model assumption is correct or whether leakage paths exist.

**Not needed for screening:** Temperature profiles (needed only if density current effects are suspected), floc size measurements (needed only for particle tracking models), and turbidity profiles (useful for performance correlation but not model validation at this stage).

---

## Decision triggers

**Trigger 1 — Move from screening to design model:** The screening model shows the open wall configuration improves the baffling factor by **≥0.1** (e.g., from 0.4 to 0.5+) or reduces dead zone fraction by **≥10 percentage points**, AND the utility is willing to fund a retrofit.

**Trigger 2 — Upgrade from 2D to 3D:** If a 2D vertical slice is attempted first and it cannot capture the lateral flow distribution from 8 orifices (expected, given the 5.5:1 width-to-depth ratio). This is likely an immediate trigger—the recommendation is to start with 3D.

**Trigger 3 — Move from single-phase to particle tracking:** The question shifts from "which configuration has better hydraulics?" to "will the retrofit meet specific turbidity targets?" This requires field-measured floc properties as input.

**Trigger 4 — Model reliability flags:** CFD-predicted headloss differs from measured by >30%. RTD prediction error exceeds 25% on t₁₀. Predicted flow patterns contradict field observations (e.g., model shows uniform flow, but turbidity profiles show strong lateral variation). Strong sensitivity to uncertain parameters (>30% change in key metrics when varying turbulence model or boundary conditions).

**Trigger 5 — Regulatory or capital threshold:** Capital expenditure >$500K generally warrants validated 3D CFD. Projects >$2M warrant full validation with field data and particle tracking.

---

## Recommended modeling inputs

### First-pass screening model checklist

- [ ] Basin geometry from record drawings (floc basin, sed basin, wall location, launder positions)
- [ ] 8 orifice locations, sizes, and elevations from record drawings
- [ ] Plate settler geometry: angle, spacing, length, extent within basin
- [ ] Design flow rate (~40 MGD per basin, or current operational range)
- [ ] Water temperature (for viscosity; use seasonal average or worst-case)
- [ ] Launder weir lengths and positions
- [ ] Backer board extent (full coverage vs. partial? top gap? bottom gap?)
- [ ] Porous zone coefficients for plate settlers: D₁ = 12/w², D₂ = 1000 × D₁, porosity = w/(w+t)
- [ ] Turbulence model: k-ω SST recommended
- [ ] Virtual tracer: pulse injection at inlet, monitor at outlet for ≥3× theoretical detention time

### Later detailed design model checklist (additions to above)

- [ ] Tracer test RTD data for calibration/validation
- [ ] Headloss measurement across the wall (both configurations if possible)
- [ ] Velocity measurements at 9–12 points (ADV)
- [ ] Flow split data between parallel basins
- [ ] Backer board condition assessment (leakage paths)
- [ ] For particle tracking: floc size distribution, apparent density, settling velocity
- [ ] Parametric perforation patterns to test: open area ratios 5–15%, hole diameters 2–6 inches, grid vs. staggered
- [ ] Target port velocity: 0.5–1.0 ft/s (prevent floc breakup while maintaining distribution)
- [ ] Idelchik loss coefficients for candidate perforation patterns

---

## Source notes

**Idelchik, I.E. — Handbook of Hydraulic Resistance (4th ed., 2008).** The gold-standard reference for headloss through perforated plates. Chapter 8 provides loss coefficients as a function of open-area ratio, Reynolds number, and edge geometry. Essential for calculating porous-jump parameters and validating orifice pressure drops. Every CFD model of a perforated wall should start here.

**Kawamura, S. — Integrated Design and Operation of Water Treatment Facilities (2nd ed., 2000).** The single most practical design reference for perforated inlet walls and plate settlers in drinking water treatment. Provides specific hole sizes (3–6 inches), velocities (0.15–0.5 ft/s), and open-area ratios (3–6% for sedimentation inlet walls). Based on ~50 years of design experience at Montgomery Watson.

**Crittenden et al. — MWH's Water Treatment: Principles and Design (3rd ed., 2012).** The most comprehensive water treatment textbook. Chapter on sedimentation covers Hazen theory, perforated inlet baffle design, plate settler theory (derived from Yao, 1970), RTD analysis, and Morrill Index. Primary academic reference for all topics in this memo.

**Kizilaslan, Demirel, and Aral (2020) — "A Perforated Baffle Design to Improve Mixing in Contact Tanks," Water, 12(4), 1022.** The strongest published study on perforated baffle optimization using CFD. Tested solidity ratios 65–90% (open area 10–35%) using LES in OpenFOAM with hole-scale resolution. Found hydraulic efficiency improved from "average" to "superior" baffling (36% improvement in baffling factor) with optimized perforations. Directly applicable to this project's wall design question.

**Malavasi et al. (2012) — "On the pressure losses through perforated plates," Flow Measurement and Instrumentation.** Definitive experimental study showing that the number of holes materially affects pressure drop at constant open-area ratio, especially for plates with **fewer than ~15 holes**. This is the key evidence supporting resolved-orifice modeling for the 8-port wall.

**Teixeira and Siqueira (2008) — "Performance Assessment of Hydraulic Efficiency Indexes," J. Environ. Eng., 134(10), 851–859.** Seminal paper evaluating 14 hydraulic efficiency indices for water treatment basins. Recommended t₁₀ as the best short-circuiting indicator and the Morrill Dispersion Index as the best mixing indicator. Essential reference for selecting RTD-derived metrics.

**US EPA (2020) — Disinfection Profiling and Benchmarking Technical Guidance Manual, EPA 815-R-20-003.** The definitive source for baffling factor classifications (Unbaffled: 0.1, Poor: 0.3, Average: 0.5, Superior: 0.7, Perfect: 1.0), tracer study methodology (Appendix E), and t₁₀ determination from tracer data. While written for disinfection CT compliance, the hydraulic methodology is directly applicable to sedimentation basins.

**GLUMRB (2022) — Recommended Standards for Water Works (Ten States Standards).** The de facto regulatory design standard for drinking water treatment across most US states. Section 4.2.5 covers rectangular sedimentation basin criteria; Section 4.2.7 covers modular plate/tube settling units including loading rates and inlet distribution requirements.

**Stamou, Adams, and Rodi (1989) — "Numerical Modeling of Flow and Settling in Primary Rectangular Clarifiers," J. Hydraulic Research, 27(5), 665–682.** The foundational paper for CFD modeling of rectangular settling tanks. Established the 2D approach with coupled momentum and solid concentration equations that most subsequent basin CFD work builds upon.

**Teefy, S. (1996) — Tracer Studies in Water Treatment Facilities: A Protocol and Case Studies, AWWA Research Foundation.** The definitive protocol for conducting tracer tests in water treatment facilities. Covers tracer selection, dosing, sampling frequency, data analysis, and case studies. Essential reference when the project reaches the field validation stage.

**Yao, K.M. (1970) — "Theoretical Study of High Rate Sedimentation," J. Water Pollution Control Federation, 42(2), 218–228.** Foundational theory for inclined plate and tube settlers. Derived the critical settling velocity equation: V_c = S·v₀ / [sin θ + (L·cos θ)/w], where S=1 for parallel plates. All plate settler design and the porous zone modeling approach trace back to this theory.

---

## Source list

- Abeyratne, W.M.L.K. et al. (2023). "Suspended solid removal efficiency of plate settlers and tube settlers analysed by CFD modelling." *Water Science & Technology*, 87(9), 2116–2127. https://iwaponline.com/wst/article/87/9/2116/94559
- Alrawashdeh, H. et al. (2020). "Numerical and experimental investigation of utilizing the porous media model for windbreaks CFD simulation." *Sustainable Cities and Society*. https://www.sciencedirect.com/science/article/pii/S2210670720308647
- ANSYS FLUENT 12.0 User's Guide, Section 7.3.20 — Porous Jump Boundary Condition. https://www.afs.enea.it/project/neptunius/docs/fluent/html/ug/node256.htm
- Audenaert, W.T.M. et al. (2020). "Practical validation of computational fluid dynamics for water and wastewater treatment." *Water Science and Technology*, 81(8), 1636. https://iwaponline.com/wst/article/81/8/1636/73682/
- Brown, L. and Jacobsen, F. (2009). "Evaluating and Optimising the Performance of Chlorine Contact Tanks Using CFD." Water New Zealand. https://www.waternz.org.nz/Attachment?Action=Download&Attachment_id=891
- Cho, Y. et al. (2010). "Evaluation of the effect of baffle shape in flocculation basin on hydrodynamic behavior using CFD." *Korean J. Chem. Eng.*, 27, 874–880. https://link.springer.com/article/10.1007/s11814-010-0144-4
- Crittenden, J.C. et al. (2012). *MWH's Water Treatment: Principles and Design*, 3rd ed. John Wiley & Sons.
- Demirel, E. and Aral, M.M. (2020). "Perforated Baffles for the Optimization of Disinfection Treatment." *Water*, 12(12), 3462. https://www.mdpi.com/2073-4441/12/12/3462
- GLUMRB (2022). *Recommended Standards for Water Works*. Great Lakes–Upper Mississippi River Board. https://files.dep.state.pa.us/Water/BSDW/Public_Water_Supply_Permits/2022_Recommended_Standards_for_Water_Works.pdf
- Goula, A.M. et al. (2008). "A CFD methodology for the design of sedimentation tanks in potable water treatment." *Chemical Engineering Journal*, 140, 110–121.
- Hirom, K. et al. (2024). "Examining the Effects of Longitudinal Inclined Plates and Perforated Inlet Baffle on the Settling Efficiency of a Rectangular Sedimentation Tank." *Water, Air, & Soil Pollution*. https://link.springer.com/article/10.1007/s11270-024-06891-2
- Idelchik, I.E. (2008). *Handbook of Hydraulic Resistance*, 4th Revised and Augmented Edition. Begell House.
- Kawamura, S. (2000). *Integrated Design and Operation of Water Treatment Facilities*, 2nd ed. John Wiley & Sons.
- Kizilaslan, M.A., Demirel, E., and Aral, M.M. (2020). "A Perforated Baffle Design to Improve Mixing in Contact Tanks." *Water*, 12(4), 1022. https://www.mdpi.com/2073-4441/12/4/1022
- Li, Y., Davidson, J.H., and Peng, F. (2023). "A fluid flow model for the pressure loss through perforated plates." arXiv:2304.11730. https://arxiv.org/pdf/2304.11730
- Malavasi, S. et al. (2012). "On the pressure losses through perforated plates." *Flow Measurement and Instrumentation*. https://www.sciencedirect.com/science/article/abs/pii/S0955598612000787
- Stamou, A.I., Adams, E.W., and Rodi, W. (1989). "Numerical Modeling of Flow and Settling in Primary Rectangular Clarifiers." *J. Hydraulic Research*, 27(5), 665–682.
- Stamou, A.I. and Gkesouli, A. (2015). "Modeling settling tanks for water treatment using computational fluid dynamics." *J. Hydroinformatics*, 17(5), 745–762. https://iwaponline.com/jh/article/17/5/745/3505
- Takata, K. and Kurose, R. (2017). "Influence of density flow on treated water turbidity in a sedimentation basin with inclined plate settler." *Water Supply*, 17(4), 1140–1148. https://iwaponline.com/ws/article/17/4/1140/15037
- Tarpagkou, R. and Pantokratoras, A. (2014). "The influence of lamellar settler in sedimentation tanks for potable water treatment — A computational fluid dynamic study." *Powder Technology*, 268, 139–149. https://www.sciencedirect.com/science/article/abs/pii/S003259101400730X
- TCEQ (2019). RG-559: Baffling Factors and T10 Calculations. https://www.tceq.texas.gov/downloads/drinking-water/plan-technical-review/guidance/rg-559.pdf
- Teefy, S. (1996). *Tracer Studies in Water Treatment Facilities: A Protocol and Case Studies*. AWWA Research Foundation.
- Teixeira, E.C. and Siqueira, R.N. (2008). "Performance Assessment of Hydraulic Efficiency Indexes." *J. Environ. Eng.*, 134(10), 851–859. https://ascelibrary.org/doi/10.1061/(ASCE)0733-9372(2008)134:10(851)
- USEPA (2020). *Disinfection Profiling and Benchmarking Technical Guidance Manual*, EPA 815-R-20-003. https://www.epa.gov/system/files/documents/2022-02/disprof_bench_3rules_final_508.pdf
- Walkerton Clean Water Centre (2015). Fact Sheet: Baffling Factor Selection for CT Calculations. https://wcwc.ca/wp-content/uploads/2020/06/WCWC-Fact-Sheet_Vol-1_Issue-5_Baffling-Factor-Selection-for-CT-Calcs.pdf
- Yao, K.M. (1970). "Theoretical Study of High Rate Sedimentation." *J. Water Pollution Control Federation*, 42(2), 218–228.