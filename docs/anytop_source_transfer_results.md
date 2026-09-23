# Genuine AnyTop source-to-robot comparison

The `ANYTOP_Source_to_Robot` scene displays the original generated Hound XYZ skeleton beside a four-limb robot driven by that same sample. This is a six-second standing weight shift, not a walking demonstration. Matching foot colors identify corresponding endpoints.

[Video](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/anytop_transfer_v1/comparison.mp4) · [Blender file](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/anytop_transfer_v1/anytop_transfer.blend) · [Validation](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/anytop_transfer_v1/transfer_validation.json)

## What comes from AnyTop

The existing quadruped checkpoint generated `Hound_rep_1_#0` in the seed-100 batch. Its original `.xyz.npy` supplies all 120 poses at 20 fps. The source file hash is recorded in `retarget.json`; generation command, checkpoint hash, source revisions and environment remain in `hound_seed100_batch8/run.json`.

Both figures use the same fixed coordinate conversion `(x,y,z) -> (x,-z,y)`, origin and scale. The left figure displays all 44 original joint positions directly, avoiding the approximation introduced by fitting XYZ to BVH. The robot uses:

| Robot channel | Source |
|---|---|
| Body position | Midpoint of pelvis and neck |
| Body heading and pitch | Pelvis-to-neck axis; roll resolved against world up |
| Head direction | Head-to-nose direction |
| Four end effectors | Left/right front finger tips and rear toe tips |
| Frame timing | Original 120 samples at 20 fps |

There is no smoothing, procedural foot cycle, straight-line root replacement, contact pinning, lateral foot offset, root correction, or temporal resampling. The source's foot drift and height variations remain visible. The robot does not reproduce the source's tail, facial joints, articulated spine or all intermediate limb joints.

## What retargeting changes

The robot uses fixed 0.7-unit upper/lower segments and hips at +/-0.35 units laterally. IK finds knees/elbows that reach the source endpoints. Outward bend planes avoid robot self-intersections. This changes intermediate joint poses substantially: the largest knee displacement relative to the initial source-bend solve is 1.133 robot design units. It does not change the endpoint or body trajectories.

`motion.npz` retains both `retarget_*` (initial source-bend solve) and `clean_*` (outward collision-cleaned solve), alongside original transformed `source_xyz`. The manifest separately reports both collision audits: the initial solve has 622 intersecting proxy pair/frame checks; the cleaned solve has zero. These counts are not counts of distinct frames.

## Verification

The saved Blender file was reopened and compared directly against the original hashed XYZ file over every frame, in both baked FK and editable IK modes:

- Maximum source visualization position error: 9.78e-8 units.
- Maximum robot foot error: 4.52e-7 FK, 9.09e-7 IK units.
- Maximum body position error: 6.39e-8 units.
- Maximum head direction vector error: 5.38e-7.
- 477 evaluated FK poses at 80 Hz, including subframes: zero proxy intersections or clearance-margin violations; minimum clearance 0.0976 units.
- Collision model: conservative 0.075-radius limb capsules and oriented torso/head boxes. Intended hip mounts and adjacent segments of each limb are excluded.

The low display plinth is below the raw feet. It is not evidence of correct ground contact, physical balance, or a dynamics simulation. The clip is not a seamless loop. Source bone lengths vary because this view preserves generated XYZ rather than enforcing a fitted skeleton.

## Reproduction

Use a fresh output directory on ShareDrive; builders refuse to overwrite the existing result.

```bash
.venv-anytop/bin/python scripts/prepare_anytop_transfer.py \
  /media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/contact_baseline_v1/analysis.json \
  --output /media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/anytop_transfer_NEW

/snap/blender/7803/blender --background --factory-startup --python-exit-code 1 \
  --python scripts/build_anytop_transfer_blender.py -- \
  /media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/anytop_transfer_NEW

/snap/blender/7803/blender --background --factory-startup --python-exit-code 1 \
  --python scripts/verify_anytop_transfer_blender.py -- \
  /media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/anytop_transfer_NEW
```

The builder saves the Blender file, still and PNG sequence. Encode the sequence with ffmpeg at 20 fps to create the comparison MP4. The robot's `ik_fk` property switches between baked action (0) and editable targets (1). Collision verification applies to the saved motion, not arbitrary subsequent edits.

This establishes a visible, numerically verified AnyTop-to-robot transfer for one quadruped sample. Biped coverage, reliable walking/running/jumping samples, broader screening and motion editing remain outstanding plan work.
