# Visualization Methods Review Notes

These notes capture the repo-facing takeaway from the two new visualization research memos:

- [visualization_methods_for_sed_model22_decision_memo.docx](/C:/Github/sed_model22/docs/research/source-notes/visualization_methods_for_sed_model22_decision_memo.docx)
- [visualization_methods_for_sed_model22_candidate_methods_memo.md](/C:/Github/sed_model22/docs/research/source-notes/visualization_methods_for_sed_model22_candidate_methods_memo.md)

## What The Two Memos Agree On

- particle pathlines / particle trails are the best first animated method for `sed_model22`
- the strongest reason is not style, it is communication: they show where the water wants to go in a way operators and non-specialists can read quickly
- this method is also the best near-term fit for the current repo constraints:
  - steady screening fields
  - low-resolution `854 x 480` preview output
  - CPU-first Python implementation
  - explicit honesty about screening-model limits
- static streamline output still belongs in the stack because it matches standard engineering communication and works well for report stills
- voxel-heavy flow rendering should not drive the next implementation step
- voxel views are better treated as geometry context, especially for future `3D` or serpentine over-under path explanation

## Where The Memos Differ

- the markdown memo argues for dye-pulse scalar advection as the next method after particles
- the Word memo is more conservative and keeps streamline and arrow support ahead of dye because dye animation can imply stronger transient-transport credibility than the current model supports

This is a real difference in emphasis, not a contradiction about the first step.

## Practical Repo Reading

The strongest shared signal is:

1. build particle pathlines first
2. keep or strengthen static streamline/report-still support
3. treat dye-pulse as a later method only if it is framed clearly as synthetic tracer or steady-field proxy transport
4. defer voxel-driven flow storytelling until the geometry and fidelity justify it

## Recommended Repo Decision

For the current repo milestone, the safest practical decision is:

- first animated method: deterministic particle pathlines with fading trails
- report/still companion: static streamlines with modest density and clear geometry masking
- diagnostic companion: sparse arrow/glyph overlays only for technical review or debugging
- defer dye-pulse until the team is comfortable with the labeling and honesty rules for transport-like outputs

This keeps the repo aligned with the current `v0.2` product boundary:

- directional comparison signal matters more than cinematic richness
- practical clarity matters more than visual novelty
- the output should not imply full transient CFD or validated transport prediction

## Implementation Notes Worth Preserving

- do not add stochastic jitter to particles
- keep particle counts modest so the result does not read like high-fidelity CFD or PIV data
- keep honesty text explicit in preview output
- use streamline stills for engineering-facing reports
- reserve voxel cutaways for geometry explanation, especially once explicit serpentine bypass representation exists

## Suggested Next Visualization Step

If the repo returns to visualization work soon, the most defensible sequence is:

1. add deterministic particle-pathline preview output
2. add or refine static streamline stills for reports
3. revisit dye-pulse only after agreeing on proxy-language and use limits

