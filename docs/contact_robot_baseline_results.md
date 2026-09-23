# Contact analysis and first robot baseline

Completed 2026-09-22. The nine distinct Hound outputs have been screened, and the strongest candidate has been transferred to a four-limb robot with separate before/after contact Actions. This is a supported weight-shift prototype, not a validated walking gait or completed universal retargeter.

Follow-up: the [collision-checked walking result](walking_collision_results.md) is now available. The original comparison below retains the limb intersections discovered during review; use `WALK_Collision_Checked` for the new walking animation.

## Open the result

- [Robot comparison Blender file](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/robot_baseline_v1/robot_contact_comparison.blend)
- [Six-second comparison video](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/robot_baseline_v1/comparison.mp4)
- [Rendered comparison](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/robot_baseline_v1/comparison.png)
- [Contact/quality plots](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/robot_baseline_v1/contact_report.png)
- [Raw XYZ versus BVH fitting diagnostics](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/robot_baseline_v1/source_fit_diagnostics.png)
- [All nine clip scores and intervals](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/contact_baseline_v1/analysis.json)
- [Retarget parameters and metrics](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/robot_baseline_v1/retarget.json)
- [Saved-file playback and IK edit verification](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/robot_baseline_v1/reload_validation.json)

The running Blender session now has `LAB_Contact_Comparison` selected at frame 70. The ten existing scenes, original source Actions, and the original scene's Camera/Cube/Light were preserved. The new comparison was appended through the working MCP connection; the existing open file was not overwritten. The comparison is also saved independently at the path above.

Press **Space** over the viewport to play frames 1–120 at 20 fps. Orange is the transferred motion; blue is contact-cleaned. Green floor markers indicate inferred contact. This sequence is not a seamless loop.

Select `CLEAN_Hound_seed0100_rep01`. Its Object Properties → Custom Properties → `ik_fk` defaults to **0**, using the baked clean Action. Set it to **1** to use the animated `IK_CLEAN_..._A/B/C/D` targets and `CTRL_POLE_CLEAN_...` poles. Re-enable viewport Extras/Bones to see the controls, or select them in `IK_TARGETS` in the Outliner. Moving a target at the current frame works; insert location keys to preserve an edit when changing frames. FK bone editing is available in Pose Mode at `ik_fk = 0`.

## Screening and source diagnosis

The first screen accepts seed 100 repetitions **1, 6, 3**, followed by seed 101 repetition **0**, in that order. Five clips are rejected for excessive lowering/collapse, large endpoint fitting error, or high jerk. These are initial engineering thresholds selected for this small batch; they are not calibrated against a held-out motion-quality dataset.

The selected clip is seed 100 repetition 1. Its median pelvis-to-neck distance is **0.808719 source units**, with approximately **3.46%** relative variation. Its raw endpoint-to-BVH mean discrepancy is **0.1592 body lengths**. The 95th-percentile mismatch between raw edge lengths and the fixed BVH edge lengths is **0.1372 body lengths**. The raw diffusion positions therefore cannot all be represented exactly on the fixed-length exported skeleton. The largest whole-batch fitting outlier is seed 100 repetition 5, frame 8, at `Bip01_HeadNub`: **1.2376 source units**.

The baseline consumes the separately preserved **raw XYZ** trajectories, rather than copying the fitted BVH rotations. This avoids treating the export's fitting artifacts as target joint angles. It does not eliminate the need to inspect the generated motion.

`configs/hound_robot.json` records the named endpoint/bend mapping, target attachments, proportions, contact thresholds, and quality gates. A/B/C/D map to front-left/front-right/rear-left/rear-right. To permute roles, move the source endpoint/bend/role values between entries while keeping each target limb's hip attachment.

Contact detection uses two binomial smoothing passes, full 3D endpoint speed, height hysteresis, and a four-frame minimum duration. Thresholds are normalized by median source body length: height on/off **0.10/0.16**, speed on/off **0.30/0.60 body lengths per second**. The floor is the fifth percentile of smoothed endpoint height. It is estimated, not an observed surface.

In the selected clip, B/C/D are classified as supporting throughout, while A enters at frame **67**. This is why the result is described as a weight shift rather than walking. The detector can mistake a low, slowly moving foot for support; the green markers are hypotheses, not measured forces.

## Transfer and cleanup

The source is converted to Blender Z-up and scaled by **1.112871** to a robot body length of **0.9 design units**. Each of the four robot limbs uses two **0.7-unit** segments. The core follows the pelvis/chest midpoint and body orientation; the head tracks the source head-to-nose direction. Target trajectories, source-relative coordinates, pole directions, contact weights, world anchors, root corrections, and solutions are retained in `motion.npz`.

