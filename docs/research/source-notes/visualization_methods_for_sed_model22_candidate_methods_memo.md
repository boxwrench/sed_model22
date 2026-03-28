# Visualization methods for sed_model22: a decision memo

**Particle advection with fading trails should be built first.** It is the single method that best balances flow communication, technical honesty, low-resolution readability, and Python/CPU buildability for a steady screening-grade baffled-basin model. Dye-pulse scalar advection should follow as v2, adding concentration-based insight that particles alone cannot show. LIC textures, voxel cutaways, and synchronized multi-section views should be reserved for later when the model's geometry and fidelity warrant them. This memo evaluates every candidate method against sed_model22's real constraints and ranks them by what can actually be built, rendered, trusted, and shipped now.

---

## 1. Recommendation

**Rank of candidates for sed_model22 right now:**

1. **Particle advection with fading trails** — build first. Deterministic RK4 integration through the steady velocity field, rendered as short comet-like segments with alpha-fading tails. Pre-compute pathlines once, animate as a sliding window over stored trajectories. Shows main flow path, recirculation, dead zones, short-circuiting, and acceleration through constrictions — all visible without annotation. Works at 854×480 on CPU. Zero dependencies beyond numpy, scipy, matplotlib, and ffmpeg.

2. **Dye-pulse scalar advection** — build second. Semi-Lagrangian backward advection of a concentration band injected at the inlet, rendered frame-by-frame via `imshow`. Communicates mixing, dispersion, dead zones (dye never reaches them), and short-circuiting (dye arrives early at outlet) in a way particles cannot. Also lightweight, deterministic, and CPU-friendly.

3. **Static streamlines with speed coloring** — build alongside v1 for report stills. `matplotlib.streamplot()` with `color=speed`, `linewidth=speed`, and masked arrays for baffles. One-liner generation, no animation needed, ideal for plan-view report figures.

**Reserved for future complex output:** Synchronized multi-section views (plan + longitudinal + transverse) via matplotlib subplots for quasi-3D geometry. Voxel geometry rendering via PyVista for 3D spatial comprehension. Stream tubes via PyVista for 3D serpentine flow paths. Topology/network diagrams via NetworkX for active-path logic.

---

## 2. Best-fit analysis

The recommended methods survive every constraint that matters for this repo:

**Steady screening model.** In a steady field, pathlines and streamlines coincide — particle positions are fully determined by seed location and integration time. No stochastic forcing is needed or appropriate. This eliminates the most dangerous honesty risk (false turbulence impression). Dye advection through a steady field is physically meaningful: it shows how a pulse disperses along the real flow topology without implying transient flow dynamics.

**Baffled basin geometry.** Particles naturally accumulate in recirculation zones, stall in dead zones, and accelerate through constrictions between baffles. The viewer sees these behaviors emerge from the animation without needing domain expertise. Fading trails make recirculation loops visible as tight spirals or persistent clusters. Dye visualization makes dead zones visible as regions the dye never reaches, and short-circuiting visible as early dye arrival at the outlet.

**Low-resolution silent preview video.** At **854×480**, individual data points are hard to read, but moving particles with trails remain legible because the eye tracks motion, not static detail. A dark background with light-colored trails (the "wind map" aesthetic pioneered by Fernanda Viégas and Martin Wattenberg) maximizes contrast and motion readability. Scalar dye fields rendered with `imshow` are inherently resolution-matched to the underlying grid — no wasted pixels.

**Python/CPU-first implementation.** Particle advection with vectorized RK4 costs **<1 ms per step for 1,000 particles** on a single CPU core. Pre-computing all pathlines for a 10-second video takes seconds. Rendering via matplotlib's `LineCollection` with per-segment RGBA alpha and piping to ffmpeg via `FFMpegWriter` completes a full 854×480 video in **1–5 minutes** with no GPU. Semi-Lagrangian dye advection with `scipy.ndimage.map_coordinates` costs **<10 ms per frame** on a 200×100 grid.

**Report-facing communication.** Static streamlines colored by speed are the single most common visualization in the water treatment CFD literature — appearing in virtually every published paper on baffled sedimentation tanks, chlorine contact tanks, and flocculation basins. Reviewers and engineers recognize this format instantly. Particle animations add a dynamic layer that communicates flow behavior to non-specialists more intuitively than any static image.

**Technical honesty.** Particles following deterministic pathlines through a steady field are mathematically exact representations of what the model predicts — they do not add information the model does not contain. The key honesty risks (smooth interpolation hiding grid coarseness, dense textures implying high-fidelity CFD, stochastic jitter implying turbulence) are all avoided by the recommended styling: modest particle count, visible discrete behavior, muted color palette, and explicit labeling.

---

## 3. Comparison table

