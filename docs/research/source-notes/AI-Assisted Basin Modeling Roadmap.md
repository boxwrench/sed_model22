# **Computational and AI-Assisted Modeling Frameworks for Rectangular Sedimentation and Flocculation Basins: An Operational Decision-Support Roadmap**

The evolution of water and wastewater treatment processes has moved progressively from empirical design rules toward sophisticated numerical simulations capable of capturing the intricate fluid dynamics and chemical kinetics of unit operations. For the process practitioner, the challenge is no longer a lack of computational power, but rather the selection of a modeling fidelity that balances the rigor of physical laws with the agility required for real-time operational decision-making. Rectangular sedimentation and flocculation basins, while seemingly simple in geometry, are governed by complex interactions between inlet momentum, density-driven currents, and evolving particle characteristics. This report provides a comprehensive technical roadmap for implementing a hierarchy of models—from high-fidelity Computational Fluid Dynamics (CFD) to reduced-order and machine-learning surrogates—focused on identifying the minimum level of physics-based complexity necessary to produce reliable plant-level decisions.

## **The Paradigm of Minimum Modeling Complexity**

In the context of plant operations, the pursuit of maximum theoretical fidelity often encounters diminishing returns. While a scientist might require a model that resolves the Kolmogorov microscale to understand energy dissipation, an operator requires a model that accurately predicts effluent turbidity breakthrough under a 20% flow increase.1 The "minimum level of physics" is thus defined by the sensitivity of the model to actionable variables. If a 2D depth-averaged model can predict a sludge blanket rise with sufficient lead time to adjust a waste-activated sludge (WAS) pump, the added complexity of a 3D RANS simulation may be unnecessary for that specific decision.2

## **Scientific Accuracy vs. Operational Decision Confidence**

Scientific accuracy is rooted in the "why"—the fundamental regularities and first principles governing fluid motion and particle interaction.1 This requires capturing the full spectrum of turbulence, non-Newtonian sludge behavior, and multi-class population balances.3 Conversely, operational decision confidence is rooted in the "what"—the ability of a model to provide a reliable "fingerprint" of the system's state.5 An operator values a model that demonstrates robustness under noisy plant data and provides clear uncertainty bounds, even if it simplifies some of the vertical velocity gradients.1

| Modeling Metric | Requirements for Scientific Accuracy | Requirements for Operational Decision Confidence |
| :---- | :---- | :---- |
| **Physics Fidelity** | Resolves 3D turbulence, transient eddies, and multi-phase interactions.3 | Resolves global mass balance and primary flow paths (short-circuiting).2 |
| **Data Requirements** | High-resolution laboratory data for parameter estimation (e.g., fractal dimensions).3 | Online SCADA data (flow, turbidity, temperature, sludge depth).10 |
| **Validation Focus** | Agreement with local velocity/concentration profiles at specific points.12 | Agreement with effluent trends and hydraulic indices (![][image1], Morrill Index).14 |
| **Computational Lead Time** | Hours to days; typically used for offline design or forensic analysis.14 | Seconds to minutes; integrated into real-time dashboards or control loops.17 |
| **Uncertainty** | Focus on numerical error and convergence.16 | Focus on input data uncertainty and process variability.1 |

The implementation of a decision-support system must prioritize model transparency and interpretability to foster operator trust.5 A "black-box" model that predicts a failure without explaining the physical driver (e.g., a density current caused by a temperature shift) is less likely to be adopted than a "grey-box" model that correlates the failure to a specific hydraulic mechanism.20

## **Governing Processes Influencing Basin Performance**

The performance of rectangular basins is not merely a function of their theoretical hydraulic retention time (HRT). Instead, it is dictated by several competing physical processes that can significantly reduce effective settling volume.

## **Inlet Jet Momentum and Energy Dissipation**

The inflowing water at the head of a basin carries significant kinetic energy. If the inlet is poorly designed, this jet momentum persists deep into the basin, creating a high-velocity "core" that short-circuits directly to the outlet.12 This effect is particularly pronounced in basins without adequate baffling. Research indicates that the jet effect can lead to the resuspension of already settled particles near the inlet pipe.22 To mitigate this, practitioners often employ vertical or porous baffles to break up the incoming momentum and promote a more uniform velocity distribution across the basin's cross-section.8 Numerical simulations show that optimizing baffle height (typically 3 to 4 meters in full-scale basins) can reduce effluent solids by over 50% by expanding the effective settling volume.12

## **Density Currents and Thermal Stratification**

Density-driven currents are a primary cause of non-ideal behavior in both primary and secondary sedimentation tanks.7 These currents occur when the influent has a different density than the ambient water in the basin, usually due to differences in suspended solids concentration (solids-induced density currents) or temperature (thermal stratification).7 A high-solids influent tends to dive to the bottom of the tank, creating a "density waterfall" that travels along the floor toward the sludge hopper.7 This can lead to the displacement of the sludge blanket and high-velocity currents near the outlet weirs.7 Thermal stratification, conversely, can cause the influent to "float" across the surface if it is warmer than the basin water, bypassing the entire settling zone.7 Modeling these effects requires the inclusion of buoyancy terms in the momentum equations and often necessitates at least a 2D vertical (2DV) or 3D approach.24

## **Short-Circuiting and Dead Zone Formation**

Short-circuiting occurs when a portion of the flow exits the basin much faster than the theoretical HRT, while dead zones are stagnant regions where water circulates but does not effectively contribute to the treatment process.12 These phenomena are captured through the calculation of Residence Time Distributions (RTD). In rectangular basins, dead zones typically form in the corners and behind poorly positioned baffles.12 For an operator, identifying these zones is critical because they represent "lost" infrastructure capacity. Models that utilize hydraulic efficiency indicators, such as the Baffling Factor (![][image1]), provide a quantitative measure of how well the basin geometry is utilized.15

## **Particle Settling Velocity Distributions and Sludge Blanket Interaction**

In wastewater treatment, particles do not settle at a single velocity. Instead, they represent a wide distribution of sizes and densities.12 In dilute regions, "Class I" discrete settling occurs, where particles fall independently according to Stokes’ Law.26 As concentrations increase, particles begin to aggregate ("Class II" flocculent settling) or interfere with one another ("Class III" hindered settling).27 The interaction between the downward settling of particles and the upward movement of water (the hydraulic loading) determines the height of the sludge blanket.7 If the upward velocity exceeds the settling velocity of the bulk sludge, the blanket rises, increasing the risk of solids carryover.7 Real-time models must therefore incorporate concentration-dependent settling functions, such as the Vesilind or Takács models, to accurately predict blanket dynamics.27

## **Floc Growth and Shear-Induced Breakup**

In the flocculation stage, the objective is to promote particle collisions to form larger, faster-settling flocs.9 This process is governed by the velocity gradient (![][image2]), which represents the mixing energy.4 However, excessive mixing energy can lead to shear-induced breakup, where the hydrodynamic forces exceed the internal binding strength of the flocs.3 The balance between aggregation (driven by collisions) and breakup (driven by shear) is the fundamental physics of flocculation.9 For practitioners, the goal is to maintain ![][image2] values within an optimal range (typically 20-90 ![][image3]) to maximize capture efficiency without creating fragile "pin-flocs" that are difficult to settle.29

## **Mathematical Formulations for Different Fidelity Levels**

The choice of mathematical framework dictates the computational cost and the types of phenomena the model can resolve.

## **Continuity and Momentum Equations**

At the highest level, 3D CFD solvers utilize the Navier-Stokes equations for incompressible fluid flow.31 The continuity equation ensures mass conservation:

![][image4]  
where ![][image5] is the velocity vector. The momentum equations account for the forces acting on the fluid:

![][image6]  
where ![][image7] is density, ![][image8] is pressure, ![][image9] is dynamic viscosity, and ![][image10] represents body forces such as gravity.31 For rectangular basins, these are often simplified into Reynolds-Averaged Navier-Stokes (RANS) forms to account for the effects of turbulence without resolving every individual eddy.23

## **Depth-Averaged Shallow Water Equations (2D SWE)**

For many operational scenarios, the 2D Shallow Water Equations provide a significant computational speedup by averaging the equations over the water depth (![][image11]).2 This approach assumes that vertical velocities are negligible and the pressure distribution is hydrostatic 2:

![][image12]  
The SWE are particularly useful for large-scale basin analysis, such as predicting sediment deposition in detention ponds or large primary clarifiers where vertical stratification is minimal.2 However, their reliance on depth-averaging means they cannot capture density currents or the internal structure of a sludge blanket.2

## **Turbulence Closures Relevant to Basin Scales**

