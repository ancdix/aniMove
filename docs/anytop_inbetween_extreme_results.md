# In-betweening and four-support to two-support stress test

Two new Blender scenes compare controlled AnyTop variation and an authored upright goal. The natural variations work as a motion-editing prototype. The upright experiment reaches the requested pose after substantial cleanup, but raw transition quality and physical balance remain unresolved.

- [Four variations video](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/inbetween_rearup_v2/variations.mp4)
- [Four-to-two-support video](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/inbetween_rearup_v2/extreme.mp4)
- [Blender file](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/inbetween_rearup_v2/inbetween_experiments.blend)
- [Saved-animation validation](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/inbetween_rearup_v2/saved_animation_validation.json)

## Fixed context and generated motion

All clips have 120 samples at 20 fps. The editor preserves frames 1–30 and 91–120 in the model's normalized feature representation. AnyTop generates frames 31–90. The source is the previously inspected Hound seed-100 sample 01, using the quadruped checkpoint.

The first experiment uses that source's original beginning and ending. Four selected seeds, 3101, 3102, 3103 and 3105, are transferred onto the same robot beside the original. There is no smoothing or contact pinning in these four robot transfers. Fixed-length IK and outward knees adapt the robot while preserving source foot targets and body motion.

Six natural candidates were generated. Seed 3100 was rejected for a large motion spike, unreachable targets and collisions. Replacement 3104 was rejected for a head/limb intersection; 3105 passed. This is screening of a small sample, not a general model success-rate estimate.

For all ten samples across both experiments, fixed normalized feature error was exactly zero. Denormalized feature differences were floating-point noise (less than 1e-6). However, fixed suffix features do **not** fix suffix world-space position: generated root velocities accumulate through the middle. Both the original raw arrays and the resulting world offsets are retained in each run manifest. The edited suffix has the same relative pose, but can be translated horizontally.

## The extreme guide is authored

The extreme test starts with the original motion and ends in an authored rearing pose. The source torso was rotated toward 70 degrees of elevation, rear leg targets were adjusted with FABRIK, and the full source skeleton was fitted and encoded using upstream feature routines. Fitting produces approximately **74.9 degrees** of torso elevation. This static pose supplies the final 30-frame window. Its mean source fitting error is approximately 0.131 source units and is recorded in `run.json`.

The unknown middle is masked out during diffusion. It is not a procedural interpolated rise. Neither the original guide nor the final pose should be described as an unconditionally generated upright motion.

Four extreme candidates were generated. None passed the first robot-transfer attempt with the requested contact corrections. The best candidate, `rear_up_seed3101`, approaches roughly 54 degrees before the fixed ending but has a visible snap into the final pose. Its largest raw boundary step among the monitored body/end-effector points is about 0.590 robot design units in one frame.

## Explicit robot cleanup for the extreme test

The right-hand robot uses the same limb lengths and dimensions as the previous rig, with:

1. Three binomial smoothing passes on XYZ (seven-frame support).
2. Rear foot anchors throughout; four foot anchors initially, with front feet released over frames 31–43.
3. A gradual horizontal body-center shift toward the rear support midpoint; the front targets follow this shift to retain their relation to the torso.
4. Root reach correction when needed and collision-aware knee bends.
5. Continuous IK playback to keep planted feet fixed between animation keys.

The largest body correction relative to the smoothed source is **0.795 design units**, against a 0.9-unit robot body length. This is a substantial retargeting adjustment, not a small polish. Raw generated motion is always displayed alongside it. Raw and corrected arrays are stored separately; initial failed transfers are also retained.

After cleanup the robot reaches all targets, the torso ends at 74.9 degrees and both front end effectors are well above the ground. The body-center projection ends at the midpoint between the two rear supports. This is only a **geometric support proxy**: no mass distribution, center-of-mass dynamics, torques, friction or balance controller has been simulated. It does not establish physical balance.

## Blender verification

The saved file was reopened and all six robots (original, four variations, one extreme test) were evaluated against independent numerical targets in both FK and IK modes for all 120 frames. Endpoint/joint errors remain below 1e-4 design units.

Each robot was also checked at 477 poses, including quarter-frame samples (80 Hz):

- No conservative limb/torso/head proxy intersections or 0.015-unit clearance-margin violations.
- Extreme minimum clearance approximately 0.03138 units.
- The initial FK interpolation showed 0.00434-unit rear-foot drift and 0.00244-unit floor penetration between keys. FK remains available for comparison; **the saved extreme scene defaults to IK**.
- Extreme IK rear-foot drift is approximately 1.05e-6 units across dense samples.
- Extreme minimum evaluated mesh height is approximately +1.01e-6 units above the floor.
- Original raw skeleton display was verified against its saved XYZ arrays.

The proxy excludes intended hip mounts and adjacent segments of the same limb. Contact and collision results apply to this saved animation, not arbitrary edits. There is no loop closure: replay resets from the upright ending to the four-support beginning.

## Editing repair and reproduction

`patches/anytop-editing.patch` replaces the all-zero input placeholder with normalized supplied features, validates input shape/finiteness, repairs preview-grid sizing, and exports reusable numeric features, separate XYZ and 20-fps BVH. `setup_anytop.sh` applies this patch separately from the generation patch.

The GPU experiment uses the actual repaired `prepare_inpainting_inputs` and upstream diffusion sampler through `scripts/run_inbetween_experiment.py`. Twelve repository tests pass, including three new tests of the actual input-preparation function. The stock editing CLI's complete multi-video export is not the end-to-end path exercised here.

```bash
.venv-anytop/bin/python scripts/run_inbetween_experiment.py --name inbetween_rearup_NEW
.venv-anytop/bin/python scripts/prepare_inbetween_robots.py \
  /media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/inbetween_rearup_NEW
```

The run script accepts `--kinds natural rear_up` and `--seeds ...`. Use new output names; existing raw experiments are never overwritten. The robot preparation script accepts `--only ...` and `--robot-prefix ...` for separate retargeting experiments. Its current extreme path includes the disclosed smoothing and upper-body translation correction.

`build_inbetween_blender.py` is an experiment-specific assembly of the selected runs, followed by `verify_inbetween_blender.py`. `polish_inbetween_blender.py` records the presentation update and default continuous-IK mode. The final source snapshots preserve the exact scripts and patches. Assets, guides, outputs, previews and logs remain on ShareDrive. `inbetween_rearup_v1` contains only guide preparation from an initial startup failure; the completed primary generation is `inbetween_rearup_v2`, with replacement natural candidates in `inbetween_extra_v1`.

## What to do next

Use shorter intermediate pose windows or compatible rearing reference motion to reduce the extreme transition's boundary snap. Compare that against this raw result before increasing cleanup. A subsequent balance claim requires at least a credible mass/center-of-mass model, followed by dynamics if physical execution is intended. The original plan's biped-source transfer and broader motion screening remain outstanding.