| Method | Best for | Fails at | Current 2D | Future 3D | Required inputs | Generation complexity | Render cost (854×480) | Preview video suitability | Honesty risk | sed_model22 timing |
|---|---|---|---|---|---|---|---|---|---|---|
| **Particle trails** | Main path, recirculation, acceleration, short-circuiting | Scalar quantities, concentration, precise dead-zone boundaries | ✅ Excellent | ⚠️ Needs PyVista for 3D | Steady velocity field + geometry mask | Low: RK4 + interpolation | ~2 min/10 s video | ★★★★★ | Low if no jitter added | **Build now** |
| **Dye-pulse advection** | Dead zones, dispersion, mixing, short-circuiting timing | Individual flow paths, velocity magnitude | ✅ Excellent | ✅ Extends to 3D scalar | Steady velocity field + geometry mask | Low: semi-Lagrangian + imshow | ~1 min/10 s video | ★★★★☆ | Moderate: implies transient accuracy | **Build next** |
| **Static streamlines** | Flow topology, report stills, engineering convention | Animation, temporal behavior, concentration | ✅ Excellent | ⚠️ 2D only via matplotlib | Steady velocity field + mask | Trivial: one `streamplot()` call | <1 s per image | ★★☆☆☆ (static) | Low–moderate | **Build now** (stills) |
| **Arrow/quiver field** | Raw data display, resolution honesty | Flow topology, recirculation readability, low-res video | ✅ Works | ⚠️ Cluttered in 3D | Steady velocity field | Trivial: one `quiver()` call | <1 s per image | ★☆☆☆☆ | Very low | Build now (debug overlay) |
| **Animated scalar bands** | Speed variation, constriction highlighting | Flow direction, topology | ✅ Works | ✅ Extends to 3D | Steady velocity magnitude | Low: imshow animation | ~30 s/10 s video | ★★★☆☆ | Low | Build next |
| **LIC texture** | Dense field direction, publication aesthetics | Magnitude, animation (expensive), screening honesty | ✅ Works | ⚠️ 2D only practical | Steady velocity field + noise texture | Medium: needs `lic` package | ~5–15 min/animated video | ★★★☆☆ | **High**: looks like high-fidelity CFD | Later |
| **Animated LIC (UFLIC)** | Full-field flow animation, visual richness | Honesty, CPU cost, implementation complexity | ⚠️ No Python package | ❌ | Steady velocity field + phase-shifting noise | High: no ready implementation | ~10–30 min/10 s video | ★★★★☆ | **Very high** | Not yet |
| **Stream ribbons/tubes** | 3D flow paths, vorticity, convergence | 2D output, low-res readability | ❌ Irrelevant for 2D | ✅ Excellent | 3D velocity field | Medium: PyVista/VTK | Moderate (needs OpenGL) | ★★★☆☆ | Moderate | Later (3D) |
| **Voxel cutaways** | 3D geometry comprehension, occupancy | Flow direction, smooth flow, low resolution | ❌ Irrelevant for 2D | ✅ Good for geometry | 3D occupancy grid | Medium: PyVista | Moderate–high | ★★☆☆☆ | Low | Later (3D geometry) |
| **Synchronized sections** | Multi-plane engineering detail, vertical redistribution | Single-glance overview, non-specialist audience | ⚠️ Limited value for 2D | ✅ Excellent | 3D field + plane definitions | Low: matplotlib subplots | Very low | ★★★☆☆ | Very low | Later (3D) |
| **Isosurfaces** | 3D tracer plume boundaries, threshold visualization | 2D output, velocity fields | ❌ Irrelevant for 2D | ✅ Excellent | 3D scalar field | Low: PyVista `contour()` | Moderate | ★★★☆☆ | Moderate | Later (3D) |
| **Translucent solids** | Presentation-quality 3D with internal flow | Low-res readability, CPU rendering, depth sorting | ❌ Irrelevant for 2D | ⚠️ Rendering challenges | 3D geometry + flow field | High: transparency sorting | High (needs GPU or depth peeling) | ★☆☆☆☆ | Moderate | Not yet |
| **Topology/network diagrams** | Active vs blocked paths, flow splitting logic, compartmental models | Spatial detail, continuous field behavior | ⚠️ Overly abstract for current 2D | ✅ Excellent for serpentine path logic | Compartment definitions + flow rates | Low: NetworkX + matplotlib | Very low | ★★★☆☆ | Moderate: hides spatial detail | Later (serpentine) |
| **Occupancy/corridor views** | Preferential flow paths as volumes, dead-zone detection | Individual trajectory detail, velocity information | ✅ Works as 2D density map | ✅ Excellent for 3D | Velocity field → many streamlines → binned density | Medium: many streamlines + binning | Moderate | ★★★☆☆ | Low | Later |
| **Tracer plumes (3D)** | Concentration evolution in complex geometry | 2D output, velocity-only fields | ⚠️ Reduces to dye-pulse in 2D | ✅ Excellent | 3D transient scalar field | Medium–high: 3D advection solver | High | ★★★☆☆ | Moderate | Later (3D) |
| **Layered slices** | Depth scanning through 3D domain, bridging 2D and 3D | Single-view overview, non-specialist readability | ❌ Irrelevant for 2D | ✅ Good transitional method | 3D scalar field | Very low | Very low | ★★★☆☆ | Very low | Later (3D) |

---

## 4. Visual readability: what the viewer actually sees

### Particle trails at 854×480

