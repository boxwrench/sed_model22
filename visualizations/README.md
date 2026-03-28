# Visualizations

This folder holds repo-visible visualization outputs that are useful for discussion and review.

Current artifact:

- `v0_2_current_blocked_voxel_isometric.svg`: a 2.5D isometric voxel-style rendering of the `v0.2` `current_blocked` longitudinal screening case at the typical flow.
- `v0_2_design_spec_voxel_isometric.svg`: the matching `v0.2` design-spec view for side-by-side review.
- `v0_2_design_vs_current_voxel_comparison.html`: side-by-side comparison page for the `v0.2` design and current blocked-wall cases.
- `v0_1_verification_empty_voxel_isometric.svg`: 2.5D isometric voxel-style rendering of the original empty-basin verification case.
- `v0_1_baseline_baffle_voxel_isometric.svg`: 2.5D isometric voxel-style rendering of the original baseline `v0.1` baffle test case.
- `v0_1_test_pair_voxel_comparison.html`: side-by-side comparison page for the original `v0.1` test pair.
- `templates/`: small reusable media templates for repeatable still and preview generation.

Important interpretation notes:

- this is a presentation of the current `2D length x depth` screening field, extruded across basin width for readability
- it is not a full `3D` solve
- the water voxels use run-normalized relative speed bands, not field-credible absolute velocities
- the blocked transition wall is drawn as a solid panel for readability even though the current solver still treats it as a loss interface

Animation setup notes:

- Still-image rendering does not require `ffmpeg`.
- Preview-video assembly is optional and looks for `ffmpeg` in this order:
  - `SED_MODEL22_FFMPEG`
  - `ffmpeg` on `PATH`
  - `tools/ffmpeg/bin/ffmpeg.exe` inside this repo
  - a known local Pinokio install path
  - `imageio_ffmpeg` if installed
- The practical user-download path for this repo is `tools/ffmpeg/bin/ffmpeg.exe`.
- The current preview path rasterizes SVG scenes before stitching. If `cairosvg` is unavailable, the pipeline still writes the stills, cards, and scene manifest but skips the `.mp4`.
- If `ffmpeg` is not found, the media pipeline should still render stills, comparison pages, cards, and manifests; it will just skip the `.mp4` preview.
