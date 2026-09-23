# Collision-checked walking animation

Completed 2026-09-22. The new `WALK_Collision_Checked` scene contains an eight-second forward walk with alternating swing feet, fixed stance points, and collision-aware bend directions. The original comparison scene is retained as a reference; use the new walking scene for the corrected result.

- [Walking video — 1280×720, 30 fps](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/robot_walk_v2/walking.mp4)
- [Saved walking Blender file](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/robot_walk_v2/robot_walk.blend)
- [Rendered walking frame](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/robot_walk_v2/walking.png)
- [Saved-file collision and playback validation](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/robot_walk_v2/walk_validation.json)
- [Motion parameters and provenance](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/robot_walk_v2/retarget.json)
- [32-clip AnyTop walking search](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/robot_walk_v2/walking_source_search.json)

## What drives the walk

The foot placements are **procedural four-beat walking**, with bounded AnyTop torso/head detail. This is not presented as a diffusion-generated walking gait.

An additional 24 Hound clips and eight Horse clips were generated with the existing quadruped checkpoint. None passed the direct-walk screen: at least one body length of travel, sufficiently raised pelvis, at least two stance episodes on every limb, and stance fractions between 0.25 and 0.90. The one Hound clip that traveled 1.23 body lengths was collapsed and lacked usable repeated support phases. This is a result for these samples and thresholds, not a claim that AnyTop cannot generate walking.

The controller therefore specifies the locomotion directly, as contemplated by the plan's procedural motion layer:

- 240 frames at 30 fps, eight seconds, five 1.6-second gait cycles.
- Forward speed 0.38 robot units/second; 3.027 units of displacement between the first and last keyed frames.
- Each foot is planted for 75% of its cycle. Exactly three feet are classified as supporting while one swings.
- Swing height 0.16 units. Horizontal quintic easing and a smooth lift curve have continuous position, velocity, and acceleration at landing/liftoff.
- Feet stay in separate left/right lanes. Hip attachments move from ±0.24 to ±0.35 units; small mounting struts connect them to the existing torso.
- AnyTop Hound seed 100, repetition 1 supplies small torso-height, yaw/pitch, and head variations, resampled over the eight seconds. It does not supply the step timing or travel speed.

The tracking camera follows the robot; the scrolling ground grid shows its forward travel. The file is a forward-travelling clip, so replay resets its world position. It is not a seamless root-motion loop.

## Collision handling

`scripts/collision.py` adds exact segment-to-segment and segment-to-box distances. Limb capsules use a conservative radius of **0.075**, enclosing the 0.043-radius beams and 0.075-radius joint balls. Oriented boxes enclose the torso/top panel and head/visor. The required separation margin is **0.015 robot units**.

The cleanup chooses outward bend planes while preserving core positions, segment lengths, and foot targets. If necessary, it searches alternative pole directions against the other limbs and body, with penalties for abrupt changes. Candidate motions fail acceptance if the required margin is still violated.

Adjacent segments in the same mechanical joint and the intended proximal hip mounting region are excluded. This permits their designed physical connections; unrelated limbs and the remaining torso/head interactions are checked. The solver's control comparison uses deliberately naive inward poles on the same walking targets, rather than claiming that comparison is an original AnyTop walk.

The HEAD rest-bone roll is also aligned with its animated frame so the head mesh and collider agree. The new rig retains baked FK, editable two-bone IK targets/poles, the `ik_fk` property, and separate source/control data.

## Verification

The saved `.blend` was reopened for independent checks. Evaluated Blender poses were checked at 30 fps in both FK and IK modes, then the default baked motion was sampled at **120 Hz**, including the interpolation between keys.

| Check | Result |
| --- | ---: |
| Dense sampled poses | 957 |
| Detected inter-limb/body intersections | 0 |
| Clearance-margin violations | 0 |
| Minimum conservative clearance, all checked pairs | 0.10016 units |
| Minimum inter-limb clearance | 0.55000 units |
| Minimum limb-to-torso clearance | 0.15234 units |
| Maximum evaluated joint-position error | 1.26e-6 units |
| Maximum evaluated segment-length error | 8.23e-7 units |
| Mean stance slip, baked FK | 7.39e-6 units/s |
| Mean stance slip, editable IK | 1.27e-5 units/s |
| Lowest evaluated visible mesh vertex | −2.23e-5 units, within the 1e-4 floor tolerance |
| Live IK target edit error | 3.96e-7 units |

Nine regression tests passed, including crossing/parallel/degenerate segment cases, box distances, collision cleanup without changing foot targets, gait support count, fixed stance points, and step-boundary continuity. The preview was verified as 240 frames at 30 fps, exactly 8.000 seconds. Multiple rendered poses and the live appended viewport were inspected.

These checks establish kinematic collision clearance for the saved animation. They are not a dynamics/force-balance simulation. Arbitrary later IK edits require rerunning collision checks; the rig does not apply a live collision constraint during manual editing.

## Blender use

`WALK_Collision_Checked` has been appended to the running session. All eleven previous scenes, their Actions, and the original Camera/Cube/Light remain available. Press **Space** to play/pause.

The selected rig is `CLEAN_Controlled_Walk_AnyTop_Hound100_01`. Its `ik_fk` custom property is **0** for the baked Action and **1** for editable IK targets/poles. Enable viewport Extras/Bones to expose the controls, or select them in the Outliner. Green markers show stance; their absence shows swing.

All new generation, analysis, robot and preview artifacts are on ShareDrive. No additional model weights or training dataset were downloaded. `robot_walk_v1` was an intermediate numerical candidate; use **`robot_walk_v2`**.

## Reproduce

Run from the repository root and choose a new destination:

```bash
WALK_DATA=/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated
.venv-anytop/bin/python scripts/walking_motion.py \
  --source "$WALK_DATA/hound_seed100_batch8/Hound_rep_1_#0.json" \
  --output "$WALK_DATA/robot-walk-new"
/snap/blender/7803/blender --background --factory-startup --python-exit-code 1 \
  --python scripts/build_walking_blender.py -- "$WALK_DATA/robot-walk-new"
/snap/blender/7803/blender --background --factory-startup --python-exit-code 1 \
  --python scripts/verify_walking_blender.py -- "$WALK_DATA/robot-walk-new"
/snap/blender/7803/blender --background --factory-startup --python-exit-code 1 \
  --python scripts/render_walking_preview.py -- "$WALK_DATA/robot-walk-new"
.venv-anytop/bin/python -m unittest discover -s tests -v
```

The next useful extension is a speed/turn controller with the same stance and collision checks. Direct AnyTop gait transfer can be revisited with a better qualifying source; the newly generated source clips and screening reasons are preserved.