The viewer sees **200–500 small bright dots moving through a dark basin layout**, each trailing a short fading tail of 15–20 frames. Baffles appear as dark solid rectangles. The motion is smooth, continuous, and entirely determined by the velocity field — no jitter, no randomness. At the inlet, particles appear at fixed intervals and spread across the entry width. Through constrictions between baffles, trails compress and lengthen (acceleration is visible as longer inter-frame spacing). In recirculation zones behind baffles, particles loop in tight spirals or cluster persistently — the eye immediately reads these as "trapped flow." Dead zones appear as areas with **no particles** or extremely slow-moving ones, visually black against the moving field. Short-circuiting is visible as particles that transit the entire basin much faster than others, reaching the outlet while most particles are still mid-basin.

**What reads clearly:** Main flow path (dominant particle stream), recirculation (spiral/cluster behavior), dead zones (empty regions), acceleration (trail stretching), short-circuiting (fast-transit particles). **What remains ambiguous:** Exact velocity magnitude (visible only as trail spacing, not precisely), concentration (particles don't show how much water goes where), and mixing intensity (diffusion is not represented by deterministic particles).

### Dye-pulse advection at 854×480

The viewer sees a **colored band** (blue or warm-toned against a dark background) injected at the inlet, then stretching and deforming as it advects through the basin. The band elongates through constrictions, wraps around baffles, and disperses. Regions the dye never reaches appear permanently dark — these are dead zones. Early arrival of color at the outlet indicates short-circuiting. The dye's shape after several transit times reveals the effective mixing pattern.

**What reads clearly:** Dead zones (no dye), short-circuiting (early outlet arrival), dispersion (band spreading), flow splitting (band bifurcation at baffles). **What remains ambiguous:** Velocity direction (color shows concentration, not flow direction), recirculation details (dye accumulates but doesn't show loop structure), individual pathlines.

### Static streamlines for report figures

The viewer sees **smooth colored curves** tangent to the velocity field, with color mapping to speed (cool blues for slow, warm reds for fast). Baffles are masked regions where no streamlines penetrate. Recirculation zones appear as closed loops. Dead zones appear as regions with sparse or absent streamlines. This is the format water treatment engineers and regulators already expect from CFD presentations.

**What reads clearly:** Flow topology, recirculation loops, main flow path, speed distribution. **What remains ambiguous:** Temporal behavior, mixing, concentration — but these are not the purpose of a plan-view still.

---

## 5. Honesty and misinterpretation risk

### Particle trails

**How it could mislead:** If particles are given stochastic perturbation or "diffusion noise" to look more natural, viewers will interpret this as modeled turbulence. If particle count is too high (>1,000), the dense swarm can resemble experimental PIV or LES output. If the animation runs at high frame rate with very smooth motion, it can create an impression of temporal resolution the steady-state model does not have.

**Mitigation rules:**
- **Never add random jitter or diffusion noise** to particle positions. Every particle must follow a deterministic pathline through the steady field.
- **Cap particle count at 200–500** for preview video. This is enough to show flow structure without creating a dense "experimental" appearance.
- **Use a moderate frame rate** of 24 fps rather than 60 fps — the animation should feel deliberate, not hyperreal.
- **Label the video** with a persistent text overlay: "Steady-state screening model — directional flow pattern" or similar.
- **Use a muted, single-hue color palette** (white or light blue on dark background) rather than vivid rainbow particle coloring.
- In report context, caption should state: "Particle trajectories computed from steady-state velocity field. Screening-grade resolution; directional pattern is more defensible than literal velocity values."

### Dye-pulse advection

**How it could mislead:** Animated dye transport implies the model computed transient advection-diffusion with validated dispersion coefficients. Viewers may interpret the dye spread as a calibrated prediction of actual mixing behavior. If numerical diffusion is present (it always is in coarse-grid advection), the apparent dispersion is an artifact of the numerical scheme, not a modeled physical process.

**Mitigation rules:**
- **Label explicitly as synthetic tracer** — "Advected tracer pulse using steady velocity field. Dispersion is approximate."
- **Minimize numerical diffusion** by using higher-order interpolation (cubic) in the semi-Lagrangian step and keeping the CFL number reasonable.
- **Do not report quantitative dispersion metrics** (Morrill Index, etc.) from the dye animation unless the transport solver has been validated.
- **Use deliberately stylized coloring** (stepped color bands rather than smooth gradients) to signal that concentration values are approximate.

### Static streamlines

**How it could mislead:** Smooth streamlines through a coarse field use bilinear interpolation between grid points, creating trajectories that appear more precise than the underlying data. Very thin obstacles (<1 grid cell) may be "tunneled through" by the interpolation. Dense streamline fields look like publication-quality CFD.

**Mitigation rules:**
- **Use moderate density** (`density=1.5–2.0` in matplotlib, not 5+). Sparse streamlines signal "screening model."
- **Show the grid or cell boundaries** as a light overlay when presenting to technical audiences.
- **Color by speed using a sequential, single-hue palette** (e.g., `cmap='Blues'` or `cmap='viridis'`) — avoid rainbow/jet.

### LIC textures (reserved for later)

**Highest honesty risk of all methods.** LIC produces output that closely resembles experimental smoke-wire or oil-flow photography. Ansys documentation explicitly describes LIC as producing images "similar to a static picture of moving smoke or fluid injected into the fluid." For a screening-grade model, this visual similarity to experimental results or high-fidelity CFD is actively misleading. LIC also fills the entire domain with texture, creating an impression of everywhere-resolved detail that a coarse model cannot support. **LIC should not be used for sed_model22 until the model's resolution and validation level justify the visual fidelity it implies.**

---

## 6. Production practicality

### Particle advection with fading trails

**Data requirements:** 2D steady velocity field as two numpy arrays (U, V) on a regular grid, plus a boolean mask array for baffles/walls. These exist in sed_model22 v0.1 output.

**Generation steps:**
1. Build `scipy.interpolate.RegularGridInterpolator` objects for U and V components.
2. Define seed points along the inlet boundary (evenly spaced, deterministic).
3. Pre-compute all pathlines via vectorized RK4 with fixed timestep. For each seed point, integrate forward until the particle exits the domain or a maximum time is reached. Store positions as arrays.
4. For animation: define a sliding window of length ~20 positions per particle. At each frame, advance the window by one step. Build `LineCollection` segments with RGBA alpha gradient for fading tails.

**Render steps:**
1. Set up matplotlib figure at exact 854×480 pixels: `fig, ax = plt.subplots(figsize=(8.54, 4.80), dpi=100)`.
2. Draw static background: basin outline, baffles as filled rectangles, optional light-gray streamlines.
3. For each frame: update `LineCollection` segments, call `writer.grab_frame()`.
4. Encode via `FFMpegWriter(fps=24, codec='h264')` with `-pix_fmt yuv420p`.

**Dependency risk:** numpy, scipy, matplotlib, ffmpeg (system binary). All standard, all already in most Python scientific environments. No compiled extensions, no GPU, no special builds.

**Expected preview runtime:** Pre-computation of 500 pathlines on a 200×100 grid: **<5 seconds**. Rendering 300 frames at 854×480 via matplotlib + ffmpeg: **1–3 minutes**. Total: **under 5 minutes** per run on a modern laptop CPU.

**Deterministic automated output:** Fully deterministic with fixed random seed for particle seeding (or, better, use deterministic evenly-spaced seeding that requires no random seed at all). Same input velocity field → same video, bit-for-bit.

### Dye-pulse scalar advection

**Data requirements:** Same 2D steady velocity field and mask. Additionally requires choosing a diffusion coefficient (or setting it to zero for pure advection).

**Generation steps:**
1. Initialize a concentration array `C[ny, nx]` with a band of dye at the inlet.
2. Per timestep: backward-trace departure points using the steady velocity field, interpolate C at departure points using `scipy.ndimage.map_coordinates(order=3)`.
3. Apply mask: set `C[mask] = 0`.
4. Store frames as a 3D array `C[nt, ny, nx]` or render on-the-fly.

**Render steps:**
1. Use `ax.imshow(C, cmap='Blues', vmin=0, vmax=1)` with `set_data()` updates and `blit=True`.
2. Encode identically to particle approach.

**Expected preview runtime:** Advection step: **~5 ms per frame** on 200×100 grid. 300 frames of advection: **~1.5 seconds**. Rendering: **~1 minute**. Total: **under 2 minutes**.

**Dependency risk:** Same as particles. `scipy.ndimage.map_coordinates` is the only additional function, already in scipy.

### Static streamlines

**Data requirements:** Same velocity field and mask.

**Generation steps:** One call to `ax.streamplot(X, Y, U_masked, V_masked, density=2, color=speed, cmap='viridis', linewidth=lw)`.

**Render steps:** `fig.savefig('streamlines.png', dpi=150)` for report-quality output at ~1280×720.

**Expected runtime:** **<2 seconds** including figure setup, streamplot computation, and file save.

---

## 7. Buildability buckets

### Build Now

- **Particle advection with fading trails** — Primary animated visualization for preview video. ~200–300 lines of Python. Core algorithm: vectorized RK4 + RegularGridInterpolator + LineCollection + FFMpegWriter.
- **Static streamlines (speed-colored)** — Report stills. ~20 lines of Python. One `streamplot()` call with masked arrays and speed coloring.
- **Arrow/quiver overlay** — Debug and validation tool. ~10 lines. Useful for verifying the velocity field is correct before building animations.
- **Basin geometry renderer** — Shared utility for all methods. Draws baffles, walls, inlet/outlet as matplotlib patches.

### Build Next

- **Dye-pulse scalar advection** — Second animation type. ~150 lines. Semi-Lagrangian advection + imshow animation. Adds concentration-based insight that particles cannot provide.
- **Animated scalar bands (speed magnitude)** — Pulsing color field showing where flow is fast vs slow. ~50 lines on top of existing rendering infrastructure.
- **Occupancy density map** — Seed many streamlines, bin into 2D density grid, render as heatmap. Shows "where the water wants to go" as an aggregate view. ~80 lines.
- **Composite report figure** — Multi-panel matplotlib figure combining streamlines, speed contour, and geometry in a single publication-ready output.

### Later / Not Yet

- **LIC texture** — Requires `lic` or `licpy` package. Visually excellent but carries high honesty risk for a screening model. Build only when model fidelity rises enough to justify the visual density. Animated LIC (UFLIC) has no ready Python implementation and should not be attempted.
- **Synchronized multi-section views** — Valuable when geometry becomes quasi-3D or 3D. Multiple matplotlib subplots showing plan, longitudinal, and transverse sections with shared colorbars. Moderate implementation effort (~300 lines) but requires 3D data that doesn't exist yet.
- **Voxel geometry rendering** — Via PyVista `UniformGrid`. Useful for showing 3D occupancy and baffle layout in serpentine over-under paths. Introduces PyVista dependency (~200 MB). Defer until 3D geometry output exists.
- **Stream tubes** — Via PyVista `streamlines().tube()`. Excellent for 3D serpentine flow. Requires 3D velocity field and PyVista.
- **Isosurface tracer plumes** — Via PyVista `contour()`. Excellent for 3D tracer transport visualization. Requires 3D scalar field.
- **Topology/network path diagrams** — Via NetworkX. Useful for explaining active vs blocked paths in serpentine over-under configurations. Low implementation cost but requires compartmental model abstraction that doesn't exist yet.
- **Translucent geometry with embedded flow** — The most visually attractive 3D option but also the hardest to render correctly (depth-sorting artifacts, GPU dependency, poor low-resolution readability). Not practical until the repo has a robust 3D rendering pipeline.

---

## 8. Concrete build suggestion

### v1: particle advection preview video (build now)

Create a module `viz_particles.py` that:
1. Accepts the v0.1 steady 2D velocity field (U, V arrays) and geometry mask as input.
2. Seeds 300–500 particles at the inlet boundary using deterministic, evenly-spaced positions, injected in staggered waves to fill the basin over time.
3. Pre-computes all pathlines via vectorized RK4 with `RegularGridInterpolator` for field sampling.
4. Renders a 10–15 second 854×480 MP4 at 24 fps using dark background, white or light-blue fading trails (LineCollection with per-segment RGBA alpha), and solid dark-gray baffle geometry.
5. Adds a persistent text label: "Steady screening model — directional flow pattern."
6. Outputs deterministically: same input → same video.

Also create `viz_streamlines.py` that generates a single-call static streamline figure colored by speed, suitable for inclusion in reports. This is a ~20-line utility function.

### v2: dye-pulse and composite output (build next)

Add `viz_dye.py` that:
1. Accepts the same velocity field and injects a dye pulse at the inlet.
2. Advects via semi-Lagrangian method for ~2× the theoretical detention time.
3. Renders as an animated scalar field using `imshow` with stepped color bands (not smooth gradients) to maintain honesty about the approximate nature of the transport.
4. Produces an RTD-like curve of outlet concentration vs time as a companion plot.

Add `viz_composite.py` that assembles a multi-panel report figure: streamlines (top-left), speed contour (top-right), particle snapshot at representative time (bottom-left), dye state at representative time (bottom-right).

### Future: 3D serpentine visualization (later, when geometry warrants)

When sed_model22 extends to quasi-3D or 3D output with serpentine over-under paths:

1. **Geometry comprehension:** Introduce PyVista dependency. Render 3D basin geometry as a voxel occupancy view with cutaway capability — this is where voxel views earn their place. Use isometric projection with baffle walls as semi-transparent surfaces and flow channels as void space. This answers "what does the geometry look like?" before showing any flow data.

2. **Flow path explanation:** Use PyVista stream tubes seeded at the inlet, colored by speed or residence time. Tubes through serpentine over-under paths show which routes the water takes, whether it goes over or under each baffle, and how flow distributes among alternative paths.

3. **Synchronized sections:** For engineering-detail report output, generate a 3-panel matplotlib figure showing plan view (XY), longitudinal section (XZ along flow path), and transverse section (YZ at a key baffle) with shared colorbars. This is the format water treatment engineers expect and trust.

4. **Topology/path diagram:** For explaining active vs blocked paths in serpentine configurations, generate a NetworkX-based graph showing compartments as nodes (sized by volume), connections as edges (thickness proportional to flow rate), and active paths highlighted in color. This is the clearest way to communicate "the model says water prefers path A over path B" without any field-visualization ambiguity.

---

## 9. How voxel views fit the roadmap

Voxel views have a specific and limited role. They are **excellent for geometry comprehension** — showing the 3D shape of a baffled basin with over-under paths as a clear solid/void map. They are **poor for flow visualization** — blocky rendering cannot communicate smooth velocity fields, and at low resolution the blockiness dominates. The right role for voxels in sed_model22's future is as the **geometry context layer** underneath flow-oriented overlays (stream tubes, tracer isosurfaces, or particle paths).

Concretely, a voxel cutaway animation that peels away the basin wall to reveal internal baffle structure is an effective 5-second introduction to a complex geometry before transitioning to flow visualization. Voxel views should not be used to show velocity, concentration, or any continuous scalar — smoother methods (isosurfaces, stream tubes, colored sections) do this better. For static report stills, an isometric voxel cutaway with annotations labeling each compartment and flow path would be effective. For animated flow, voxels should serve only as the background geometry that contextualizes particle or tracer motion.

**Voxel views should not be built until sed_model22 produces 3D geometry output.** When that happens, PyVista's `UniformGrid` with clip/threshold filters is the implementation path — straightforward, well-documented, and compatible with the existing matplotlib-based pipeline for compositing.

---

## 10. Detailed answers to the serpentine over-under questions

For serpentine over-under paths specifically, the visualization challenge is explaining geometry that cannot be seen from any single 2D view. The methods that work best are:

**Available geometry:** Voxel cutaway (isometric view with one wall removed) + annotated synchronized sections (plan + longitudinal showing the over-under pattern). The cutaway shows spatial relationships; the sections show exact dimensions and clearances.

**Active bypass path:** Stream tubes colored by flow rate through the 3D domain. Tubes that carry high flow are thick and brightly colored; underutilized paths have thin, muted tubes. This directly answers "where does the water go?"

**Blocked vs open path logic:** Topology/network diagram with nodes for each compartment and edges for each connection. Blocked paths shown as dashed gray lines; open paths as solid colored lines with thickness proportional to flow. This is the most unambiguous representation for non-specialists.

**Vertical movement:** Longitudinal section (XZ plane along the flow path centerline) with velocity vectors or streamlines. This is the only 2D view that directly shows upward and downward flow components. Combined with a plan view showing horizontal distribution, the pair communicates the full 3D behavior without 3D rendering.

**Flow preference through alternative routes:** Occupancy density map — seed thousands of pathlines, bin into a 3D grid, render as a volume with opacity proportional to occupancy. High-occupancy corridors show preferred routes; zero-occupancy regions show dead zones and bypassed paths. Alternatively, a Sankey diagram showing flow splitting ratios at each junction point.

---

## 11. Comparison table: methods for questions 2a–2f

| Hydraulic behavior | Particle trails | Dye pulse | Streamlines | Arrows | LIC | Occupancy map |
|---|---|---|---|---|---|---|
| Main flow path | ★★★★★ (dominant particle stream) | ★★★★☆ (dye front) | ★★★★★ (central streamlines) | ★★★☆☆ (longest arrows) | ★★★★☆ (brightest texture band) | ★★★★★ (highest density) |
| Recirculation zones | ★★★★★ (spiraling trails) | ★★★☆☆ (dye accumulates but no loop structure) | ★★★★★ (closed loop streamlines) | ★★★☆☆ (reversing arrows) | ★★★★☆ (visible texture swirls) | ★★★★☆ (moderate density clusters) |
| Short-circuiting risk | ★★★★★ (fast-transit particles) | ★★★★★ (early outlet arrival) | ★★★☆☆ (shows path but not timing) | ★★☆☆☆ (static, no timing) | ★★☆☆☆ (no timing) | ★★★★☆ (high density on fast paths) |
| Dead / slow zones | ★★★★☆ (empty regions, slow particles) | ★★★★★ (dye never reaches them) | ★★★★☆ (sparse/absent streamlines) | ★★★★☆ (short/absent arrows) | ★★★☆☆ (undirected texture) | ★★★★★ (zero occupancy) |
| Flow splitting around baffles | ★★★★☆ (visible particle divergence) | ★★★☆☆ (dye front splits) | ★★★★★ (bifurcating streamlines) | ★★★★☆ (diverging arrows) | ★★★★☆ (texture splits) | ★★★★☆ (density distribution) |
| Acceleration through constrictions | ★★★★★ (trails elongate, spacing increases) | ★★★☆☆ (dye front stretches) | ★★★★☆ (streamlines compress) | ★★★★★ (arrows lengthen) | ★★★☆☆ (texture compresses) | ★★★☆☆ (density decreases where flow is fast) |

---

## 12. What works when the model is steady-state

In a steady field, pathlines, streamlines, and streaklines are all identical curves. This is a significant advantage: it means particle advection through a steady field produces **mathematically exact streamlines** without the ambiguity that afflicts transient flows. Every visualization method that relies on advection (particles, dye, LIC) is on solid ground when the field is steady — the visual output represents the actual predicted flow topology.

Methods that implicitly communicate temporal evolution (animated tracer plumes, streaklines that grow over time) carry a subtle dishonesty risk when applied to steady fields: the viewer sees change over time and may infer that the model computed temporal dynamics. Particle animation mitigates this naturally because the viewer understands they are watching a "virtual injection" into a fixed flow field. Dye advection carries higher risk because the evolving dye front looks like a transient simulation result.

The methods that work best for steady-state are those where the time axis in the animation represents **observation time of an ongoing process** (particles entering and traversing the basin continuously) rather than **evolution of the flow itself** (which isn't changing). This is why particle advection is the strongest candidate: it naturally represents "what happens to water as it enters and flows through the basin" without implying the flow pattern is changing.

---

## 13. How engineering tools typically depict baffled tank flow while acknowledging model limitations

The water treatment CFD literature follows a remarkably consistent visual convention. Published papers on baffled sedimentation tanks, chlorine contact tanks, and flocculation basins almost universally present results as:

1. **Velocity magnitude contour plots** on 2D plan-view or cross-sectional planes — the single most common visualization, appearing in nearly every paper.
2. **Streamline overlays** colored by speed — the standard topology visualization.
3. **RTD curves** (E(t) and F(t)) — the quantitative metric that regulators and designers actually use.
4. **Comparative panels** — side-by-side configurations (e.g., 2 baffles vs 4 baffles vs 6 baffles) sharing the same colorbar and scale.

These methods share a property: **they all show the field as-computed, without adding visual information the model did not generate.** The convention avoids animated particles, LIC textures, or photorealistic rendering. This is partly tradition but also partly honesty — the presentation format inherently communicates "this is a computational result on a grid" rather than "this is what the flow looks like in reality."

FLOW-3D HYDRO is the notable exception: it uses animated dye tracer visualization for marketing and demonstration purposes, explicitly coloring fluid by tracer percentage. But these animations are generated from transient solutions on fine grids, not screening models.

For sed_model22, the honest middle ground is: **use the engineering-convention static formats (streamlines, contours) for report figures, and use carefully styled particle animation for preview video that communicates flow structure without claiming CFD-level fidelity.**

---

## 14. Visual cues for readability at 854×480 in silent clips

At **854×480**, roughly standard-definition widescreen, fine text is illegible, thin lines may alias, and dense data fields collapse into noise. The methods that survive this resolution share common traits:

- **High contrast.** Dark background with bright foreground elements. The "wind map" aesthetic (dark navy or black background, white or bright-blue trails) maximizes readability.
- **Motion over detail.** The human visual system tracks moving objects at far lower resolution than it reads static text. Moving particles at 854×480 communicate flow direction effectively even when individual particle size is only 2–3 pixels.
- **Large-scale structure over fine gradients.** Broad dye fronts read clearly; subtle velocity gradient shading does not. Use stepped color bands (5–8 discrete levels) rather than smooth gradients for any scalar rendering.
- **Persistent geometry context.** Baffle outlines should be drawn with **2–3 pixel wide lines** in a contrasting color (white on dark, or dark on light) so the viewer always knows where walls are, even at low resolution.
- **Minimal text.** At 854×480, a single-line label in **18–24 pt font** is readable. Keep text to a model identifier and honesty label only.

Methods that fail at this resolution: dense arrow fields (individual arrows become unreadable below ~5 pixels), LIC textures (the fine texture detail is lost, leaving a blurry smear), and synchronized multi-section views (each panel gets only ~427×240 pixels, too small for useful detail).

---

## 15. Methods that show "where the water wants to go" vs "where particles happen to drift"

This distinction is the core communication challenge. The viewer should understand the **systematic flow preference** of the basin, not the trajectory of any individual particle. Three methods achieve this:

**Occupancy density maps** directly answer this question. Seed 5,000+ pathlines uniformly at the inlet, bin their positions into a 2D grid, and render the resulting density as a heatmap. High-density cells are where the flow consistently goes; zero-density cells are dead zones. This eliminates the "one unlucky particle" problem and shows aggregate behavior.

**Streamlines** show topology rather than individual trajectories. Because they are tangent to the velocity field everywhere simultaneously, they communicate the field's intent rather than one particle's history. A streamline plot says "the flow pattern is this shape" rather than "this particular water parcel went here."

**Dye-pulse front** shows the ensemble behavior of all the water entering at once. The leading edge of the dye front reveals the fastest path through the basin — the short-circuiting route. The lagging edges reveal the slowest paths. The final dye distribution reveals which regions participate in flow and which don't. This is the most natural representation of "where the water wants to go."

Particle trails fall between these extremes. With 200–500 particles, the viewer sees enough trajectories to infer the flow pattern, but each trail is still an individual path. The mitigation is to ensure particles are seeded uniformly and continuously so the collective behavior represents the field, not any single starting position.

---

## 16. Methods with highest risk of implying unmodeled physics

| Method | Risk level | What it falsely implies | Mitigation |
|---|---|---|---|
| Stochastic particle jitter | **Very high** | Turbulence is resolved | Never add noise; use deterministic RK4 |
| LIC texture | **High** | Dense field resolution everywhere; resembles experimental visualization | Defer to later; if used, desaturate and label heavily |
| Animated LIC (UFLIC) | **Very high** | Transient turbulent flow | Do not build for screening model |
| Smooth contour interpolation | **High** | High grid resolution | Use stepped/banded contours; show grid overlay |
| Dense particle swarms (>1,000) | **High** | PIV-like experimental data or DNS-resolution tracking | Cap at 200–500 particles |
| 3D perspective with lighting/shadows | **Moderate–high** | Volumetric CFD computation | Use flat 2D projections; save 3D for validated models |
| Rainbow/jet colormap | **Moderate** | Precise quantitative data | Use sequential single-hue palette (viridis, Blues) |
| High-framerate animation | **Moderate** | Fine temporal resolution | Use 24 fps, not 60 fps |

---

## 17. Report-support balance: clarity vs honesty vs simplicity

For report-facing output, the correct balance depends on the audience:

**For regulatory/permit review:** Maximum honesty. Use static streamlines + velocity contours in the standard engineering format. Include grid resolution statement, model type label, and baffling factor calculation. Avoid animation entirely — regulators work from printed or PDF figures.

**For design team/internal review:** Clarity first, with honesty labels. Animated particle video communicates flow behavior more effectively than any static figure. Include the honesty label and resolution statement, but prioritize communicating the hydraulic insight.

**For client/stakeholder presentation:** Visual clarity and engagement, with honest framing in the presenter's narration rather than embedded in the visual. Particle animation or dye-pulse video is appropriate. Avoid dense technical overlays.

In all cases, **computational simplicity is a feature, not a limitation.** A visualization that takes 2 minutes to generate from a run bundle can be regenerated whenever the model changes. A visualization that requires 30 minutes of manual ParaView manipulation becomes a bottleneck that discourages iteration.

---

## 18. References

Scientific flow visualization for baffled basins and water treatment hydraulics:
- Bruno et al. (2024), LES of baffled sedimentation tanks with streamlines and velocity contours: https://www.sciencedirect.com/science/article/pii/S0301479724035229
- Demirel et al. (2020), perforated baffle contact tank with 3D streamlines and RTD: https://www.mdpi.com/2073-4441/12/4/1022
- Goula et al. (2008), CFD sedimentation tank with DPM particle tracking: https://www.sciencedirect.com/science/article/abs/pii/S1385894707006250
- FLOW-3D HYDRO serpentine contact tank tracer visualization: https://www.flow3d.com/products/flow-3d-hydro/water-treatment/
- EPA Disinfection Profiling and Benchmarking (baffling factor tables): https://www.epa.gov/system/files/documents/2022-02/disprof_bench_3rules_final_508.pdf

Python visualization tools and implementation:
- matplotlib streamplot documentation: https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.streamplot.html
- Nicolas Rougier windmap (animated particle trails): https://github.com/rougier/windmap
- Tony S. Yu, animating particles in a flow: https://tonysyu.github.io/animating-particles-in-a-flow.html
- Jake VanderPlas matplotlib animation tutorial: https://jakevdp.github.io/blog/2012/08/18/matplotlib-animation-tutorial/
- `lic` package for Line Integral Convolution: https://lic.readthedocs.io/
- PyVista 3D scientific visualization: https://docs.pyvista.org/
- PyVista streamlines example: https://docs.pyvista.org/examples/01-filter/streamlines.html

Technical honesty and visualization ethics:
- Crameri et al. (2021), rainbow colormap distortion in hydrology: https://hess.copernicus.org/articles/25/4549/2021/hess-25-4549-2021.html
- Correll (2019), ethical dimensions of visualization research: https://dl.acm.org/doi/10.1145/3290605.3300418
- Wilke, Fundamentals of Data Visualization — uncertainty chapter: https://clauswilke.com/dataviz/visualizing-uncertainty.html
- Wood et al. (2012), sketchy rendering for information visualization: https://openaccess.city.ac.uk/1274/

3D and complex geometry visualization:
- ParaView CFD post-processing: https://www.paraview.org/Wiki/Computational_Fluid_Dynamics
- VTK stream tracer and tube filter: https://vtk.org/
- Priority Streamlines for occupancy-based flow corridor rendering (Schlemmer et al., EuroVis 2007)

---

## 19. Bottom line

**Build particle advection with fading trails first.** It is the only method that simultaneously communicates flow structure to non-specialists, stays honest about screening-grade fidelity, renders at 854×480 on CPU in minutes, requires no dependencies beyond numpy/scipy/matplotlib/ffmpeg, produces deterministic output suitable for run-bundle automation, and works directly from sed_model22's existing v0.1 steady velocity field output. Add static speed-colored streamlines alongside it for report stills — this takes 20 lines of code and matches the format water treatment engineers already expect.

**Do not build LIC, animated LIC, or dense particle swarms.** These methods carry unacceptable honesty risk for a screening model and add implementation complexity without proportional communication benefit. LIC in particular looks like high-fidelity CFD output and will mislead reviewers into overestimating model resolution.

**Dye-pulse advection should be v2.** It adds concentration-based insight that particles cannot provide (dead-zone identification, short-circuiting timing, dispersion behavior) and is nearly as simple to implement.

**Voxel views should enter the roadmap only when 3D geometry output exists**, and their role should be strictly geometry comprehension — showing the physical structure of over-under baffled paths as a cutaway occupancy view. Voxel views should never be used for flow or scalar field visualization, where smoother methods (stream tubes, isosurfaces, colored sections) are superior. When sed_model22 reaches 3D serpentine paths, the visualization stack should be: voxel cutaway for geometry context, stream tubes for flow paths, synchronized 2D sections for engineering detail, and topology diagrams for active-path logic — all built on PyVista, introduced as a single new dependency at that point.