Turbulence is a key driver of both mixing in flocculators and particle resuspension in settlers.22 The most common closure for basin-scale modeling is the ![][image13] model, which solves two additional transport equations for the turbulent kinetic energy (![][image14]) and the dissipation rate (![][image15]).7 The turbulent viscosity (![][image16]) is then calculated as:

![][image17]  
where ![][image18] is a constant. While the standard ![][image13] model is a workhorse in industry, the ![][image19] SST (Shear Stress Transport) model is often preferred for basins with significant wall interactions or baffles, as it better predicts flow separation and attachment.23

## **Advection–Dispersion–Settling Transport Equations**

The transport of suspended solids is modeled by adding a settling term to the standard advection-dispersion equation 24:

![][image20]  
where ![][image21] is the solids concentration, ![][image22] represents the turbulent dispersion coefficients, and ![][image23] is the settling velocity.24 For operational decision support, ![][image23] is typically defined by a multi-regime settling function that accounts for both dilute and hindered conditions.27

## **Simplified Population Balance or Empirical Floc Models**

While full Population Balance Equations (PBE) track the evolution of dozens of particle size classes, they are often too computationally intensive for real-time use.3 A "minimum complexity" alternative is a semi-empirical model that predicts a mean floc diameter and settling velocity based on environmental predictors like the shear rate, solids concentration, and water chemistry.9 These models assume that the flocculation process reaches a local equilibrium quickly, allowing for a depth-averaged representation of particle growth.9

## **Comparative Evaluation of Modeling Approaches**

The practitioner must choose the modeling approach that fits the specific decision need, balancing execution speed against physical detail.

| Modeling Approach | Physics Representation | Computational Cost | Calibration Effort | Interpretability | Operational Usefulness |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Full 3D CFD (RANS/LES)** | High: Captures 3D flow, baffles, and density effects.7 | Very High: Requires significant CPU/GPU time.2 | High: Needs detailed 3D velocity/solids data.13 | High: Visualizations are intuitive for engineers.14 | Offline design and troubleshooting structural issues.7 |
| **2D Shallow Water (SWE)** | Moderate: Depth-averaged; misses vertical density currents.2 | Moderate: Suitable for large areas.2 | Moderate: Standard hydraulic calibration (roughness).16 | Moderate: Useful for planview flow paths.2 | Initial screening of short-circuiting and deposition zones.2 |
| **Settling & Transport Models** | Specific: Focuses on solids flux and blanket height.27 | Low: Often implemented as 1D or 2D.28 | High: Requires batch settling tests (SVI, SSVI).26 | High: Directly predicts effluent TSS and sludge level.7 | Daily adjustment of RAS/WAS and chemical dosing.28 |
| **Reduced-Order Models (ROM)** | Moderate: Derived from CFD via SVD/POD.43 | Very Low: Near-instantaneous online prediction.43 | Moderate: Needs a diverse set of "training" CFD runs.43 | Low: Mathematically abstract but very fast.43 | MPC controllers and real-time state estimation.17 |
| **Machine Learning (ML)** | Low: Purely data-driven "black-box".5 | Minimal: Instantaneous inference.5 | Moderate: Requires clean historical datasets.5 | Very Low: Difficult for operators to trust without "Why".1 | Short-term turbidity forecasting and anomaly detection.20 |
| **Digital Twin Architectures** | Hybrid: Integrates physics with real-time data.10 | Variable: Depends on the underlying solver.18 | Ongoing: Continuous data assimilation.18 | High: Integrated into familiar dashboards.37 | Holistic optimization and resilience planning.10 |

## **Practical Simplifications for Plant Decision Support**

Identifying when to use which model is the core of "minimum complexity" modeling.

## **When Depth-Averaged Models are Sufficient**

A 2D depth-averaged model is often sufficient for basins where the horizontal dimensions are significantly larger than the vertical (e.g., length/width \> 2), and where vertical stratification is minimal.2 This is common in primary sedimentation basins with low influent concentrations or in detention ponds where the primary concern is the total mass of sediment captured.2

## **When 3D CFD Becomes Necessary**

3D modeling is essential when the decision requires an understanding of vertical flow structures that depth-averaging ignores.7

* **Density Current Management**: If the goal is to optimize a secondary clarifier where the sludge blanket and density waterfall dictate performance.7  
* **Baffle Design**: To evaluate the vertical placement and height of baffles to maximize energy dissipation.23  
* **Steep Geometries**: For basins with bottom slopes greater than 5 degrees, where the hydrostatic pressure assumption of the SWE fails.2

## **Acceptable Parameterization Strategies**

Practitioners should avoid "over-tuning" models with too many free parameters. Instead, focus on:

1. **Settling Constants**: Calibrate ![][image24] and ![][image25] using plant-specific Sludge Volume Index (SVI) or Stirred Specific Volume Index (SSVI) data.27  
2. **Roughness Heights**: Adjust wall roughness within physical bounds to match measured water surface elevations.16  
3. **Surrogate Response Surfaces**: For complex relationships like capture efficiency (![][image26]), develop a response surface based on a sensitivity analysis of flow (![][image27]) and basin depth.51

## **Software Selection: Python vs. Established Solvers**

The choice between building a custom model and using an established solver depends on the workflow requirements.

## **Established Solvers**

* **HEC-RAS 2D**: A robust, free tool for 2D hydraulic and sediment modeling. It excels at subgrid bathymetry analysis, allowing practitioners to capture detailed hydraulic results with relatively large mesh cells.52 It includes specific options for hindered settling and erosion formulations.52  
* **Delft3D / TELEMAC**: Advanced systems for morphodynamic modeling. They are well-suited for long-term sedimentation studies and offer sophisticated erosion modules.55 Delft3D’s "MorMerge" configuration is particularly useful for capturing long-term morphology changes.58  
* **OpenFOAM**: A powerful, open-source CFD engine. It is highly customizable and can be configured with discrete phase models (DPM) to track individual particle paths.15 However, it has a steep learning curve and high computational demands.2

## **Custom Python Models**

Building custom models in Python allows for tight integration with the modern data science ecosystem.46

* **FiPy / FEniCS**: Specialized libraries for solving the PDEs of fluid dynamics (FV and FE methods).61 They allow practitioners to define and solve arbitrary combinations of coupled PDEs in just a few lines of code.61  
* **PySWMM / EPyT**: Python wrappers for SWMM and EPANET that facilitate real-time interactions with hydraulic engines for process control.46  
* **Fluids**: A lightweight repository of engineering knowledge for piping, pumps, and open-channel flow, useful for the "hydraulic glue" between process units.66

## **Recommended Workflow for Practitioner-Driven Modeling**

A reliable modeling workflow prioritizes data quality and operational relevance over numerical complexity.

## **Geometry Abstraction and Mesh Resolution**

1. **Abstraction**: Start with a simplified 2D representation of the basin’s main hydraulic flow path.29 Capture the key geometric constraints: inlet width, baffle positions, and weir crests.15  
2. **Meshing**: Use an irregular mesh or subgrid approach (like in HEC-RAS) to maintain computational efficiency while resolving fine topographical details at inlets and outlets.53 Avoid excessive refinement in zones of uniform flow to save runtime.40

## **Boundary Condition Selection and Calibration**

* **Plant Flow Variable BCs**: Use time-series data from flow meters to define the inlet boundary.10 Account for internal recycles and flow splitting between parallel basins.14  
* **Calibration Variables**: Calibrate using high-frequency plant data such as effluent turbidity, sludge blanket height (SBH) from ultrasonic sensors, and return sludge concentrations.7  
* **Metrics**: Use validation metrics that resonate with operators—specifically, the model's ability to "nowcast" observed performance deviations and predict the timing of threshold crossings (e.g., turbidity \> 2 NTU).18

## **Coupling Hydraulics with Treatment Performance Outcomes**

The true value of a model lies in its ability to predict treatment failure before it occurs.

## **Solids Capture Efficiency and Turbidity Breakthrough Risk**

By coupling the hydraulic velocity field with the particle transport equations, practitioners can calculate the "capture efficiency"—the percentage of incoming solids that are successfully settled.12 A sharp drop in capture efficiency serves as a leading indicator of a turbidity breakthrough.69 Models should be tested against "crisis" scenarios, such as peak storm flows, where high hydraulic loading rates (HLR) can shorten the operational lifespan of filter media following the basin.30

## **Flocculation Sensitivity to Mixing Energy**

In flocculation basins, the model can identify "dead zones" where ![][image2] values are too low to promote aggregation, or "hot spots" near mixers where ![][image2] values are high enough to cause floc breakup.9 Coupling these sensitivity analyses with chemical dosing models (e.g., coagulant type and loading) allows for the optimization of the entire pretreatment train.71

## **Strategies for Near-Real-Time Reduced-Order Surrogate Models**

