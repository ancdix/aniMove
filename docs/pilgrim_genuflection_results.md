# Pilgrim — First Genuflection blockout study

A twelve-second ceremony now runs on the editable Pilgrim blockout: distributed bow, A then B hand planting, four-contact pause, torso reorientation, B then A release, and a separate recovery path. It includes an editable control rig, independent FK bake, raw guided-model comparison, pose stills, and numerical studies. All models and generated files remain on ShareDrive; no new weights or dataset were downloaded.

**This is authored choreography with bounded AnyTop transition variation.** The raw samples did not provide a usable ceremonial sequence without substantial correction. This completes a technical blockout study, but does not pass the plan's stronger goal of recognizable model-generated primary choreography. Surface detail and fabric remain deferred.

[Watch two cycles](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/genuflection_loop_v003/preview/two_cycles.mp4) · [Raw versus final](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/genuflection_loop_v003/comparison_preview/two_cycles.mp4) · [Editable Blender master](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/genuflection_loop_v003/pilgrim_genuflection_master.blend)

[Four-contact pose](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/genuflection_loop_v003/pose_four_contacts.png) · [Pose study](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/genuflection_loop_v003/pose_study.png) · [Onion skin](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/genuflection_loop_v003/onion_skin.png) · [Trajectories and contacts](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/genuflection_loop_v003/trajectory_study.png)

## Sequence and rig

| Time | Directed action |
| --- | --- |
| 0–1.2 s | Upright pause |
| 1.2–2.8 s | Distributed bow and lowering |
| 2.8–3.9 s | A approaches and plants |
| 3.9–5.0 s | B follows into four-contact support |
| 5.0–6.6 s | Four-contact pause; shared context joins two generation windows |
| 6.6–8.0 s | Small torso turn |
| 8.0–8.8 s | Begin recovery while both hands remain planted |
| 8.8–9.8 s | Release B first; retain A as an anchor |
| 9.8–11.0 s | Release A and return by a different torso path |
| 11.0–12.0 s | Upright pause and closed loop seam |

C/D remain planted throughout. Contact weights fade over six frames while the hand is stationary on its anchor, so the fade itself cannot cause a slide. Sensor direction stays world-oriented; this is an authored stabilization, not inferred gaze behavior. “Support” here describes the kinematic contact schedule; balance and load transfer were not simulated.

Scenes: `PILGRIM_First_Genuflection` is the solo view; `PILGRIM_Genuflection_Loop` is the raw-versus-final comparison. They share `PILGRIM_GENU_RIG`, with controls prefixed `PILGRIM_GENU_CTRL`. Enable viewport Extras/Overlays to see them. The controls follow the [Devotional Hold control guide](pilgrim_devotional_loop_results.md), now with animated A/B contact weights.

The editable Action is `PILGRIM_Genuflection_Controls_v001`. To use `PILGRIM_Genuflection_Final_FK_v001`, select it and set rig `use_controls=0`; restore the controls Action and `use_controls=1` to edit. Control objects also carry animation. The FK bake samples at 80 Hz. The scene plays frames 1–240 at 20 fps, with closing key 241. The embedded `PILGRIM_GENU_CONTROL_UTILITIES.py` provides contact and IK/FK matching helpers.

Upper-arm shells start farther from their shoulder bearings, using an additional proximal inset of 10% of segment length. This fixes a measured A-shell/carrier collision without adding a collision exclusion. Bone lengths, model topology, and the existing chest-mounted ring are unchanged.

## AnyTop experiment

The verified Pilgrim `condition_v002` and existing checkpoints were reused. Its Hound-derived calibration statistics remain a limitation: this is not evidence of morphology-only motion discovery.

Three versioned pilots preserve 32 generated six-second windows:

- `genuflection_pilot_v001`: eight samples across `all`/`bipeds`, two seeds, and descent/recovery windows. Sparse context produced body reversals and ground penetration.
- `genuflection_pilot_v002`: sixteen samples, adding short context windows and four seeds. These followed the storyboard more closely, but the final A-support recovery guide exceeded reach by about 0.05 design meters.
- `genuflection_pilot_v003`: eight `all` samples after lowering that recovery pose. All authored guide targets are reachable. This is the source of the final study.

The chosen descent is `all_half0_seed6100`; recovery is `all_half1_seed6103` (its actual diffusion seed is 6113). These are independent generated transitions, not reversed playback. Selection compares correction magnitude, motion changes, reach, and clearance across candidates. Shared still context joins them at six seconds.

