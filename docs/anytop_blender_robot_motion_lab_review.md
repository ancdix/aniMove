# AnyTop motion lab: implementation review

Reviewed 2026-09-22 against the complete 25-section plan, the running machine, and pinned upstream source. The original plan is preserved.

The proposed architecture is sound: separate inference from Blender, preserve source motion, transfer trajectories and contact timing through IK, and add rhythm and unusual movement only after the baseline works. However, the released code needs several corrections before its output can serve as a reliable interchange format. This review and asset preparation do **not** constitute a completed inference smoke test.

## Verified local readiness

- GPU: NVIDIA RTX 4090, 24,564 MiB, driver 580.173.02. Queried on the host; the restricted shell cannot see the driver correctly.
- Blender: 5.2.2 LTS. MCP scene inspection was successfully tested earlier in this task. A separate background Blender check found `io_anim_bvh` and the `bpy.ops.import_anim.bvh` operator. No custom BVH parser is needed initially.
- Conda is installed, but no `anytop` environment exists yet. Existing environments were not modified.
- Shared storage: `/media/ipsedesktop/ShareDrive1`, about 980 GiB free at inspection. It is writable on the host and formatted as exFAT. The restricted shell presents it as read-only.
- The project currently contains the plan, rather than an implemented motion pipeline. No robot rig or generated motion has been created by this review.

## Required corrections before implementation

### 1. Define the actual motion data contract