To enable "near-real-time" prediction, the practitioner must bridge the gap between high-fidelity CFD and fast execution.

## **The Offline-Online Paradigm**

1. **Offline Phase**: Run a series of full CFD simulations over a representative parameter space (e.g., varying flow rates, solids concentrations, and temperatures).43  
2. **Basis Extraction**: Use Singular Value Decomposition (SVD) or Proper Orthogonal Decomposition (POD) to extract the dominant spatial modes (eigenvalues) from these "snapshots".43  
3. **Online Phase**: Use a fast interpolation method, such as Kriging or a response surface, to map these modes to new, real-time input parameters.43 This allows for the reconstruction of the flow field in milliseconds, providing an instant prediction of the basin's state.43

## **Conceptual Architecture for a Practical Plant Digital Twin**

A digital twin transforms the static model into a dynamic operational asset.

## **Sensor Integration and Data Store**

The foundation of the twin is a "Cyber-Physical Data Store" that integrates streaming data from SCADA, IoT sensors (e.g., vibration, temperature), and external feeds like weather forecasts.10 This layer standardizes raw readings into a structured format for simulation.47

## **Data Assimilation and Model Updating**

Data assimilation is the process of continuously reconciling the model with the physical reality.18

* **PID Assimilators**: Use simple Proportional-Integral-Derivative controllers to insert "correction flows" into the model to reduce the error between simulated and measured water levels or flows.48  
* **Kalman Filtering**: Apply extended Kalman filters (EKF) to update the model’s internal states (like the sludge concentration profile) based on intermittent laboratory or sensor measurements.44

## **Uncertainty Communication and Operator Dashboards**

The visualization layer is where the "minimum complexity" model becomes actionable.

* **What-If Scenarios**: Allow operators to test decisions—like taking one basin offline for maintenance—in a safe virtual environment before execution.10  
* **Predictive Alerts**: Use 2D or 3D dashboards to highlight regions of high turbidity risk or equipment wear, using color-coded maps that are easier to interpret than complex numerical tables.10  
* **Uncertainty Management**: Communicate the confidence level of the prediction, ensuring that operators understand when the model is operating outside its validated range.1

## **Suggested Python Ecosystems and Computational Toolchains**

For a staged implementation, the following toolchains are recommended:

* **Hydraulic Core**: FiPy for custom PDE solutions or OpenFOAM for high-fidelity RANS.15  
* **Data Science & AI**: scikit-learn for regression, pandas for time-series cleaning, and TensorFlow or Keras for Physics-Informed Neural Networks (PINNs).60  
* **Optimization**: Pywr for resource allocation and SciPy for non-linear parameter identification.17  
* **Visualization**: Matplotlib for 2D plots and HT (or similar web-based libraries) for interactive 3D dashboards.37

## **A Progressive Learning Pathway**

Practitioners should move through modeling stages to ensure each increment adds operational value.

1. **Conceptual Hydraulics (Stage 1\)**: Focus on the theoretical HRT and basic plan-view flow patterns using 2D SWE solvers (e.g., HEC-RAS) to identify major short-circuiting risks.2  
2. **Mechanic-Biological Coupling (Stage 2\)**: Add settling kinetics and simple floc models. Calibrate against effluent TSS and sludge blanket heights using historical plant data.28  
3. **Surrogate Modeling (Stage 3\)**: Develop ROMs using SVD to enable the model to run on the plant's local hardware in near-real-time.43  
4. **AI-Assisted Optimization (Stage 4\)**: Implement a full digital twin with data assimilation, using AI to refine chemical dosing and energy use (e.g., mixer speeds and sludge pumping) based on predictive forecasts.10

By following this roadmap, water process practitioners can build robust, transparent models that not only satisfy scientific rigor but also provide the actionable insights required for reliable daily plant management. The goal is a "grey-box" future where the predictability of physics and the adaptability of AI work in concert to ensure effluent compliance and resource efficiency.20

#### **Works cited**

