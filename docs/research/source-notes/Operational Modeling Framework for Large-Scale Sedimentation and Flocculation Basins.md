# **Operational Modeling Framework for Large-Scale Sedimentation and Flocculation Basins**

This framework provides a technical roadmap for a water process practitioner to design computational models specifically for large-scale rectangular basins. Based on the provided design criteria (160 MGD nominal plant rating with \~40 MGD per basin), the goal is to identify the minimum level of physics-based complexity required to optimize existing geometry—specifically baffle and launder placement—using Python-driven toolchains.

## **1\. Plant-Specific Modeling Constraints**

Based on the provided record drawings, the modeling domain consists of two distinct zones with the following characteristics:

| Parameter | Flocculation Section | Sedimentation Section |
| :---- | :---- | :---- |
| **Volume** | \~800,000 gal (0.8 MG) | \~1,663,600 gal (1.6 MG) |
| **Dimensions** | 60' W x 80' L x 25' D | 60' W x 340' L x 11' D |
| **Nominal Flow** | 40 MGD (\~27,700 gpm) | 40 MGD (\~27,700 gpm) |
| **Key Internals** | Vertical Mixers (12 per basin) | High-Rate Plate Settlers (Inclined) |

For a basin of this scale (340' length), the primary hydraulic risks are short-circuiting and density currents that bypass the high-rate plate settlers.1

## **2\. Minimum Physics for Retrofit Decisions**

To optimize launder and baffle placement, the model must resolve the spatial distribution of velocity and pressure.

## **Scientific Accuracy vs. Decision Confidence**

* **Scientific Accuracy:** Requires 3D RANS or Large Eddy Simulation (LES) to resolve every turbulent eddy around individual plate settlers.  
* **Decision Confidence:** Requires capturing the global flow path and "dead zones." For rectangular basins where length (340') \>\> depth (11'), a **2D Vertical (2DV)** or **2D Depth-Averaged** model is the minimum physics required for launder/baffle optimization.3

## **Governing Equations (2DV Approach)**

For optimizing vertical baffles or launder submergence, a 2DV (Length-Depth) model is often superior to a plan-view (Length-Width) 2D model because it captures vertical stratification and density "waterfalls" caused by solids loading.5 The momentum equation in the vertical plane (![][image1]) is:

![][image2]  
where ![][image3] accounts for the drag exerted by high-rate plate settlers or perforated baffles.3

## **3\. Python Implementation Roadmap (Practitioner-Driven)**

Python is recommended for its ability to integrate historical SCADA data with numerical solvers.

## **Toolchain Selection**

1. **FiPy (Finite Volume Solver):** Best for custom 2D/3D PDE solutions. It allows the practitioner to define baffles as internal boundary conditions or "porous zones" in the mesh.8  
2. **FEniCS (Finite Element Platform):** More mathematically rigorous than FiPy; ideal for complex basin geometries where unstructured meshes are needed to resolve launder weir shapes.10  
3. **Fluids Library:** Useful for calculating the head loss through the specific launder types (finger vs. wall-mounted) to set the downstream boundary conditions.13

## **Modeling the High-Rate Plate Settlers**

Since your plant uses "Stainless Steel Inclined Plates," the model must account for the laminarizing effect of these plates.

* **Simplification:** Instead of modeling each plate (which would require millions of mesh cells), represent the settler zone as a **Porous Media Zone** with anisotropic permeability (higher resistance perpendicular to the plates, lower parallel to them).8

## **4\. Retrofit Optimization Workflow**

## **Baffle Placement and Type**

* **Objective:** Maximize energy dissipation in the first 17-20% of the basin length.  
* **Test Cases:**  
  * **Solid Baffles:** Use to lengthen the flow path and create serpentine flow (though 180-degree turns should be avoided if they induce high turbulence).  
  * **Perforated Baffles:** Generally more efficient for spreading flow evenly across the 60' width. Research suggests an open area of \~40% is optimal for energy dissipation without creating jetting.  
* **Python Strategy:** Use a "Snapshot POD" (Proper Orthogonal Decomposition) approach to run 50 variations of baffle height and position (![][image4]) and find the configuration that minimizes the Morrill Index (a measure of short-circuiting).

## **Launder Placement (Finger vs. Inboard)**

* **Objective:** Minimize the "up-flow" velocity near the outlet to prevent floc carryover.  
* **Optimization:** Relocating effluent launders inboard (away from the end wall) can reduce effluent solids by up to 60% by capturing water before it hits the end-wall "up-sweep" current.  
* **Metric:** Use the **Residence Time Distribution (RTD)** curve. A "good" retrofit will shift the ![][image5] (time for 10% of tracer to exit) closer to the theoretical hydraulic retention time.3

## **5\. Digital Twin Architecture for 160 MGD Operations**

For real-time support, the high-fidelity Python model should be converted into a Reduced-Order Model (ROM).

1. **Data Assimilation:** Integrate real-time flow (5-40 MGD) and turbidity from SCADA. Use a **PID Assimilator** to adjust the model's internal friction factors based on observed water levels.  
2. **Surrogate Model (POD-RBF):** Use Proper Orthogonal Decomposition combined with Radial Basis Functions (RBF) to create a "lookup table" that provides instantaneous velocity maps for any given influent flow and temperature.  
3. **Operator Dashboard:** Visualize the "Risk of Breakthrough." If a storm event increases flow from 20 to 40 MGD, the dashboard should show the predicted rise of the solids concentration profile relative to the launder elevation.14

## **6\. Staged Implementation for the Practitioner**

* **Stage 1 (Conceptual):** Build a 2D plan-view model in FiPy using your 60'x340' dimensions to identify if flow splits evenly across the 60' width.  
* **Stage 2 (Vertical):** Build a 2DV (Length-Depth) profile of one basin. Insert the high-rate settlers as a porous block and test 3 different baffle locations (![][image6] feet from inlet).  
* **Stage 3 (Optimization):** Link the Python model to an optimization loop (using SciPy.optimize) to move the launder position and minimize the predicted effluent concentration (![][image7]).3

#### **Works cited**

1. Improving secondary settling tanks performance by applying CFD models for design and operation | Water Supply | IWA Publishing, accessed March 24, 2026, [https://iwaponline.com/ws/article/23/6/2313/95496/Improving-secondary-settling-tanks-performance-by](https://iwaponline.com/ws/article/23/6/2313/95496/Improving-secondary-settling-tanks-performance-by)  
2. (PDF) Improving removal efficiency of sedimentation tanks using different inlet and outlet position \- ResearchGate, accessed March 24, 2026, [https://www.researchgate.net/publication/336428170\_Improving\_removal\_efficiency\_of\_sedimentation\_tanks\_using\_different\_inlet\_and\_outlet\_position](https://www.researchgate.net/publication/336428170_Improving_removal_efficiency_of_sedimentation_tanks_using_different_inlet_and_outlet_position)  
3. CFD Modelling for Wastewater Treatment Processes | Request PDF, accessed March 24, 2026, [https://www.researchgate.net/publication/362159074\_CFD\_Modelling\_for\_Wastewater\_Treatment\_Processes](https://www.researchgate.net/publication/362159074_CFD_Modelling_for_Wastewater_Treatment_Processes)  
4. HIGH RATE PRIMARY TREATMENT – EMERGING TECHNOLOGIES \- Access Water, accessed March 24, 2026, [https://www.accesswater.org/publications/proceedings/-289001/high-rate-primary-treatment---emerging-technologies](https://www.accesswater.org/publications/proceedings/-289001/high-rate-primary-treatment---emerging-technologies)  
5. (PDF) Inverse Calculation Model for Optimal Design of Rectangular ..., accessed March 24, 2026, [https://www.researchgate.net/publication/273619082\_Inverse\_Calculation\_Model\_for\_Optimal\_Design\_of\_Rectangular\_Sedimentation\_Tanks](https://www.researchgate.net/publication/273619082_Inverse_Calculation_Model_for_Optimal_Design_of_Rectangular_Sedimentation_Tanks)  
6. Hydraulic Flushing of Sediment in Reservoirs: Best Practices of Numerical Modeling \- MDPI, accessed March 24, 2026, [https://www.mdpi.com/2311-5521/9/2/38](https://www.mdpi.com/2311-5521/9/2/38)  
7. Digital Twins for Wastewater Treatment: A Technical Review \- Engineering, accessed March 24, 2026, [https://www.engineering.org.cn/engi/EN/10.1016/j.eng.2024.04.012](https://www.engineering.org.cn/engi/EN/10.1016/j.eng.2024.04.012)  
8. CFD for wastewater treatment: an overview | Request PDF \- ResearchGate, accessed March 24, 2026, [https://www.researchgate.net/publication/303690543\_CFD\_for\_wastewater\_treatment\_an\_overview](https://www.researchgate.net/publication/303690543_CFD_for_wastewater_treatment_an_overview)  
9. FiPy: A Finite Volume PDE Solver Using Python \- NIST Pages, accessed March 24, 2026, [https://pages.nist.gov/fipy/en/latest/index.html](https://pages.nist.gov/fipy/en/latest/index.html)  
10. A Review of Computational Modeling in Wastewater Treatment Processes | ACS ES\&T Water, accessed March 24, 2026, [https://pubs.acs.org/doi/10.1021/acsestwater.3c00117](https://pubs.acs.org/doi/10.1021/acsestwater.3c00117)  
11. A CFD methodology for the design of sedimentation tanks in potable water treatment: Case study: The influence of a feed flow control baffle | Request PDF \- ResearchGate, accessed March 24, 2026, [https://www.researchgate.net/publication/222688807\_A\_CFD\_methodology\_for\_the\_design\_of\_sedimentation\_tanks\_in\_potable\_water\_treatment\_Case\_study\_The\_influence\_of\_a\_feed\_flow\_control\_baffle](https://www.researchgate.net/publication/222688807_A_CFD_methodology_for_the_design_of_sedimentation_tanks_in_potable_water_treatment_Case_study_The_influence_of_a_feed_flow_control_baffle)  
12. fluids \- PyPI, accessed March 24, 2026, [https://pypi.org/project/fluids/](https://pypi.org/project/fluids/)  
13. State estimation of wastewater treatment plants based on reduced-order model, accessed March 24, 2026, [https://www.researchgate.net/publication/328154902\_State\_estimation\_of\_wastewater\_treatment\_plants\_based\_on\_reduced-order\_model](https://www.researchgate.net/publication/328154902_State_estimation_of_wastewater_treatment_plants_based_on_reduced-order_model)  
14. Digital Twins for Water Treatment Facilities and Water Industry Management, accessed March 24, 2026, [https://www.attinc.com/news/digital-twins-for-water-treatment-industry/](https://www.attinc.com/news/digital-twins-for-water-treatment-industry/)  
15. From Pipe to Pixel: How Digital Twins Are Powering the Future of Smart Water Utilities, accessed March 24, 2026, [https://www.trinnex.io/insights/how-digital-twins-are-powering-the-future-of-smart-water-utilities](https://www.trinnex.io/insights/how-digital-twins-are-powering-the-future-of-smart-water-utilities)  
16. What is Delft3D? Competitors, Complementary Techs & Usage \- Sumble, accessed March 24, 2026, [https://sumble.com/tech/delft3d](https://sumble.com/tech/delft3d)  
17. Development and identification of a reduced-order dynamic model for wastewater treatment plants | Request PDF \- ResearchGate, accessed March 24, 2026, [https://www.researchgate.net/publication/380712346\_Development\_and\_identification\_of\_a\_reduced-order\_dynamic\_model\_for\_wastewater\_treatment\_plants](https://www.researchgate.net/publication/380712346_Development_and_identification_of_a_reduced-order_dynamic_model_for_wastewater_treatment_plants)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAZCAYAAAAmNZ4aAAABYklEQVR4Xu2UvytGURjHv0JRQigDpWwyKqNBmSxk8K4GKSMDk3/ArJTBJAOZJBaR8h8oizIwCZNJfny/nnPv+zjovm5eRfdTn977nHPuc573/LhAQUHBf6OJttOaELeGtrzUBhPq3XPKHr2id/SUboT4ns6jXEylDNMbekDbYJOuvBtBFtxzBz2jXXSOvtB92ujGZDFKx8OzCp6GFdCSjoAtxZSLB+gDrYNNNkSbXf93URE7iCb9jBnYv/wJ9G+1ZZmTauA6fYw7cqBcs8jYIp1cLXmyvxeur4+OuLgSlGuRLrk2Ha6Si9M97aWr9JluwyqepLsoXyn9HsG24jK0xUzQW3pCn2BLfQ67LYNu3FsyJT+my3QM9uIh3YRdhQQVo6ulhBoT0w/L0xNiHSwVeQ27Xh/Q0uhjkdAQxTE68WtxI+y9+IPTiS8+HHlQsq24sdpon7R/3XFHtdHJ//VJC/4er238M8bWT9/vAAAAAElFTkSuQmCC>

[image2]: <data:image/png;base64,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>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAYCAYAAAD6S912AAABNklEQVR4Xu2UPy9EURBHR0RCrGj8TTaRbChEiVYUCo0tVITCp9gtt5JoiIhSgi9AIRpRCJ1G6QsQCYVGRcEZc8l9s3Ffnm33JCdv3/zuTjb3zl2RNhGdOITD2BVq+uz9XVGAHnzDZ3zAdxzAA1yO1uVSwgu89oFY4xvs80GKFfzENR/AOe75YooOPBRruOQy5QyrvphCN/tSrOFRNvpGmw36Yh6T+CTWNPYkXlSUUdyW5qZ6YC2hDRbxVqzhbDbOp+4LAW18hdOunqQbN3wxoDflHvt9kKKC+2Kj41nHD1fT09ZtqIl9dycbi2yKjcULPuIx3uErrorda4+OWQPHfaCL58NnvfwzYjdmLrz/xRaWffG/jAQV/aVTUVYYPZxTnMAx3MWFzIoC6Pb8/NvoOLU87G2a+QKcvi8AuU66LgAAAABJRU5ErkJggg==>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAZCAYAAAAmNZ4aAAABoElEQVR4Xu2UTShEURTHj1DkIyESpShSilKWVuxlwYKSlY0VydbGSik7ZWElC5bISiMlZUUsFSVKoZSVfPz/c++ZOXPNh3nLaX71a+aee959957z3hMpUqRIoVENG2CJH9f5WL6UwkZYHk6k4xA+wFd4Brf9+A0uSHIzueiHl/DZaxmDXTawZP5zpzewFc7DH3gEK01OJmbhsv8/J+5apQM+wRoNsCwziWmRAfgBy8TdbAjWmvlsTMMecddxs6yWMgy/zfgP3LXdaRR083smtiJZ1mUft+BnOJEnbB1vwkOQCngAXxIZHj65+iSyv7dmjqUbMeNcsEU86Tvs8zHt74UmES0LJzfE9YEX8vQTcF+SrxR/Y+JOc+djIVo19rcXtsNrcddMmrz4Ylz8BK7CUXElOYY7sD6ZGl+Ur9aXz8mE3uwePoo7GPNZvRRYZn4sFPbEjkNYzs0wGMA1m2C3uDLHJNrHKIVmuBsGxS3MKvHDof3VB21Kk6IyCE9hWzghLnYFF2ELHBfX7yqbFBU++eluqnTCdXgO1+T/n9oiBcYvpIxKP7FFz2oAAAAASUVORK5CYII=>

[image5]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABYAAAAZCAYAAAA14t7uAAABKklEQVR4Xu2UvyuFYRTHj/zIQDJJFKtBBkpklP9BRoMyUmRQRrNJUrJbpUzKaFAGm/wY7SYDn+/73Mc9jttN930z6H7qMzznPPe853k69zFr828Yw3nsiIkyTOMbnmNvyJViBT9wOybKcozvuBATrbJqqdNoZZ1XWiyjKWh2DcovxSDs4hEuY3fIFQziE46E+Die4KOlE3nyaHbiDh5ag+JTeIZdIa6NPVYfRc+e1ed9FO9x7itbQ6Pm71edqFgmFu7Ha7fWiW9ww8UKNGr6sTrUkTa/p38UHsZnt+7DKzx1sYIZvMBb3LJ0b56WCwtt1oZGxMJD+ODWufCBi/2KWFhvid6UTD7Bmos1ZRLv8NXSuL3gYi03gPs4i5e4bhW+ihOW/jj6SJs/5hNAejYV9xZlcQAAAABJRU5ErkJggg==>

[image6]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAHAAAAAZCAYAAADpG6rZAAAEHUlEQVR4Xu2YS4hURxSGj0QxQVETgw80OIgIEkEkKPhAQVQUNJsoiiFuhCghK0VCAi5FxMdCEMRE1IWIMGDECCKCTRbBxIUuFMTHIuIDFRHFCC40OZ+navrc6tvdt4fp6ZlwP/iZrsfUvVXn1KlTV6SkpKSkpKRkoDMqrUiYGfRh2tACI6U6TiOGqearxqQNLcAY41UTVWOTNs8HYn3GqYYkbYMCJrlHtTptCIxQHVCdCnqm2p3pUQzGeK66p3ql+ks1PdPDFnCd2DOOqG6pfld1uT5FwCiPVb+qjqteqFZJrYEWq26rrgbdUM3J9BjA4HF4OLuiIvkGnKd6o9qZ1GMM2oqyVLVLzBki51X/qk6L7erRqsuqK6qPXT/+950rN4NnXBQbizGBOfKsc1KNICdVj1RTQxlmiDkPbYOGRgbEUEz866R+s9QatRFbxcbxz/gp1MVFjIbqVg11/eKieqM2AgPhFM0MyJips3wqtgt5p1z4ZzyfLZ5X7gT1DBjr04UHyni531GNwDiEz9mu7gexsV+qZrkyIc/D+fS3WJ+i8F7+TJ8kNvb3ro5yRWyeET/nGk6oHqgeill/Y/iNrrl+/U09A8aFq2dAPBWPLUqa/MTdHcfBcI0MiBP0li1iDhd3JLRkQAaIByh/MeaXkl2kRjDBNS2qKL01IG306Q2sAeMeFssWoZkB03doBqGXdfhOzEkWZJuLG5DwuMmVibnEXuI+EyE0tBIe+ppOGPAr1SHVR66urw3o4RrxViyExo1U2IApX6j+kdqQ0in624Dc755K7bnfTgMCY/Pcz125Ir0wIBlcww79TD0D+smkbZQrkp18Eeaq7qvWhjLZJqHtE2mexOD4RcAxFoa/HsZGrH8sV6SgAdltxHpeuFuy9xrqN7hyHhzg8QWKqij1DAi/SHbSEa4FJCGtwJn0p2STEYxTCX9Xij3Lp/rA8UKmWjRhWi82jj+2IK5LnAtjpokYHzXuiiWZPcSQyYuQzBCL8UKYoDor5jGdYorYV4hvpJpQRDDuBbFJRbpC2Z9fcfG5APs7XIRnpA4W5XfcNrH14WsM8D5HxUJfJBrU3/M808Qy++Gujqsaz9on1TOQJJJn/RjqEL+pWxb6vIeJHlP9FsQLXBf7LIUHLOnp2b9UpHYxo/xunKz6Q/Vt0B2xlNzDDiKqXJL8sBrDY55oi2AwPtO9FttJZ1RPJLtGjI+j4ET1zmA+h91U7VftEAvB2yXroBiMDJVn/RzEb6530cg9UEEmFBuIz52+wLcC78nXGBZ1uuRMUCyrZmHzDNgqn4k9b5HURoUIR1E9AwKRj/dlnOVJmwe74LD0Kfph4n/JCtXetLKNEHoHSiY/6GFHHpT8868dcI/si51eEsCAPqlpN4TxkpKSkpKSkjbyHyVyD7NHoiFOAAAAAElFTkSuQmCC>

[image7]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACIAAAAZCAYAAABU+vysAAAB0ElEQVR4Xu2WvytFYRjHH2EQ+ZHfoS6DQhgwkBJlZKKUP0BKsonpDmRhMaMMyiBlUMRwiwVlQgqFwWJQBmUQ32/Pe3h7O/eH2z1K3W99ur3Pc849T8/zfc95RdL6p8oAxaAS5FnxbJBrrQMTC9gFH+ATPIF3EAI5YAWMehcHpQqwDXZAM8g0cf6eg33wClpNPOVqB8/gBXQ5OU8d4E20I4HpVHQMM6Kj8RO98iABj4VFXIAyN2GJhbDgBjeRKtWKFjLhJhyxkCFRwwaidXAGitzEX4rvhwjYkOje+BN5hbAr8bQJ8t1gEloSn52XBbYksULCbiAJcfy0wZiboGjSPYltwhCocYNJiDvuHnQ68W/xdX4HWpx4IzgCw06cfjoGpWZdDfrBoujuiph4HbgF3Wa9LHH82CN6A7fxNVgFV6IPq7eu89QERqw1Hz4HekEbeDTxQXADys066lhs8XvC1vFdMSA/N/tpWrQLnvhwPpQKi46amhf1IL1Isev8VKRMNLd9NKDP6CEeDw7BrMlHRIuuMlyCElE/ujZISgWiW3ASHIA+KzclOgLmT8CaaGfYFY56AYxLDJ/8VoWiBye/P/S6xXHzGu84wbjdybTSSkhfAqVH87jFBA4AAAAASUVORK5CYII=>