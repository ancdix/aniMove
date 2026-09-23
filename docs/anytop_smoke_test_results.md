# AnyTop CUDA / Blender smoke test

Completed 2026-09-22. The generation-to-Blender path works. Motion quality remains mixed; this is a functional smoke test, not acceptance of the raw clips for robot retargeting.

Follow-up: [contact analysis and the first robot baseline](contact_robot_baseline_results.md) are now complete. The later report supersedes the live-scene selection and pending-work status below; this document retains the original smoke-test measurements.

## Outputs

- [Verified Blender file](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/hound_smoke_verified.blend): nine distinct motion scenes, with preserved raw Actions and all 44 named Hound joints.
- [Preview gallery](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/hound_smoke_gallery/index.html): nine videos with controls.
- [Contact sheet](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/hound_smoke_gallery/contact_sheet.jpg): each row is a clip; columns show 0.5, 2.0, 3.5 and 5.0 seconds.
- [Eight-sample run](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/hound_seed100_batch8/run.json), [generation validation](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/hound_seed100_batch8/validation.json), and [Blender validation](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/hound_smoke_verified.validation.json).

Blender's running session contains the nine imported scenes. `RAW_Hound_seed0100_rep03` is selected at frame 41, with playback set to frames 1–120 at 20 fps. The original `Scene` containing Cube, Light and Camera is preserved. Press Space over the viewport to play, or select another `RAW_Hound_...` scene from the scene selector.

The earlier `hound_first.blend` and `hound_smoke.blend` are intermediate inspection files. Use **`hound_smoke_verified.blend`**, which corrects an extra held frame introduced by Blender's duration updater.

## Runtime and reproducibility

Python 3.8.15, Torch 2.4.1+cu121, CUDA runtime 12.1, and an NVIDIA RTX 4090 were verified in the isolated `.venv-anytop` environment. `pip check` passed. The upstream version requirements were retained; resolved packages and Conda package URLs are saved in `configs/anytop-pip-lock.txt` and `configs/anytop-conda-explicit.txt`.

The initial serial package download was stopped to reuse matching existing CUDA wheels. Conda supplied the Python environment, and uv completed installation of the same pinned package requirements. uv's build cache is local because the ShareDrive filesystem cannot create the symlinks needed for build environments. Model weights, skeleton conditioning, reusable wheels, generated outputs, and run logs are on ShareDrive.

Source, Motion, and model revisions match the implementation review. Every run records source and Motion diffs, the exact command, package versions, checkpoint hash, asset-manifest hash, GPU, seed, and elapsed time. No training or full Truebones dataset preprocessing was performed.

## Generation checks

| Check | Result |
| --- | --- |
| First generation | One Hound clip, quadruped checkpoint, seed 100 |
| Batch | Eight repetitions with seed 100, completed in 90.5 seconds |
| Alternate seed | One Hound clip with seed 101 |
| Distinct outputs | Nine; ten clips were generated in total because the first seed-100 clip was repeated in the batch |
| Per-clip layout | Features `(120, 44, 13)`, global XYZ `(120, 44, 3)`, BVH, MP4, metadata |
| Timing | All previews and BVHs contain 120 frames at 20 fps, six seconds |
| Numeric integrity | Finite features/XYZ/BVH transforms; nonstatic motion; named joint order preserved |
| Same-seed check | First clip and batch repetition 0 have byte-identical feature arrays |
| Different-seed check | Seed 101 differs visibly and numerically; XYZ component RMS difference from seed 100 is about 0.2894 source units |
| GPU diffusion | About 1.52 seconds per sample after model loading |
| BVH fitting plus MP4 export | About 9.2–9.8 seconds per sample |

No model download occurs during inference: T5 and AnyTop weights are loaded from the staged ShareDrive assets with Hugging Face offline mode enabled.

## Blender checks and fixes

The importer was first checked on a temporary fixture with moving root translation, nonzero rotation, and multiple terminal joints. It was then tested on the generated clips in a separate background Blender 5.2.2 process.

All nine distinct generated clips passed a comparison of **every joint head at every frame** against positions reconstructed from their BVH files. The maximum difference across all clips was **0.00005174 source units**, below the 0.0001 tolerance. Each Action spans frames 1–120, and the final scene playback range is exactly 1–120 at 20 fps.

This measures faithful **BVH-to-Blender import**, separately from the larger XYZ-to-BVH fitting error below. It does not claim that fitting exactly preserves the diffusion model's proposed positions.

Recorded changes:

1. AnyTop exports BVH frame intervals explicitly at 1/20 second instead of Motion's 1/24-second default.
2. Generation saves XYZ separately from the original denormalized feature arrays and adds metadata/timings.
3. Motion's opt-in `leaf_joints=True` export preserves terminal joint names as ordinary BVH joints, with zero-offset End Sites. Blender can therefore retain every source endpoint as a named bone. A regression test verifies joint names, hierarchy, rotations/positions, and frame timing through a round trip.
4. Blender's importer sets scene duration one frame beyond the last key when starting at frame 1. The wrapper explicitly sets and verifies the inclusive playback range after import.

Coordinates map `(x, y, z)` in the Y-up source to `(x, -z, y)` in Blender, with unit scale 1. These are upstream normalized units, not calibrated meters. The viewport was inspected through the running Blender MCP connection after loading the result.

## Visual assessment and remaining work

The previews are nonblank and show varying articulated Hound poses, body lowering, head movement, and limb movement. Seed 101 visibly changes the sequence. Repetitions 1, 3 and 6 provide useful initial inspection candidates. Several other samples show severe folding or stretched-looking configurations; do not treat every generated clip as a usable gait.

The current inverse-kinematics export fit has mean joint-position errors ranging from **0.105 to 0.238 source units**, and the largest single-frame/joint error is **1.238**. This is material compared with the roughly body-sized coordinate range. The raw XYZ and original feature arrays are retained so later work can distinguish model output quality from fitting artifacts.

Before building robot behavior around these samples:

- Compare raw XYZ against fitted BVH at the worst frames and set explicit fit/contact quality thresholds.
- Identify source end effectors, inspect stance/contact timing, and select coherent clips.
- Add scale calibration, contact correction, and task-space transfer; use raw XYZ where appropriate instead of assuming the fitted bone angles are ground truth.
- Validate more skeletons and a second model family before claiming general ingestion or Milestone A complete.
- Fix and test upstream editing separately before using it for in-betweening. The known editing defects remain unmodified.

The robot rig, retargeter, contact cleanup, rhythm controls, and full 50-clip/two-family milestone have not been built in this step.