1. Socio-environmental modeling shows physics-like confidence with water modeling surpassing it in numerical claims \- PMC, accessed March 24, 2026, [https://pmc.ncbi.nlm.nih.gov/articles/PMC11986976/](https://pmc.ncbi.nlm.nih.gov/articles/PMC11986976/)  
2. Comparison of CFD with Reservoir Routing Model ... \- SciSpace, accessed March 24, 2026, [https://scispace.com/pdf/comparison-of-cfd-with-reservoir-routing-model-predictions-202y2mw98p.pdf](https://scispace.com/pdf/comparison-of-cfd-with-reservoir-routing-model-predictions-202y2mw98p.pdf)  
3. Flocculation Dynamics of Cohesive Sediment in Turbulent Flows Using CFD-DEM Approach, accessed March 24, 2026, [https://www.intechopen.com/chapters/1172915](https://www.intechopen.com/chapters/1172915)  
4. Simulation of Turbulent Flocculation and Sedimentation in Flocculent-Aided Sediment Retention Basins \- Clemson OPEN, accessed March 24, 2026, [https://open.clemson.edu/cgi/viewcontent.cgi?article=1200\&context=scwrc](https://open.clemson.edu/cgi/viewcontent.cgi?article=1200&context=scwrc)  
5. Data-driven modeling approaches to support wastewater treatment plant operation, accessed March 24, 2026, [https://www.researchgate.net/publication/257549931\_Data-driven\_modeling\_approaches\_to\_support\_wastewater\_treatment\_plant\_operation](https://www.researchgate.net/publication/257549931_Data-driven_modeling_approaches_to_support_wastewater_treatment_plant_operation)  
6. Physics-based modelling offers a new way to study drug targets, accessed March 24, 2026, [https://www.drugtargetreview.com/article/194156/physics-based-modelling-offers-a-new-way-to-study-drug-targets/](https://www.drugtargetreview.com/article/194156/physics-based-modelling-offers-a-new-way-to-study-drug-targets/)  
7. Improving secondary settling tanks performance by applying CFD models for design and operation | Water Supply | IWA Publishing, accessed March 24, 2026, [https://iwaponline.com/ws/article/23/6/2313/95496/Improving-secondary-settling-tanks-performance-by](https://iwaponline.com/ws/article/23/6/2313/95496/Improving-secondary-settling-tanks-performance-by)  
8. Sediment Basins \- South Carolina Department of Environmental Services, accessed March 24, 2026, [https://des.sc.gov/sites/des/files/docs/Environment/docs/sedim-Basin.pdf](https://des.sc.gov/sites/des/files/docs/Environment/docs/sedim-Basin.pdf)  
9. Testing floc settling velocity models in rivers and freshwater ... \- ESurf, accessed March 24, 2026, [https://esurf.copernicus.org/articles/12/1267/2024/](https://esurf.copernicus.org/articles/12/1267/2024/)  
10. Digital Twins for Water Treatment Facilities and Water Industry Management, accessed March 24, 2026, [https://www.attinc.com/news/digital-twins-for-water-treatment-industry/](https://www.attinc.com/news/digital-twins-for-water-treatment-industry/)  
11. Digital Twins For Water Utilities: Reduce NRW By 25% \- Aqua Analytics, accessed March 24, 2026, [https://aquaanalytics.com.au/resources/digital-twin-water/](https://aquaanalytics.com.au/resources/digital-twin-water/)  
12. (PDF) Improving removal efficiency of sedimentation tanks using different inlet and outlet position \- ResearchGate, accessed March 24, 2026, [https://www.researchgate.net/publication/336428170\_Improving\_removal\_efficiency\_of\_sedimentation\_tanks\_using\_different\_inlet\_and\_outlet\_position](https://www.researchgate.net/publication/336428170_Improving_removal_efficiency_of_sedimentation_tanks_using_different_inlet_and_outlet_position)  
13. ANALYSIS OF FLOW AND SEDIMENTATION PROCESSES IN SECONDARY SEDIMENTATION TANK, accessed March 24, 2026, [https://real.mtak.hu/56264/1/606.2017.12.2.7.pdf](https://real.mtak.hu/56264/1/606.2017.12.2.7.pdf)  
14. CFD Modelling for Wastewater Treatment Processes | Request PDF, accessed March 24, 2026, [https://www.researchgate.net/publication/362159074\_CFD\_Modelling\_for\_Wastewater\_Treatment\_Processes](https://www.researchgate.net/publication/362159074_CFD_Modelling_for_Wastewater_Treatment_Processes)  
15. CFD for wastewater treatment: an overview | Request PDF \- ResearchGate, accessed March 24, 2026, [https://www.researchgate.net/publication/303690543\_CFD\_for\_wastewater\_treatment\_an\_overview](https://www.researchgate.net/publication/303690543_CFD_for_wastewater_treatment_an_overview)  
16. Challenges and Opportunities of Computational Fluid Dynamics in Water, Wastewater, and Stormwater Treatment | Request PDF \- ResearchGate, accessed March 24, 2026, [https://www.researchgate.net/publication/345142630\_Challenges\_and\_Opportunities\_of\_Computational\_Fluid\_Dynamics\_in\_Water\_Wastewater\_and\_Stormwater\_Treatment](https://www.researchgate.net/publication/345142630_Challenges_and_Opportunities_of_Computational_Fluid_Dynamics_in_Water_Wastewater_and_Stormwater_Treatment)  
17. Development and identification of a reduced-order dynamic model for wastewater treatment plants | Request PDF \- ResearchGate, accessed March 24, 2026, [https://www.researchgate.net/publication/380712346\_Development\_and\_identification\_of\_a\_reduced-order\_dynamic\_model\_for\_wastewater\_treatment\_plants](https://www.researchgate.net/publication/380712346_Development_and_identification_of_a_reduced-order_dynamic_model_for_wastewater_treatment_plants)  
18. From Pipe to Pixel: How Digital Twins Are Powering the Future of Smart Water Utilities, accessed March 24, 2026, [https://www.trinnex.io/insights/how-digital-twins-are-powering-the-future-of-smart-water-utilities](https://www.trinnex.io/insights/how-digital-twins-are-powering-the-future-of-smart-water-utilities)  
19. Data Assimilation and Inverse Problems for Digital Twins \- IMSI, accessed March 24, 2026, [https://www.imsi.institute/activities/digital-twins/data-assimilation-and-inverse-problems-for-digital-twins/](https://www.imsi.institute/activities/digital-twins/data-assimilation-and-inverse-problems-for-digital-twins/)  
20. A Review of Computational Modeling in Wastewater Treatment Processes | ACS ES\&T Water, accessed March 24, 2026, [https://pubs.acs.org/doi/10.1021/acsestwater.3c00117](https://pubs.acs.org/doi/10.1021/acsestwater.3c00117)  
21. Courses & Webinars \- Modelling & Integrated Assessment, accessed March 24, 2026, [http://iwa-mia.org/courses-webinars/](http://iwa-mia.org/courses-webinars/)  
22. Sediment Resuspension in Water Distribution Storage Tanks \- Sandia National Laboratories, accessed March 24, 2026, [https://www.sandia.gov/cfd-water/sediment-resuspension-in-water-distribution-storage-tanks/](https://www.sandia.gov/cfd-water/sediment-resuspension-in-water-distribution-storage-tanks/)  
23. A CFD methodology for the design of sedimentation tanks in potable water treatment: Case study: The influence of a feed flow control baffle | Request PDF \- ResearchGate, accessed March 24, 2026, [https://www.researchgate.net/publication/222688807\_A\_CFD\_methodology\_for\_the\_design\_of\_sedimentation\_tanks\_in\_potable\_water\_treatment\_Case\_study\_The\_influence\_of\_a\_feed\_flow\_control\_baffle](https://www.researchgate.net/publication/222688807_A_CFD_methodology_for_the_design_of_sedimentation_tanks_in_potable_water_treatment_Case_study_The_influence_of_a_feed_flow_control_baffle)  
24. (PDF) Inverse Calculation Model for Optimal Design of Rectangular ..., accessed March 24, 2026, [https://www.researchgate.net/publication/273619082\_Inverse\_Calculation\_Model\_for\_Optimal\_Design\_of\_Rectangular\_Sedimentation\_Tanks](https://www.researchgate.net/publication/273619082_Inverse_Calculation_Model_for_Optimal_Design_of_Rectangular_Sedimentation_Tanks)  
25. Hydraulic Flushing of Sediment in Reservoirs: Best Practices of Numerical Modeling \- MDPI, accessed March 24, 2026, [https://www.mdpi.com/2311-5521/9/2/38](https://www.mdpi.com/2311-5521/9/2/38)  
26. Section 7D-1 \- Design Criteria \- Iowa Statewide Urban Design and Specifications, accessed March 24, 2026, [https://www.iowasudas.org/wp-content/uploads/sites/15/2020/03/7D-1.pdf](https://www.iowasudas.org/wp-content/uploads/sites/15/2020/03/7D-1.pdf)  
27. SETTLING TESTS 6, accessed March 24, 2026, [https://experimentalmethods.org/wp-content/uploads/2017/12/Chapter-6.pdf](https://experimentalmethods.org/wp-content/uploads/2017/12/Chapter-6.pdf)  
28. Digital Twins for Wastewater Treatment: A Technical Review \- Engineering, accessed March 24, 2026, [https://www.engineering.org.cn/engi/EN/10.1016/j.eng.2024.04.012](https://www.engineering.org.cn/engi/EN/10.1016/j.eng.2024.04.012)  
29. (PDF) Modeling and Simulation of a Vertical Hydraulic Flocculator for a Drinking Water Treatment Plant \- ResearchGate, accessed March 24, 2026, [https://www.researchgate.net/publication/394567852\_Modeling\_and\_Simulation\_of\_a\_Vertical\_Hydraulic\_Flocculator\_for\_a\_Drinking\_Water\_Treatment\_Plant](https://www.researchgate.net/publication/394567852_Modeling_and_Simulation_of_a_Vertical_Hydraulic_Flocculator_for_a_Drinking_Water_Treatment_Plant)  
30. HIGH RATE PRIMARY TREATMENT – EMERGING TECHNOLOGIES \- Access Water, accessed March 24, 2026, [https://www.accesswater.org/publications/proceedings/-289001/high-rate-primary-treatment---emerging-technologies](https://www.accesswater.org/publications/proceedings/-289001/high-rate-primary-treatment---emerging-technologies)  
31. Survey of Mathematical Models of and Numerical Methods for Fluid Dynamics Water Engineering \- arXiv, accessed March 24, 2026, [https://arxiv.org/html/2512.16351v1](https://arxiv.org/html/2512.16351v1)  
32. 13.3 COMPARISON BETWEEN LES AND RANS COMPUTATIONS FOR THE STUDY OF CONTAMINANT DISPERSION IN THE M.U.S.T FIELD EXPERIMENT \- AMS supported meetings, accessed March 24, 2026, [https://ams.confex.com/ams/pdfpapers/126845.pdf](https://ams.confex.com/ams/pdfpapers/126845.pdf)  
33. Physics-Informed Neural Networks for Shallow Water Equations \- POLITesi, accessed March 24, 2026, [https://www.politesi.polimi.it/bitstream/10589/195179/2/RA\_Thesis.pdf](https://www.politesi.polimi.it/bitstream/10589/195179/2/RA_Thesis.pdf)  
34. Optimization of the sedimentation tank with CFD simulation, accessed March 24, 2026, [https://www.waterh.net/wp-content/uploads/2015/10/Article\_25.pdf](https://www.waterh.net/wp-content/uploads/2015/10/Article_25.pdf)  
35. Mike 21 Model Based Numerical Simulation of the Operation Optimization Scheme of Sedimentation Basin \- ResearchGate, accessed March 24, 2026, [https://www.researchgate.net/publication/359691548\_Mike\_21\_Model\_Based\_Numerical\_Simulation\_of\_the\_Operation\_Optimization\_Scheme\_of\_Sedimentation\_Basin](https://www.researchgate.net/publication/359691548_Mike_21_Model_Based_Numerical_Simulation_of_the_Operation_Optimization_Scheme_of_Sedimentation_Basin)  
36. Mathematical Modelling of Particle Removal and Head Loss in Rapid Gravity Filtration, accessed March 24, 2026, [https://www.researchgate.net/publication/244611628\_Mathematical\_Modelling\_of\_Particle\_Removal\_and\_Head\_Loss\_in\_Rapid\_Gravity\_Filtration](https://www.researchgate.net/publication/244611628_Mathematical_Modelling_of_Particle_Removal_and_Head_Loss_in_Rapid_Gravity_Filtration)  
37. Using Digital Twins for Better Wastewater Treatment \- DEV Community, accessed March 24, 2026, [https://dev.to/hightopo/using-digital-twins-for-better-wastewater-treatment-2ima](https://dev.to/hightopo/using-digital-twins-for-better-wastewater-treatment-2ima)  
38. Full article: Comparing 2D models in simulating suspended sediment processes in vegetated flow \- Taylor & Francis, accessed March 24, 2026, [https://www.tandfonline.com/doi/full/10.1080/23249676.2025.2566313](https://www.tandfonline.com/doi/full/10.1080/23249676.2025.2566313)  
39. Comparison of Hydrodynamics Simulated by 1D, 2D and 3D Models Focusing on Bed Shear Stresses \- MDPI, accessed March 24, 2026, [https://www.mdpi.com/2073-4441/11/2/226](https://www.mdpi.com/2073-4441/11/2/226)  
40. Creating 2D Flow Areas and Computational Mesh in HEC RAS | CivilGEO \- YouTube, accessed March 24, 2026, [https://www.youtube.com/watch?v=Qh7-tSGu4XA](https://www.youtube.com/watch?v=Qh7-tSGu4XA)  
41. Data-driven modeling techniques for prediction of settled water turbidity in drinking water treatment \- Frontiers, accessed March 24, 2026, [https://www.frontiersin.org/journals/environmental-engineering/articles/10.3389/fenve.2024.1401180/full](https://www.frontiersin.org/journals/environmental-engineering/articles/10.3389/fenve.2024.1401180/full)  
42. Modelling the COD Reducing Treatment Processes at Sjölunda WWTP \- Lund University Publications, accessed March 24, 2026, [https://lup.lub.lu.se/student-papers/record/5368008/file/5368010.pdf](https://lup.lub.lu.se/student-papers/record/5368008/file/5368010.pdf)  
43. Reduced-order modeling of solid-liquid mixing in a stirred ... \- CORA, accessed March 24, 2026, [https://cora.ucc.ie/server/api/core/bitstreams/4a996cbb-a521-401e-a974-1f3b5143bb90/content](https://cora.ucc.ie/server/api/core/bitstreams/4a996cbb-a521-401e-a974-1f3b5143bb90/content)  
44. State estimation of wastewater treatment plants based on reduced-order model, accessed March 24, 2026, [https://www.researchgate.net/publication/328154902\_State\_estimation\_of\_wastewater\_treatment\_plants\_based\_on\_reduced-order\_model](https://www.researchgate.net/publication/328154902_State_estimation_of_wastewater_treatment_plants_based_on_reduced-order_model)  
45. State estimation of wastewater treatment plants based on model approximation | Request PDF \- ResearchGate, accessed March 24, 2026, [https://www.researchgate.net/publication/322257890\_State\_estimation\_of\_wastewater\_treatment\_plants\_based\_on\_model\_approximation](https://www.researchgate.net/publication/322257890_State_estimation_of_wastewater_treatment_plants_based_on_model_approximation)  
46. Intelligent control of combined sewer systems using PySWMM—A Python wrapper for EPA's Stormwater Management Model \- PMC, accessed March 24, 2026, [https://pmc.ncbi.nlm.nih.gov/articles/PMC11998929/](https://pmc.ncbi.nlm.nih.gov/articles/PMC11998929/)  
47. Digital Twin Platform for Water Treatment Plants Using Microservices Architecture \- PMC, accessed March 24, 2026, [https://pmc.ncbi.nlm.nih.gov/articles/PMC10935207/](https://pmc.ncbi.nlm.nih.gov/articles/PMC10935207/)  
48. (PDF) Digital Twins of Urban Drainage Systems: innovative data assimilation algorithm for continuous state update \- ResearchGate, accessed March 24, 2026, [https://www.researchgate.net/publication/396400725\_Digital\_Twins\_of\_Urban\_Drainage\_Systems\_innovative\_data\_assimilation\_algorithm\_for\_continuous\_state\_update](https://www.researchgate.net/publication/396400725_Digital_Twins_of_Urban_Drainage_Systems_innovative_data_assimilation_algorithm_for_continuous_state_update)  
49. Digital Twin: a tool to optimise water treatment plant management | SUEZ, accessed March 24, 2026, [https://www.suez.com/en/water/water-conservation/water-plants/digital-twin](https://www.suez.com/en/water/water-conservation/water-plants/digital-twin)  
50. How Digital Twins transform wastewater treatment with real-time optimization, accessed March 24, 2026, [https://blog.veoliawatertechnologies.com/en/how-digital-twins-transform-wastewater-treatment-with-real-time-optimization](https://blog.veoliawatertechnologies.com/en/how-digital-twins-transform-wastewater-treatment-with-real-time-optimization)  
51. Multi-decadal simulation of estuarine sedimentation under sea level rise with a response-surface surrogate model \- the NOAA Institutional Repository, accessed March 24, 2026, [https://repository.library.noaa.gov/view/noaa/57335/noaa\_57335\_DS1.pdf](https://repository.library.noaa.gov/view/noaa/57335/noaa_57335_DS1.pdf)  
52. 2D Options \- Hydrologic Engineering Center, accessed March 24, 2026, [https://www.hec.usace.army.mil/confluence/display/RAS2DSed/2D+Options](https://www.hec.usace.army.mil/confluence/display/RAS2DSed/2D+Options)  
53. Summary of 2D Sediment Parameters and Options \- Hydrologic Engineering Center, accessed March 24, 2026, [https://www.hec.usace.army.mil/confluence/rasdocs/h2sd/ras2dsed/latest/summary-of-2d-sediment-parameters-and-options](https://www.hec.usace.army.mil/confluence/rasdocs/h2sd/ras2dsed/latest/summary-of-2d-sediment-parameters-and-options)  
54. 2D Computational Options \- Hydrologic Engineering Center, accessed March 24, 2026, [https://www.hec.usace.army.mil/confluence/rasdocs/h2sd/ras2dsed/6.1/sediment-data/sediment-computation-options-and-tolerances/2d-computational-options](https://www.hec.usace.army.mil/confluence/rasdocs/h2sd/ras2dsed/6.1/sediment-data/sediment-computation-options-and-tolerances/2d-computational-options)  
55. What is Delft3D? Competitors, Complementary Techs & Usage \- Sumble, accessed March 24, 2026, [https://sumble.com/tech/delft3d](https://sumble.com/tech/delft3d)  
56. Which mathematical simulation models should use to simulate coastal erosion?, accessed March 24, 2026, [https://www.researchgate.net/post/Which-mathematical-simulation-models-should-use-to-simulate-coastal-erosion](https://www.researchgate.net/post/Which-mathematical-simulation-models-should-use-to-simulate-coastal-erosion)  
57. A Comparative Study of Comprehensive Modeling Systems for Sediment Transport in a Curved Open Channel \- MDPI, accessed March 24, 2026, [https://www.mdpi.com/2073-4441/11/9/1779](https://www.mdpi.com/2073-4441/11/9/1779)  
58. Model Sensitivity Analysis for Coastal Morphodynamics: Investigating Sediment Parameters and Bed Composition in Delft3D \- MDPI, accessed March 24, 2026, [https://www.mdpi.com/2077-1312/12/11/2108](https://www.mdpi.com/2077-1312/12/11/2108)  
59. Dam Break Simulation with HEC-RAS and OpenFOAM \- EarthArXiv, accessed March 24, 2026, [https://eartharxiv.org/repository/view/2708/](https://eartharxiv.org/repository/view/2708/)  
60. Using Hybrid Machine Learning to Predict Wastewater Effluent Quality and Ensure Treatment Plant Stability \- MDPI, accessed March 24, 2026, [https://www.mdpi.com/2073-4441/17/13/1851](https://www.mdpi.com/2073-4441/17/13/1851)  
61. FiPy: A Finite Volume PDE Solver Using Python \- NIST Pages, accessed March 24, 2026, [https://pages.nist.gov/fipy/en/latest/index.html](https://pages.nist.gov/fipy/en/latest/index.html)  
62. FEniCS | FEniCS Project, accessed March 24, 2026, [https://fenicsproject.org/](https://fenicsproject.org/)  
63. Multiphysics Simulations in Python with FEniCS and FEATool, accessed March 24, 2026, [https://www.featool.com/tutorial/2017/06/16/Python-Multiphysics-and-FEA-Simulations-with-FEniCS-and-FEATool/](https://www.featool.com/tutorial/2017/06/16/Python-Multiphysics-and-FEA-Simulations-with-FEniCS-and-FEATool/)  
64. pinns · PyPI, accessed March 24, 2026, [https://pypi.org/project/pinns/](https://pypi.org/project/pinns/)  
65. EPyT: An EPANET-Python Toolkit for Smart Water Network Simulations \- GitHub, accessed March 24, 2026, [https://github.com/OpenWaterAnalytics/EPyT](https://github.com/OpenWaterAnalytics/EPyT)  
66. fluids \- PyPI, accessed March 24, 2026, [https://pypi.org/project/fluids/](https://pypi.org/project/fluids/)  
67. 1D and 2D modeling with HEC-RAS & InfoWorks ICM: Differences, similarities, and an integrated workflow \- Autodesk, accessed March 24, 2026, [https://www.autodesk.com/blogs/water/2024/08/20/2d-modeling-with-infoworks-icm-and-hec-ras-differences-similarities-and-an-integrated-workflow/](https://www.autodesk.com/blogs/water/2024/08/20/2d-modeling-with-infoworks-icm-and-hec-ras-differences-similarities-and-an-integrated-workflow/)  
68. CFD Modelling for Wastewater Treatment Processes: IWA Working Group on Computational Fluid Dynamics, accessed March 24, 2026, [https://api.pageplace.de/preview/DT0400.9781780409030\_A49387895/preview-9781780409030\_A49387895.pdf](https://api.pageplace.de/preview/DT0400.9781780409030_A49387895/preview-9781780409030_A49387895.pdf)  
69. Treatment of Produced Water in the Permian Basin for Hydraulic Fracturing: Comparison of Different Coagulation Processes and Innovative Filter Media \- MDPI, accessed March 24, 2026, [https://www.mdpi.com/2073-4441/12/3/770](https://www.mdpi.com/2073-4441/12/3/770)  
70. Effects of Hydraulic Loading Rate and Filter Length on the Performance of Lateral Flow Sand Filters for On-Site Wastewater Treatment | Request PDF \- ResearchGate, accessed March 24, 2026, [https://www.researchgate.net/publication/274305153\_Effects\_of\_Hydraulic\_Loading\_Rate\_and\_Filter\_Length\_on\_the\_Performance\_of\_Lateral\_Flow\_Sand\_Filters\_for\_On-Site\_Wastewater\_Treatment](https://www.researchgate.net/publication/274305153_Effects_of_Hydraulic_Loading_Rate_and_Filter_Length_on_the_Performance_of_Lateral_Flow_Sand_Filters_for_On-Site_Wastewater_Treatment)  
71. Optimizing Flocculation and Settling Parameters of Superfine Tailings Slurry Based on the Response Surface Method and Desirability Function \- MDPI, accessed March 24, 2026, [https://www.mdpi.com/2075-163X/15/11/1216](https://www.mdpi.com/2075-163X/15/11/1216)  
72. Development and Optimization of a Flocculation Procedure for Improved Solid-Liquid Separation of Digested Biomass (Poster), NREL, accessed March 24, 2026, [https://docs.nrel.gov/docs/fy16osti/65278.pdf](https://docs.nrel.gov/docs/fy16osti/65278.pdf)  
73. Optimization of Flocculation Settling Parameters of Whole Tailings Based on Spatial Difference Algorithm \- MDPI, accessed March 24, 2026, [https://www.mdpi.com/2073-8994/11/11/1371](https://www.mdpi.com/2073-8994/11/11/1371)  
74. Discrete Physics-Informed Training for Projection-Based Reduced-Order Models with Neural Networks \- MDPI, accessed March 24, 2026, [https://www.mdpi.com/2075-1680/14/5/385](https://www.mdpi.com/2075-1680/14/5/385)  
75. A water resource simulator in Python \- The University of Manchester Research Explorer, accessed March 24, 2026, [https://research.manchester.ac.uk/files/158453438/pywr.pdf](https://research.manchester.ac.uk/files/158453438/pywr.pdf)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAABZElEQVR4Xu2UvUsDQRDFRxLBYET8iBIQ0gl+gIiVvYhVehtbU6cRrGz8ByxFEAsR1FYLsRAsFLSMdhaCXRBBsFXfc2dv9/YKyebKPPhxN7PLvL2dvRXpKVJ9YEyfuWsW3IMWOAPD6eF4LYIPcAj6QRncKHzvWldiDOY1tgavoKq5rvQDTkBR43HwBD7Bgp0UK+4zDepebga8gzcw5eWjtAvaYvZ/X3kUY3ou7quiNAiuwZ244oT9oMGWmxonNpCNXAny3J4vsOTlRsEGGPByFGtwUetiTmBKLMBCQ16uBL7BmpfjT3ck2WO7A471nb16BsvJqLhm+vvMCaeSXU1owEXdgm2NR8ADaGr8J3scrQGLsngtmeEUGtjttX2y/w7npVQR02SuhtfEdHo4UbQBNSH/X3ChwSR4kazBnsYdKzTgaboABxrbL9rUuGOFBlQDXOo77zH2c84N56MCWJUcr/ae8tMv1spGy7dkySIAAAAASUVORK5CYII=>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA8AAAAaCAYAAABozQZiAAABFklEQVR4Xu2SMUuCURSG38iGsEUE0c3ApalAQglcXFxcxNEf4E/wB/QvIoj2CBrcw9GgycGhQURcHAKhoaV8X86nnO9q6Zw98PBxz7nn495zD/BnSdMcPXGxI5p06xgHtES79JtO6Sft0Ty9pa3lZk+WPtIv+kQPo7i+DfpK5/Q8iq+4oGP6TmuwE3i0vqYvNBXkMIMVXoUJxyXs2DE6dEAzYSJAzTvzgVM6gf1gGyo+9oE2rKtFH9yVe1jxWhO2ocd/hhWH3RXqgY7qXQ1Mgj7Ain9DHdaeuzChRikRa4RD19Hbas/aZBVgI1gJExFq5Ad+mCzRhE1XGfG752kfNq4bJ2vJG+xoI9gL3NAhrdI6bDT/2TMWulgvUpLZtBkAAAAASUVORK5CYII=>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABsAAAAaCAYAAABGiCfwAAAA5UlEQVR4XmNgGAaAGYjDgFgBTZzqYAMQPwfir0BsjCZHE+DLMGoZFsAIxFZAHIID2zBAEgUMDE7LQJrEgFgYXYIEQNAykCU5QPwWiA8B8RUglkdRQRx4BMTvgPg/lL6EKg0BMUB8G4hVoXwZIJ6EkKYuOAHESxkg8QMCuUDcAJelMngIxL8YIL7RBmJuBtRIpyoAGV7IAAnjvwyQMBdBUUEloAbEzkh8ISA+DMSaSGJUASxAvByI56CJg4KTH02MYgCzDJT6YMCMAVJy0wQYAPFpIJ4FxPsYIHklHEXFKBgFo2BIAADy+SvP8JUefgAAAABJRU5ErkJggg==>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAmwAAAAiCAYAAADiWIUQAAABaklEQVR4Xu3aoUoEQRwH4DEYRMEmGmy+hIjJYrEbfATxVQSbT2ARbGIwnMVgMRrEYPIJDAbRGWaPG+Zu9Q4OFm6/D37s/meWvYs/djcEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA6cxXz80eOR5d2ai/k//NQbwAALLqVkIvQer0RrdULHdmOuWnOl2Neiz0AgF64ixnUi9FtvdCR65ijYk4Fc6mYAQAW3vApWzqWa6fF/J/zkO/x2cxPzTyPp3TvYbywbRUzAEAvpG/Vvov5uTgv7YZcmCZJxWpY2BKFDQBgzlIR2g+5lKXvxiZJryIP6sXGtIVtI+TC1ZbafRgvbKvFDADQGycxXzEv9caU3sKosKVi11bYZnUYc1HM5ZNAAIDeSSVrp16c0mbIZSrd47I5tr0+ndVjzFnMR8i/AwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAF34BB484AiOnZYsAAAAASUVORK5CYII=>

[image5]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAwAAAAZCAYAAAAFbs/PAAAAd0lEQVR4XmNgGAUjBygA8UQgvgDEj4C4DyruCcSzgHglEN8FYheoOIMuVOA/FC+EimcA8S8kcV+oOBygawABXiA+DBUnSgMPEB+Aig9VDTpA/B4qjqEhHIifMiA03mGAxMUiJLGHcNVIgBWIxZH4AkAsjMQfeQAA5qAxseOd14YAAAAASUVORK5CYII=>

[image6]: <data:image/png;base64,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>

[image7]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAaCAYAAACO5M0mAAAAu0lEQVR4XmNgGAW0BjxALIYuiAzUgPg4ED8C4hNAHA7EjCgqgMAFiJ8DcT4QM0PFfgKxJVwFFDwD4ulAzIIk9h+IJyHxwcZ/BWJjZEEGiMKFyAJ+QNyKLAAE3AwQhenIgiBFIMXIQBOInwCxIkwAFBQHgFgHJgAF5UCcgSygxADxbQySGCgE3gExK5IY2EqQW0DhtgWKQSEQiawIZu1bZEFsAGbtATRxDODJALEWPWgwQCIDxER9dImhBgBnnh/2TCJJ+QAAAABJRU5ErkJggg==>

[image8]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAZCAYAAAAIcL+IAAAAyElEQVR4XmNgGAXUBhxAzIjE5wFiYSQ+GNgA8VUg3g7EskA8B4ivQLEBsqJFQMwCxP+BOAEmAQUgMU8QwxXK4Abit0CsiaQIBEAKy5EFlID4MBDzIomB2CCFvkhiDC5APAlZgAFiOoYtrUAchCwABNFAvJwB4n4wAFn7HIhjoHxQMJUB8W+YAhgAWfsPiE8A8WoGiFtBwWWPrAgEQNaCHM0KxOIMkIBGDnwwAAXLHgaIo/ECkDUg0+4DsR2aHAoIQcLSaHJDCgAAf4wgLsOIhm8AAAAASUVORK5CYII=>

[image9]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAwAAAAYCAYAAADOMhxqAAAAvklEQVR4XmNgGAWDEbACMT+6IC6gD8SfgHgPEHMjiZcD8X8kPhxEM0AkWpHEOIB4KxB/RRKDg/lA/A+IXZDEZID4CRCfRhKDg98MENNApsIAyDaQrSDbMQBIogqJzwPEBxggzjFmgGhih0myMEA0gDwIAzpA/B6IrwKxCBAvhKoDA5C7/0LxFiBeCcRWQDwFiL8A8T4GSJDDAcjkdAaI+yWBWAxJTgCNDw86G2RBfAAWdCB3EgXCgPgbuuBwBgD1gSDtBPGoXQAAAABJRU5ErkJggg==>

[image10]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAkAAAAYCAYAAAAoG9cuAAAAdklEQVR4XmNgGCaAG4hjgHgDED8CYjsgZkRW8BqI/wNxMwNE8U4o3xdZEUjgNxDbQPkFQHwLiOXhKhggir4CsTGSGDMSGwywKYIDMSA+zABRBMLvGCCOXoGsCAZgilAcig6GnCJOIPZkQCjqBOIQIJZGVjR8AQDJaST/DxvklgAAAABJRU5ErkJggg==>

[image11]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAbCAYAAACqenW9AAAA2ElEQVR4Xu2RvwsBcRiHX2UgA0VJNpvJZDMaMVj9AVZZlH9GBlmsNoOyKLNddslioPC898N978tlU8pTT9d93rvr/X5O5Lep4B4v2LVmL+Rwg2esWrO3rHAr7osfOeAM4/bgHXfs22EUV6xhDLOYCY8DSnjDMaa8rC0RzdRxgWkja+LAuH8yxJaV6Vc7ViYJnIu7io/uPcKykTkUcSfBrmaWNDIHbUCbMNGVtEqlgQV/oN36A0V/yhSPmBf3R+nVOf0al/6THj084UTCDTnl6yFtNNeD/vkiD/+aHslAHSlhAAAAAElFTkSuQmCC>

[image12]: <data:image/png;base64,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>

[image13]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACoAAAAZCAYAAABHLbxYAAABUklEQVR4Xu2VzytFQRSAj1AWiiKSJGWHLJASK5SNbCyUP8DeRlmKf0I2FhZkydaPpaWFEqmXspJsZKPwnWbGmzu8ups3jZqvvpo5Z173vJk754pkMv+HS3zENzwMckmxhAf4hetBLik68QYr2FtMpcUEvuMxNgW5pFgTc+wbXqzVmhS6k584Z+d7eIsPOO8WRaIHt/EeP3DGT2rgFAfFXKoOvBazyyveunqjz9vF5jDh0AXneIL9NqZFj2GjW/QH+mroDpSx5sMtA/iKw2HC0SCmUPVJzLaXZUtM/y3jqP1NLValWoezcOzamirYhwv4LNVdjYle5J0w6KOtyW9Lm7hox5M4Zcf1Rgv1u84v9IZPe3P9V/puDon5nMZqUW14J8XTnHUDLeICu35SIiNiLtYVjnvxGBzhC+7jGS77yXZ/YunGljAYCddJtEVmMplMynwDcHtANKljcbEAAAAASUVORK5CYII=>

[image14]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAZCAYAAADnstS2AAAA3klEQVR4Xu2RqwoCQRSGj6CgeEcRBN/BZDFbLBaLGGziI/gEFrv4DmLWYtgomHwExWo1CF7+fy7LMs4Wm+AHXziX2T1zRuS3acIzvMOJU/ugCg/wBltOzcsVrmHSLfh4wambjOMJO5E4AVOROCQPL7BhYs59hFuYs02WHpzBNpzDDOzCPSxG+hRsXMEFzJocR6iHHQYWd6IvyPUNRX/ZC+fkvGU4hg+4lJgVcgPcBOFlAngSPcLI5BQ8zYfggxA7UgALcGDyioroFbFo6Ys+vBHPnksw7eT465qT+/Mdb4V+ITKqENUhAAAAAElFTkSuQmCC>

[image15]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAYCAYAAADH2bwQAAAAYklEQVR4XmNgGAUkg1VA/AOIG4FYFYiFgZgRJskPxH+BOBgmgA7KgXg9ELOiS4CAJBA/BGJTdAkYgClQQpeAAU4g3sGAxwQYuA7Ed4B4LhCfBmJrVGmIl0BeA1kpgCY33AEAIiYLu8ye3SYAAAAASUVORK5CYII=>

[image16]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA8AAAAbCAYAAACjkdXHAAAA70lEQVR4Xu3SOw4BURgF4F+QSBDxCIVWQ0Hh0bAGG7AAVsAqJKKhkNiAVqcRpVqIRCtBRKXFuXMvc+ePYabmJF8yc+5k5j6G6J9/XCYJAdZ5Icw6S0JQgB2k2NgK1m96S8owAR/rb9ADD+staUKHdWJGe8iw3hLx1jHUWN9SnonDQrs3kiC5trTWVeACfq0TS9to90aKcCVzvSU4wvD1hIxY2pR1RnknOf06nKFN5lerMIeTklc9RWEJB8iR/a6Ko9xClg84SYPkZn38YezSh5G6jukD3xKEGcmvR0iev+OIfejCQHEd8QIxXf3cfy4PyJIf/59cg+sAAAAASUVORK5CYII=>

[image17]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAmwAAAAsCAYAAADYUuRgAAACTUlEQVR4Xu3dv6tOcRwH8K9QfoVBin9AKAZRxGaR7oKBP0BMNotVVoO6C5Y7MVgUi+mWW24GMoiUgVgMNpPE59M5j+c533puV557zxOvV7075/l8Ts/87XvO9/stBQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIDJ2RI5Frkemal6AACssheRr5HNVX1NaQZui1UdAIBVlgOzn3Wx9ao0fQAAenQ4Ml8Xw432mq9FAQDo0YPIqcjGyNvIbPs7Z90yd4ePAgDQh++R3ZGjkbnIvW4bAIC+5Sza58ieugEAwHTIV6JpsPDgwqABAED/NkSOt/c5YNsW2T9sAwAwaacjPyKfIs9LsyXHzc4T462NbK+LAABMRg7McqB2oKrnrNneqgYAQA9ysHaiLoandQEAgK482ulZaTanHRh3qkDKmbJzSyRfedbyu7P5uggAwPLlAG1wvNPlMvmTA05GztTFZXryBwEA+CflDNu39j5nwt6N9B6P3P+Ng5GZuhjOR9bVRQAAunLm61ZpFgM8bGubSrOC801pThiYhPy/UTk4PDvy+2V7vThSAwAgLEbul2bLjFF5sHrugTYpV0vz6vV25GNkX7f9e/HB+04VAICxPrTXPHB9pe0ow2/c8jWsbT4AAJYhV47O1sUVcimyELkTeRTZ2W0DANC313UBAIDpcqQuLOFKaRZH7Iqsr3oAAPTsUORLXQQAYHrMRa7VRQAApkcuRhhs7Lu12HQXAGBq5fdr9b5xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAPD/+gUtg0iZy/vakwAAAABJRU5ErkJggg==>

[image18]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABcAAAAZCAYAAADaILXQAAABa0lEQVR4Xu2UvytGURjHH6HoRUnhLQMGRWFRSupd/APEZLCx+AeY+QcsBgwGm2zEJkysyMBgsRiUQRn8+H577vGe97lc5x4m+dSne+/znPt0es4PkX8iqIItsAgbvHgtLHjfuWDRYfgC3+AdfIZHsB6uw+mP0TlohzvwFfbD6iTO5zg8gI9wMIkHMQTv4QMcMTmfJ9GZ5+JUtAULom35iluJaAkLn8NWmzBwEr02mEWXaPF5m/iESdFFDWYTnsFmm/gp3L+HcEuyex2FK87Zfwfb12SDWdTAbQkrHrImKfjTvmQvVCfcs8FQeNRv4ICJ98FjOCXpNemGY973iujapSjBa9EteQU34CU8gT3eOB8W7kjeG0UnMVdOV8L7gweEe3kGtlWmUyzDuuSd//H0jpbT8bDorvc9AS9Er2d32UXDlnCdZuEaXBJt4ao/KBa2hDPnXeRmyjPj2hSNa8miTfwG3CHctv42/EO8A1QNNz3OkgwxAAAAAElFTkSuQmCC>

[image19]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAC8AAAAZCAYAAAChBHccAAABkElEQVR4Xu2WwStEURTGj1AKISJJSnaShERsRNnIVvkDZKukLMU/YGNjYyGRJVuDnR0LJaUmxUaxkQWF73Pv6505ZpjNvF65v/o1c7/73syZ9+49b0QCgf/LKbyDL3DPzKWeGbgDP+GimUs9TfAKZmFb7lT6GYSv8ABWmLnUMy9uySyrrMabJiptQHjFP+CEH2/Ba3gLJ6ODEuAG9tjQUwfP4LCdeIdHsEvcxm2El+Luxqw6rpSwqGYbGsbgtA1ZZAYewg6f8Yf0w/LooDxwWbUWaYs/pxAbZsxzeEFt1quDMnHF03u4pif/YFXc86EY2c0KUQv3TTYnriZNJ2zQAdtkFrbDKfgo8dVPChZli+edeDbZjyXMNqlb5IrE62oIjvj3pYTL88Jk23BXjbkPj9X4G3aWUTVeF/dh3eL+KiTRLqOH5AN8Erdczv0rl9ybuLvQF51AWNiJ5O5ytipuXp48oPJSsyCuWBa6BKvhps+4F8fjQ2PqbSCuM1TZMAHYTfT3spmwlrwPp0AgEAj8yhdDJksQKAWnvAAAAABJRU5ErkJggg==>

[image20]: <data:image/png;base64,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>

[image21]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA8AAAAaCAYAAABozQZiAAABA0lEQVR4Xu3SMUuCURTG8SPqEAkSQtQQ6CLYUEJEEPQVgginPoCLu6vg19DBPYKGnKXagqaGIFsiWhyCwMGl+t/uVc57Mm5z+cAPeZ/zXricV5E/mwLWkVNdFsvqOZEU9nCBD7xggksU0cHJ9GWdNZzhHedIh979HuEWb9gO/SxVPGGMQ/E30HHPbdxgxcxkhFfs24HKrvhrJ9LEHVbtwMQtr6KLEp7R0OUPcYeXdFEXv9UdXf42PfGHvy0hFvfxB+IP2+1Gk8Gp+MOxuJ205pXucGIRJkX0sWH6r+IBB3YQkhf/Vz22g2nc4BFbpt/EFWoS2clQ/PXv0Q2uUdYvLfK/8gk/KihVrGe+kAAAAABJRU5ErkJggg==>

[image22]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA8AAAAbCAYAAACjkdXHAAAA9ElEQVR4Xu2RPw4BQRSHn0QpESEOoCNEoZI4AIVOonAAF5C4BxWRKEkUopE4A6VSo9FpJAqF8PvlzdgxZDnAfsmXnX1/dt7MikQ04PhPWftGCbbgCj7g0bxbO3Bkcn3T88FAtGDqJwwn2PSDJAW3os1dL2dZw5ofJHl4hldYceIFmDHrJSw7uRc8F3fl7pyCJOBC9MNkDrNm/cIdeSd6q3vzznsIxY58gz3RGx7Cu+hEoXwbOQ03EoxMeIwPJqLNfFpycCZBQxzWg3SAPW/YiEWY9IPkYvz6G0R3dad6wz+vSwy24cENVkVvl42/ZB3rIyL+4wm53T9I1ue+FgAAAABJRU5ErkJggg==>

[image23]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABMAAAAZCAYAAADTyxWqAAABQklEQVR4Xu2UvytFYRjHH0VRZKCkKINFiJKUMhoMbmFRysAig8GCP8Auo4EoA7vFYKCUUnZZTHbFJj7fnnPuPe+rk3uO9X7q0+k837fnvr/ONWtQhibcxaPIvewgWMPzJJNbYeyo2TS+4jfe4zKOZgcl78f4hOs4FMYh++bNrrA1ysQAPsTFPLbNm91hR5Rp9gf2e+m5zJs303J7o2wGb7ArqucyiZ/4jmOZeide42ym9ieaTXoImqUYxkccTAfVi/ZJ+6VmO0ntAjeqIwqgE9RJqtlhUtN7e3VEQU7Nm+nZh1NhXAwtT81uzS+orkRp5sybfWElylL0dZyZ/9ACPodxjQn8wBNsibIUzf4NN3EE+8O4RhsuYnccZBjHF6utYCmMi7GKzeZfw6X5YZVGW7CSPPXnkLcddaH72GP/bNLA+QHDCDhMXtdNaQAAAABJRU5ErkJggg==>

[image24]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABMAAAAaCAYAAABVX2cEAAABXklEQVR4Xu2UzStEYRTGj1AUSVbKYhazEbKQlFhSFqxNrMxGFjYWPspS+QdsJLKwsMfCQhqlRMmCvX9BsZGP53HuyzlvM113Zju/+tW853nn3PveOXdE6lRDA1yDu5HrdhNYgEdJRpd9rLDZKHyGX/AazsIBuylZ78N7WIS9Pvbwqmx2GAeGedgWF8uxJdrsFLZEGcnBm7hYiWnRZjxud5SNwwvYFdUrMgzf4AscNPUOeA4nTC0VNmCjdzhm6itwBzaZWio8WvhFeWTSB+9gPmz6L+3wSrTZalI7hou/OxRedFN01gqw2cd/cCzCePTAER//wBHibBLueTKZg3fEZiXRAQ1fCvDuN8y6E96atWNOtNknfIgywiOGR0A4wJdm7ZgSbfYBZ6KMZGo2BF/hgZR/sJmapcHXbM+swzhVzRlsTT73w0eTZeYEbouODV+zJR9no1H0v2xS9L2tUwPfD+k+N0ePty0AAAAASUVORK5CYII=>

[image25]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABIAAAAZCAYAAAA8CX6UAAABCUlEQVR4XmNgGAWkghAgXgrEs9CwJ1SeB4jr0eRcoXIoQJcBYdh/IM4A4gAgFoHKcwJxGhB/g+IZSHIYgBeIDzNADEIHB4A4DogZ0cSxAk0gfgvEX9HEnYDYFE0MLwhigLjmKpTPCsRlQLwKroJIMIkBYtB8IBYC4rVAvAuIuZAVEQIwb4ECcgIQmwPxCQaIwVOQ1BEEMG/BXAQCOVD+E5giYgDMW4uAmBkqpsgAMQRbLGIFgkB8mgGiIRpJHBTVIG+BxEEJkiCAhc8nINZHk7ME4p9A7IEmjhWAYgdk6zoGzBgCJYFeBkjacmRAeBsFwGyDBTIMb4XKw1yKLPcIiOWg8qNgFFANAADlZT4B7P6vuQAAAABJRU5ErkJggg==>

[image26]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAbCAYAAABFuB6DAAAAyElEQVR4Xu2RMQ5BURBFr6BCFIRSIhq1VkSh0diGXqOQ6GxAI9HYgCUo9GodtRWoRLjXe2Qy4rcUTnKS9++8vJnMB/58jbz7TtOKDYp0TRv0Rvd0SrOxrmyoQ48uaSqGC5qJl4SysQ592qEFeqJ1c0m8XnzSpBuaM5lePtOWyTCgMxuQKsLMZRvOEcawtOkKYf4HWs0W7/ON4Obr0qsNENoe4dpquSUbILS9wLT9hFpqNYloLfpbWk0imktr2fmCp0YPdOILv8wdYS0c6YcXvW8AAAAASUVORK5CYII=>

[image27]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA8AAAAaCAYAAABozQZiAAABSUlEQVR4XuWTPS9FQRCGR0Qi3EiQEIkbn4lIFIROcjulRiXR0wgVGq0/oCEaf4CIQqGR20lodaIgOoUoNL6fubN7s2ePe7bnTZ7k7My8Z8/OnBX5s+qFPijFiUZqggpcwgM8wgdcwWxQl1M/nMILLAXxLjiGzyCW0aTYTjcwGuVUZbiFqTiheoI7GIzioXZgNw5uQVXSjZmHe7Em1jQk1pTwjI20IpFZTd8w7AMF0k++hk5d6FgOxcztQdFv0iNVxerVVw+oOaUJeIZFH2iFM0mb/Zhyc9b2q7n2KagD1mHNrVvgwNVsulhd0/Aq9h8PwDksw4aYUQ1fsOfWGemOWqBv34YFF9cjncC7y+eMXs3wJrbDkVhT9sX+87Ggri14LpRO4gJGYFzsRauZigLp3LVJHr0wPZmKhLxRL81MlEtqTuwydMeJ/6gfMns9Ql2dnWgAAAAASUVORK5CYII=>