Full-pose context, in zero-based half-open intervals, is:

- Descent: `[0,16)`, `[40,48)`, `[72,84)`, `[96,120)`.
- Recovery: `[0,16)`, `[36,44)`, `[64,72)`, `[96,120)`.

Root orientation features and horizontal root velocity are constrained throughout. Remaining features are generated outside those full-pose windows. Masks and guides are saved. All masked normalized features match exactly; changing every unmasked guide value to `123.456` produced exactly the same output in the probe. Thus the unknown guide interpolation is not leaking through the diffusion mask. Fixed-mask coverage is not a measure of artistic contribution.

## Corrections and provenance

Final motion uses fixed-length fitted source, explicit contact targets, bounded deviations from the authored guide, world-oriented head direction, and mechanical IK. The principal bounds are root deviation of 0.02/0.065/0.02 design meters, 10-degree body-direction and 5-degree attachment-direction cones, a 12-degree outward limb-bend sector, and up to 0.12-meter free-hand residual before contact blending. Filtering after those limits removes abrupt changes; fixed-length reconstruction and contact solves follow filtering.

The first/last sixteen frames of each six-second window return to authored context, with eight-frame fades. This preserves the shared pause and loop seam. Temporal smoothing and contact corrections are production edits, not model physics.

| Joint-position difference | RMS, design meters | Maximum |
| --- | ---: | ---: |
| Raw → fixed-length fitted | 0.16371 | 0.57498 |
| Fitted → final cleanup | 0.17722 | 0.68267 |
| Raw → final | 0.19377 | 0.81336 |
| Final → authored guide | 0.04244 | 0.22994 |
| Root-aligned fitted → final | 0.19432 | 0.71086 |
| Root-only fitted → final | 0.06559 | 0.19205 |

The final is much closer to the authored guide than to the fitted model sample. AnyTop contributes transition variation and settling, while the guide determines the action and most large-scale movement. These measurements do not support calling it primarily learned choreography. The earlier Devotional Hold remains the clearer example of preserved generated body motion.

[Full correction/selection report](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/genuflection_loop_v003/loop.json) · [Candidate scores](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/genuflection_loop_v003/selection.json) · [Contact schedule](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/genuflection_loop_v003/contacts.json) · [Generation manifest and checkpoint/source hashes](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/genuflection_pilot_v003/run.json)

`motion.npz` retains aligned RAW, FITTED, GUIDE, CLEAN, mask, poles, anchors, and contact weights. Raw/fitted arrays have 240 frames; guide/clean/controls include closing frame 241. The raw comparison displays the selected original outputs before cleanup.

## Verification

[Saved-master validation](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/genuflection_loop_v003/saved_validation.json)

- All 21 repository unit tests pass, including stationary contact intervals and the previously unreachable recovery pose.
- Every numerical target is reachable; maximum bone-length error is `5.55e-16` design meters.
- Reopened rig joint error is at most `1.31e-5`; FK bake versus evaluated controls is at most `8.32e-6`.
- Contact/ground verification covers 961 poses at 80 Hz. Rear-contact drift is at most `1.35e-6`; planted-hand drift is at most `1.17e-6`. Minimum mesh height is `-2.56e-5`, within the recorded numerical tolerance.
- Measured loop-seam position, head orientation, and finite-difference velocity mismatches are zero.
- No non-excluded mesh-surface intersections were found at two-frame intervals. Same/adjacent-bone interfaces and the original ten intended carrier interfaces remain excluded. This is sampled surface testing, not continuous collision proof.
- Root, free palm, distal orientation, anchors, contact switching, head lock/aim, and edited-pose IK/FK matching pass the saved-file functional checks.
- Numerical 20-fps peak joint acceleration fell from 32.58 to 5.10 design meters/second squared after post-limit filtering; its 95th percentile fell from 6.78 to 1.75. These are motion smoothness measurements, not physical force estimates.

Versions 001/002 remain diagnostic artifacts. **`genuflection_loop_v003` is the final verified study.** Source snapshots, logs, and artifact hashes accompany it. Live loading appends new scenes and preserves previous scenes and Actions.

## What this establishes

The blockout can perform the intended contact-role sequence with editable controls and a reusable baked Action. P4's technical delivery is demonstrated, while its learned-primary-motion gate remains open. Review this study for timing and silhouette before detailing. To pursue stronger model authorship, the next motion experiment should select shorter phrases that already have the desired support transition, simplify choreography around those phrases, and compare against this authored baseline. Adding cloth or more random seeds would not address the measured gap.
