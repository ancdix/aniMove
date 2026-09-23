# Pilgrim blockout and direct AnyTop pilot

The first Pilgrim blockout is built and loaded in Blender. It has a segmented tower, sensor/halo, torso ring, four three-segment limbs, simple contact pads, neutral limb labels, and an editable armature. Geometry remains deliberately simple; no fabric, weathering, detailed mechanisms, or final surfacing has been added.

Two separate scenes distinguish authored rig testing from model output:

| Scene | What it shows | Preview |
| --- | --- | --- |
| `PILGRIM_Blockout` | Authored upright → bow → one hand → four contacts → turn → recover pose envelope, 241 frames at 20 fps | [Pose-test video](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/blockout_v004/preview/preview.mp4) |
| `PILGRIM_Direct_AnyTop` | Unconditional AnyTop on the actual Pilgrim graph: raw positions beside a fixed-length fitted blockout, 120 frames at 20 fps | [Direct-generation video](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/pilot_v002/comparison/preview/preview.mp4) |

[Blockout Blender file](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/blockout_v004/pilgrim_blockout.blend) · [Direct-generation Blender file](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/pilot_v002/comparison/pilgrim_direct_anytop.blend) · [Upright view](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/blockout_v004/pose_upright.png) · [Four-contact view](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/blockout_v004/pose_four_contacts.png)

## Blockout and rig scope

The model skeleton contains 23 joints. Blender additionally uses four carrier bones for the visible limb mount assemblies. The model-facing names carry anatomical semantics, while the artist-facing limb names are A–D. A/B attach to the upper body; C/D attach near the core. Source coordinates are Y-up/Z-forward; Blender uses `(x, -z, y)` and explicitly declared design meters.

The saved blockout contains baked FK and calibrated wrist IK targets/poles with per-limb `ik_A` through `ik_D` properties. Defaults are FK. IK matches the authored keyed poses, but this is not yet the full production control rig: palm/distal orientation controls, interactive IK/FK snapping, head-target controls, and contact-state controls remain P2 work. The head direction in this test is authored rather than controlled by a live look-at constraint.

The pose sequence is a rig envelope test, not a generated motion or a finished ceremonial loop. Free hand paths and rear-limb bend directions were adjusted after tests exposed forelimb/rear-limb crossing during recovery. Contact-pad rotation was corrected after an earlier build put the pads partly below the floor. Versions 001–003 remain diagnostic artifacts; **004 is the verified authored blockout**. The direct comparison uses the same rest geometry with its own model-driven poses, rather than the authored pose corrections.

## Saved blockout verification

[Saved validation report](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/blockout_v004/saved_validation.json)

- All authored numerical targets are reachable without projection; segment-length error is below `5e-16` design units.
- Ring-to-limb proxy clearance is at least **0.137** design units; interlimb capsule clearance is at least **0.155** at authored integer frames.
- Reopened Blender FK and wrist IK agree with the numerical joints to approximately **1.11e-6** and **1.40e-6** units respectively across all 241 frames.
- Ground and rear-contact checks cover **961 poses at 80 Hz**. Minimum evaluated mesh height is **-1.71e-5** units; maximum rear contact drift is **1.94e-5** units, within the recorded numerical tolerances.
- Evaluated mesh surface checks every four frames report no non-excluded intersections. Same-bone, adjacent-bone, and ten explicitly listed intended carrier/bearing interfaces are excluded. This is a sampled surface-intersection check, not a complete volumetric or continuous collision proof.
- Sixteen repository tests pass, including two Pilgrim tests for reachable poses, fixed lengths, clearances, and four-contact anchor preservation.

These checks establish a usable blockout pose envelope. They do not establish dynamic balance, impact physics, arbitrary-edit safety, or the quality of the direct model samples.

## Direct custom-skeleton conditioning

This is the first experiment in this repository where AnyTop receives the **Pilgrim skeleton itself**. Generated output is not a Hound motion transferred afterward to the robot.

However, the official custom-skeleton preprocessor needs motion statistics as well as a rest skeleton. Existing generated Hound motion was transferred to Pilgrim rest vectors and fitted to its lengths solely to produce calibration BVHs. The official `process_skeleton` pipeline then generated the custom condition. This calibration can bias the resulting movement; the experiment is not evidence that morphology alone determines behavior.

Two conditions were compared:

- **Condition 001:** all eight available seed-100 Hound calibration transfers.
- **Condition 002:** only three transfers with calibration-fit RMS ≤0.06 and maximum error ≤0.18 design units; the five rejected transfers are recorded. No showcase poses or ceremonial-motion guides were used for these statistics.

The condition was checked for joint order, topology, finite values, positive position/rotation/velocity standard deviations, and a consistent scale. Zero contact-channel standard deviations for non-contact joints remain documented rather than replaced with invented contact data. The normalization scale is approximately **0.492202 model units per design meter**. The official preprocessing's optional video generation was skipped; calibration XYZ, BVH, fit logs, and the Blender previews are retained.

[Filtered conditioning manifest](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/condition_v002/condition_manifest.json)

Each condition generated four matched seeds (`5100–5103`) for each of the unified, quadruped, and biped checkpoints: **24 Pilgrim samples total**. Each checkpoint also generated a seed-5100 Hound control in each run. The three controls are byte-identical across the two runs, confirming that the change was isolated to the Pilgrim condition.

All sampling was unconditional with respect to motion: no keyframe mask, authored path, contact schedule, or procedural gait was supplied at inference. The custom skeleton and its calibration statistics remain conditions.

| Prior | Mean fit RMS, condition 001 | Mean fit RMS, condition 002 |
| --- | ---: | ---: |
| Unified | 0.404 | 0.270 |
| Quadruped | 0.360 | 0.274 |
| Biped | 0.209 | 0.143 |

Values are in design units and measure raw XYZ to fixed-length reconstruction. Filtering the calibration reduced this error in all 12 paired Pilgrim samples. This is sensitivity to calibration choice, not an improvement to the trained model or proof of broad generalization.

## Selected direct-motion candidate

The displayed candidate is **condition 002 / biped prior / seed 5100**. It has relatively quiet body motion and head/limb variation; it is a candidate for an idle/settling study, not walking or genuflection.

- Raw-to-fixed-length fit RMS: **0.132** design units; maximum: **0.317**.
- Largest raw joint displacement in one 20-fps frame: **0.060** units; 95th percentile: **0.0235**.
- Raw bone-length ratios have 5th/95th percentiles of **0.618 / 1.133**, so fixed-length reconstruction still makes material changes.
- The fitted contact-point minimum is approximately **-0.00925** relative to the normalized rest floor. The preview stage is lowered for diagnostic visibility; it does not represent solved foot contact.
- No smoothing, world-foot pinning, procedural motion replacement, time editing, or loop construction was applied to the displayed model motion. End-effector pad orientation and the visual attachment of body modules are rig/display choices.
- The six-second clip is **not a seamless loop**, and its contacts and self-collisions have not passed the authored blockout's clearance tests.

The saved comparison was reopened and checked over all 120 frames. Raw displayed points agree with the raw array within **1.32e-7** units; rig joint heads agree with the fitted array within **8.33e-7**. Named joints and 20-fps timing also survive BVH export/reload.

[Pilot 001 manifest](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/pilot_v001/run.json) · [Pilot 002 manifest](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/pilot_v002/run.json) · [Saved comparison verification](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/pilot_v002/comparison/saved_validation.json)

## Live session and next work

Both scenes were appended into the running Blender session. `PILGRIM_Blockout` is active and playing the authored pose test. All **16 pre-existing scenes and 417 Actions** were preserved, including the original Cube/Camera/Light scene. Saved files on ShareDrive are the durable artifacts; the existing live workspace was not overwritten.

P0 now has a verified blockout and pose envelope. P1 has a working direct-generation path, a bounded comparison across priors and calibration statistics, and a candidate worth developing; production motion quality remains provisional. The next work is **P2/P3 on this same blockout**: finish the distal/contact/head controls, measure and clean the selected model motion, and construct the first usable settling loop while tracking changes from the raw sample. Detailed modeling and fabric remain deferred.

Core scripts: `pilgrim_skeleton.py`, `prepare_pilgrim_condition.py`, `run_pilgrim_pilot.py`, `build_pilgrim_blockout.py`, `build_pilgrim_comparison.py`, `verify_pilgrim_blockout.py`, `verify_pilgrim_comparison.py`, `render_pilgrim_previews.py`. Each takes the asset paths shown in its argument parser or docstring. AnyTop uses `.venv-anytop/bin/python`; Blender scripts use the separate Blender executable.