The plan and upstream README describe generated NPY files as XYZ positions. The generator actually saves **denormalized motion features shaped `(frames, joints, 13)`**. It separately reconstructs global XYZ for visualization and BVH fitting, but does not save that XYZ array. See [generation and serialization](https://github.com/Anytop2025/Anytop/blob/e780d1575ca0121f29bb53821b309cf564156a95/sample/generate.py#L82-L105).

Preserve the original feature array for editing. Save reconstructed XYZ separately and label both formats explicitly. The generated features already have mean/std applied; do not denormalize them a second time. Editing inputs require the corresponding normalization before feeding the diffusion model.

Specify in each manifest: schema version, representation, array shape, joint order and parent indices, source units, up/forward axes, root conventions, frame count, FPS, and source-to-Blender transform. Use names such as `features.npy` and `xyz.npy`, rather than treating every NPY as interchangeable.

The editing output introduces another format: a pickled dictionary containing `motion`, `joint2color`, and `sample_path`. It cannot be passed straight back through the editor's plain `np.load(sample)` input path. Add an explicit adapter before repeated edits.

### 2. Fix a 20 fps versus 24 fps export mismatch

AnyTop defines [FPS = 20](https://github.com/Anytop2025/Anytop/blob/e780d1575ca0121f29bb53821b309cf564156a95/data_loaders/truebones/truebones_utils/param_utils.py#L54-L56). Both generation and editing call `BVH.save` without a frame interval. The pinned Motion library [defaults to 1/24 second](https://github.com/inbar-2344/Motion/blob/ac236251f90e5ca37c444c53ad383fc85de6d833/BVH.py#L235).

Consequently, a consumer honoring that header would play the BVH 20% faster than the 20 fps preview. Pass `frametime=1.0 / fps` at both export sites, then verify the header and playback duration. The plan's example `fps: 30` must not become a pipeline default.

The generator really does use `--motion_length`: frames are calculated as `int(motion_length * fps)`. The default six seconds gives 120 frames and matches all five downloaded checkpoint configurations. Keep that baseline; longer durations remain a quality and memory experiment, not a guaranteed capability. The CLI's text-to-motion wording is inherited help text, not the implementation's restriction.

### 3. Repair editing before relying on diffusion transitions

Update: the input repair has now been implemented and exercised with ten GPU in-betweening samples; see [editing experiment results](anytop_inbetween_extreme_results.md). The findings below describe the original pinned upstream code.

In [prepare_inpainting_inputs](https://github.com/Anytop2025/Anytop/blob/e780d1575ca0121f29bb53821b309cf564156a95/sample/edit.py#L174-L205), each supplied motion contributes its length, but the motion passed to the collator is an all-zero array. That array becomes `inpainted_motion`, so the supposedly preserved boundary frames do not contain the source motion.

An isolated execution of the actual upstream function, with embedding/mask/collation dependencies stubbed, confirmed that a nonzero input with sum 1820 yielded a zero-sum array for the collator. This verifies the input preparation defect; it is not an end-to-end editing test. Replace the placeholder with correctly normalized source features and test preservation of unmasked frames numerically.

The preview grid also uses `(1 + batch_size // 5, batch_size % 5)` and then indexes columns with `i % 5`. This creates zero columns for five or ten inputs and out-of-bounds columns for six. Fix grid sizing and handle unused cells before testing multi-clip editing.

Two independent clips are not automatically a valid in-betweening input. First align their root position, heading, skeleton, normalization, frame rate, and feature representation, then construct one boundary-conditioned sequence. Role swaps between different physical limbs also need a procedural task-space transition; the editor does not solve that robot constraint problem.

### 4. Include the hidden T5 dependency and pin all sources

All five checkpoint `args.json` files specify `t5-base`. Generation loads a tokenizer and T5 encoder at runtime even though conditioning metadata includes skeleton information. Those assets must be available in addition to the approximately 9.2 MB motion checkpoint. Retain the adjacent `args.json`; the argument loader requires it.

Pin these inspected revisions:

| Source | Revision |
| --- | --- |
| AnyTop code | `e780d1575ca0121f29bb53821b309cf564156a95` |
| Motion library | `ac236251f90e5ca37c444c53ad383fc85de6d833` |
| Inbar2344/AnyTop assets | `a1efdbb4c1495efe6a1e54d19c2824d1a957ce36` |
| google-t5/t5-base | `a9723ea7f1b39c1eae772870f3b547bf6ef7e6c1` |

Use an isolated environment based on upstream Python 3.8 / Torch 2.4.1 first. Remove the author-specific `prefix` from `environment.yaml`; record any dependency changes needed to solve it. Do not install the research environment into Blender or change the already working MCP runtime simply to match an example configuration.

T5 currently accepts a fixed model-name list, so passing an arbitrary local path as `--t5_name` is not sufficient. A symlink named `t5-base` in the local AnyTop working directory can resolve to the downloaded model directory without changing the logical model name. Alternatively, add a separate local-model-path option while retaining `t5-base` for architecture selection.

### 5. Use ShareDrive for assets, and the Linux filesystem for code/environments

Prepared asset destination:

```text
/media/ipsedesktop/ShareDrive1/ModelData/aniMove/
  AnyTop/
    checkpoints/<model-family>/args.json
    checkpoints/<model-family>/model*.pt
    dataset/truebones/zoo/truebones_processed/cond.npy
    dataset/truebones/zoo/truebones_processed/Truebones_skeletons.txt
  t5-base/
    config.json
    model.safetensors
    spiece.model
    tokenizer.json
  asset_manifest.json
```

Download completed: **17 files, 944,275,562 bytes (about 944 MB / 901 MiB)**. The manifest records pinned URLs, byte sizes, SHA-256 digests, and whether an upstream SHA-256 was checked. All published LFS SHA-256 values matched. Optimizer states are unnecessary for inference and are excluded.

exFAT does not provide the ordinary Unix symlinks expected by upstream's downloader. Keep the checkout, environment, and symlink destinations on the Linux filesystem; point local `save`, `dataset`, and `t5-base` links at ShareDrive. Keep large future outputs and caches on ShareDrive as well. Do not blindly run the upstream downloader with its default home-directory cache after staging these files.

The released conditioning file contains **70 skeletons**. Hound, Ostrich, Chicken, and Bat were loaded and inspected; their joint counts are 44, 53, 40, and 47, with 13-feature statistics and finite mean/std arrays. The generator constructs conditions directly from this file rather than opening the full training motion dataset.

The [upstream project](https://github.com/Anytop2025/Anytop#2-download-and-preprocess-truebones-dataset) withholds the processed training dataset pending licensing clarification. It is not a prerequisite for the built-in pretrained generation path inspected here. No full Truebones dataset was acquired. Training or large-scale dataset preprocessing would be a separate dependency decision.

## Design additions for the robot pipeline

- **Source semantics:** the released biped family includes birds/dinosaurs; do not equate it with a human walk library. Verify source names against conditioning data. Hound and Ostrich are concrete first examples, not behavior prompts such as “walk.”
- **Transfer representation:** distinguish body-relative swing trajectories from world/surface-relative stance anchors. Recomputing pinned feet from a moving root every frame would reintroduce sliding. Define limb socket offsets and per-limb reach scaling, not only one global `root_scale`.
- **Root and orientation:** transfer full orientation with quaternion continuity; define twist distribution and pole-vector fallback at near-straight poses. Record unreachable targets rather than silently shortening their trajectories.
- **Contacts:** estimate an initial floor and use separate local tolerances for each end effector. Express speed, acceleration and jerk in time-based units using FPS, and normalize geometric thresholds by body scale. Otherwise scores change merely because frame rate or scale changes.
- **Quality measurement:** detect contacts from source motion and retain those labels while scoring cleaned output. Re-detecting contacts solely on the cleaned target can hide failure by labelling a slipping foot as airborne. Report distributions/worst frames as well as means.
- **Rhythm and loops:** enforce monotonic time maps with bounded speed changes. Resample rotations appropriately, carry contact-event labels through the warp, and rerun contact IK afterward. Test pose, velocity, heading, and contact continuity at loop seams.
- **Mechanical feasibility:** four three-segment limbs with reachable targets do not guarantee a valid whole-body pose. Add self-collision clearance and support diagnostics. Wall/ceiling movement also needs an explicit adhesion assumption; IK alone does not establish physical feasibility.
- **Blender data handling:** prototype against Blender 5.2's current Action/slot APIs. Preserve raw Actions and meshes, use deterministic names/identifiers, and save new checkpoint files. Do not run upstream's visualization script in the live scene: it calls `read_homefile(use_empty=True)`.
- **Reproducibility:** record code and asset revisions, environment lock, Motion version, exact command, output hashes, timing, and coordinate conversions. Repeated runs with the same seed should be checked before assuming determinism across hardware or package versions.

## Recommended execution gates

1. Build the isolated AnyTop environment and wire it to the staged ShareDrive assets. Verify CUDA inside that environment, model loading, T5 loading, and imports. Apply the frame-time export fix with a recorded patch.
2. Generate one six-second Hound clip. Confirm all three artifacts exist, their representations are understood, and MP4/BVH duration agrees. Measure inference and the 150-iteration BVH-fitting/export stage separately before calling generation cheap.
3. Generate the required eight samples and a second-seed comparison. Inspect previews and BVHs; keep seed and checkpoint metadata. Only then expand to two model families and the 50-clip milestone.
4. Implement a reusable BVH importer and test ten clips with explicit axes, scale, duration, and root checks. Build the four-limb rig after that gate passes.
5. Establish a small retarget/contact-cleanup benchmark before loops or rhythm. Repair and test editing before using it for transition synthesis. Keep custom robot conditioning last, as the plan proposes.

The seven-day schedule is a useful ordering, not an evidence-based estimate. Environment compatibility, source-format corrections, and retargeting/contact behavior should determine when each gate is complete.

## Review scope and verification limits

Completed: full plan read; source inspection at pinned revisions; host GPU/storage checks; background Blender BVH-importer discovery; skeleton conditioning inspection; isolated reproduction of editing input loss and preview-grid index failures; inference-asset preparation and integrity checks recorded in the asset manifest.

Not yet completed: AnyTop environment installation, CUDA inference, visual judgment of generated motion, BVH round-trip/import acceptance tests, robot rig construction, retargeting, or upstream bug fixes. The original plan and open Blender scene were not altered.