The two-bone solver preserves segment lengths and constrains total flexion to **8–160 degrees**. Continuous pole directions prevent bend-plane flips. Contact cleanup stores a world anchor, eases entry/exit over three frames, floors the foot surfaces, and adjusts the core when support targets approach the reach limit. Any residual projection is reported and causes this baseline's acceptance checks to fail.

| Metric | Transferred | Contact-cleaned |
| --- | ---: | ---: |
| Mean endpoint speed during detected contact | 0.103990 units/s | 0.003228 units/s |
| Fully pinned interior speed | 0.104095 units/s | Below 1e-12 units/s |
| Maximum foot-surface penetration | 0.015965 units | Below 1e-12 units |
| Unreachable/projected target samples | 0 | 0 |
| Maximum core correction | 0 | 0.006284 units |
| Knee/elbow flexion range | 59.89–117.38° | 24.29–117.38° |
| Minimum remaining extension margin | 13.35% | 2.24% |

The stance sliding reduction is **96.90%**, including contact blends. The remaining slip is concentrated at A's inferred landing transition. The clean limbs approach full extension late in the clip, although every target remains reachable. These design units are not physically calibrated meters.

## Rig and verification

The preview robot has ROOT/CORE/SPINE/HEAD bones, four comparable A–D chains, named end effectors, role properties, editable IK targets/poles, a global IK/FK blend, and a rigid mechanical mesh. Separate `RETARGET_...` and `CLEAN_...` Actions are retained. Live IK permits Y/Z articulation and has an X bend limit of ±160°; the analytic bake enforces the stated total-flexion range. The live bound can be disabled for later non-biological posing experiments.

Verification completed:

- Four regression tests cover BVH round trips, contact hysteresis/short-event rejection, world pinning/swing preservation, and IK lengths/reach/degenerate poles.
- Both robots were compared against the independent numerical solution at every frame in both FK and IK modes.
- The saved file was reopened and rechecked: maximum joint-position error **9.08e-7**, maximum segment-length error **7.42e-7** design units.
- Both saved rigs followed a **0.03-unit** interactive IK target move with errors below **3.2e-7**.
- Mechanical mesh centers were checked at four frames, with maximum error below **7.6e-7**.
- No pole-angle wrapping was found. The maximum recorded adjacent pole-angle change is below **1.8e-6 radians**.
- The MP4 was checked to contain **120 frames, 20 fps, 6.000 seconds**, at 960×540.
- Rendered output and the appended live viewport were visually inspected.

The original raw files and pretrained assets are unchanged. No new models or training data were needed. All generated analyses, robot files, renders, and previews remain on ShareDrive.

## Reproduce

Run from the repository root. Choose new output directories for each experiment.

```bash
MOTION_DATA=/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated
.venv-anytop/bin/python scripts/analyze_motion.py \
  --output "$MOTION_DATA/contact-new" \
  "$MOTION_DATA/hound_seed100_batch8" "$MOTION_DATA/hound_seed101_compare"
.venv-anytop/bin/python scripts/retarget_motion.py \
  "$MOTION_DATA/contact-new/analysis.json" --output "$MOTION_DATA/robot-new"
.venv-anytop/bin/python scripts/plot_contact_report.py \
  "$MOTION_DATA/contact-new/analysis.json" "$MOTION_DATA/robot-new"
/snap/blender/7803/blender --background --factory-startup --python-exit-code 1 \
  --python scripts/build_robot_blender.py -- "$MOTION_DATA/robot-new"
/snap/blender/7803/blender --background --factory-startup --python-exit-code 1 \
  --python scripts/verify_robot_blender.py -- "$MOTION_DATA/robot-new"
/snap/blender/7803/blender --background --factory-startup --python-exit-code 1 \
  --python scripts/render_robot_preview.py -- "$MOTION_DATA/robot-new"
```

`build_robot_blender.py` refuses an existing destination unless explicitly passed `--replace`. `retarget_motion.py --clip ID` selects another gate-passing clip, but will fail rather than silently accepting unreachable clean targets. The remaining accepted candidates have not yet been validated on this robot.

## Next work

1. Expand generation to the planned 50 clips and at least two model families; prioritize a clearly advancing gait with alternating support phases.
2. Validate the reusable rig in upright poses and implement/test biped mapping. The complete Milestone C/D acceptance criteria remain open.
3. Add surface frames, contact confidence/manual overrides, collision checks and support-polygon diagnostics. This is kinematic animation, not a dynamics/stability test.
4. Build loop selection and seams only after source/contact quality is satisfactory. Rhythm, motion chaining, and unusual limb-role operators remain later steps.

The known upstream editing defects remain unmodified.
