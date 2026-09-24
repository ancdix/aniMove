# Pilgrim — Motion Harvest 001

2026-09-23. **120 unguided three-second samples produced three curated phrases and a six-second Orient loop.** This improves on the genuflection study's primary-motion authorship: no action guide, contact schedule, root path, or key poses were supplied to AnyTop. Names were assigned after inspecting movement. The three native phrases retain every fixed-length fitted body/head frame. This is promising upper-body vocabulary, not evidence of robust new support-role behaviors or physical balance.

## Review assets

- [Three phrases, raw beside final — nine-second video](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/motion_harvest_001/curated_v004/three_behaviors.mp4).
- [Orient loop — two cycles](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/motion_harvest_001/curated_v004/Orient_Loop/preview/two_cycles.mp4), [aligned raw/final loop comparison](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/motion_harvest_001/curated_v004/Orient_Loop/comparison_preview/two_cycles.mp4).
- [Blender master: eight scenes and four baked Actions](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/motion_harvest_001/curated_v004/motion_harvest_master.blend).
- [Offline interactive viewer: all 120 raw/fitted samples](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/motion_harvest_001/viewer.html), [CSV catalog](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/motion_harvest_001/catalog.csv), [full measurements](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/motion_harvest_001/analysis.json), [first of ten raw pose sheets](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/motion_harvest_001/atlas/raw_sheet_01.png).

All large assets and existing weights remain on ShareDrive. The blockout and older motion studies are preserved. Final assets are in `curated_v004`; earlier numbered directories are diagnostics.

## Generation and curation

Forty seeds (7100–7139) were generated for each checkpoint family: `all`, `quadropeds` (upstream spelling), and `bipeds`. Each sample has 60 frames at 20 fps, with three matched Hound controls using seed 7100, for 123 generated clips total. Existing `condition_v002` and model weights were reused. No new training or downloads were needed.

This is direct Pilgrim conditioning, but its feature calibration still derives from Hound statistics. It is not a demonstration of learning from morphology alone. The run manifest preserves condition/checkpoint hashes, source revision, scale, seeds, and fitting errors. Features, original XYZ, fitted XYZ, BVH, and fitting logs are retained for every sample.

Analysis measures raw and fitted data separately: A–D contact candidates, root height/range, torso pitch/yaw/roll, head motion, support-state changes, displacement, pose span, acceleration/jerk, and asymmetry. The HTML viewer supports sample selection, frame scrubbing, view rotation, and native/half-speed playback. Pose sheets and numeric screening narrowed candidates before constructing blockout comparisons.

Contact candidates require joint height within 0.10 design m of the declared 0.06 m contact-joint floor level, speed below 0.30 m/s after a one-frame Gaussian filter, and runs of at least four frames. Strict (0.06 m / 0.20 m/s) versus loose (0.14 m / 0.45 m/s) thresholds expose uncertainty. Agreement is 45% for Orient, 88% for Listen, and 80% for Unfold. These are proximity/speed heuristics, not measurements of load. The contact cleanup is an explicit production interpretation.

Initial contact-only screening passed no clips through the interlimb-clearance gate. Thirteen eligible candidates were then tested with constant per-limb clearance adjustments. Four passed that numerical screen; three were selected for different movement character. This is a curated result from a difficult batch, not a claim that most output is immediately usable. Median raw-to-fitted RMS was 0.248 m (`all`), 0.320 m (`quadropeds`), and 0.140 m (`bipeds`).

## Three discovered phrases

| Working title | Source | Observed movement | Raw → fitted RMS | Fitted → final RMS | Raw → final RMS |
| --- | --- | --- | ---: | ---: | ---: |
| Orient | bipeds / 7120 | Torso turns, neck lifts; about 19° raw yaw range | 0.124 m | 0.069 m | 0.146 m |
| Listen | bipeds / 7132 | Sideways head dip/recovery with asymmetric free-hand response | 0.139 m | 0.065 m | 0.154 m |
| Unfold | all / 7120 | Curled upper body extends upward; 0.65 m raw head displacement | 0.168 m | 0.054 m | 0.176 m |

Values are unaligned world joint-position RMS in declared design meters over all 23 joints and 60 frames. RMS stages are not additive. Full p95/max values are in each `motion.json`; normalization is 0.4922019146 source units per design meter, with a 2.9 m rest-skeleton height.

All three native clips preserve fitted joints ROOT through SENSOR (0–6) exactly over all 60 frames; no body-path rewrite, head stabilization, new key-pose sequence, or timing change was applied. Generated distal orientations also drive the controls. Raw-to-fitted body-velocity cosine is 0.910, 0.703, and 0.728 respectively, so fitting itself must remain visible in contribution accounting. These are not percentages of AI authorship.

Clearance corrections are small in parameter count but visibly meaningful: the B hand is shifted laterally by approximately 16.7, 16.4, and 8.1 cm respectively, with constant B/D bend rotations up to 36.5°. Inferred planted contacts are pinned and blended; limb IK enforces fixed lengths with a 2° minimum flexion. These changes are recorded, not described as untouched output. The native phrases preserve body/head movement at original timing and are not themselves cyclic.

Orient and Listen keep C/D contact candidates throughout. Unfold has a short early D break while C remains a candidate. None establishes the desired family of reliable three-/four-contact role transitions. Their distinctness is gestural and should be judged in playback.

## Orient loop

Orient became the six-second candidate through uniform 2× duration and an endpoint bridge; it is not reversed playback. Source and final comparisons use identical timing. Eleven boundary frames are adjusted; fitted body/head frames 7–55 remain unchanged to numerical precision (49 of 60 frames, maximum error 2.8e-12 m).

The boundary bridge contributes 0.019 m joint RMS; all fitted-to-final changes total 0.071 m RMS, and raw-to-final totals 0.147 m. Contacts and constant clearance edits still affect limbs throughout. A free B endpoint needed at most 3.7 mm reach projection; planted targets remain exact. The closing key is frame 61, outside the 1–60 playback range at 10 fps.

This is a polished blockout loop for artistic review. Surface detail, fabric, physics, and a new storyboard have not been added.

## Saved-file validation and editing

All three native assets and the loop pass control-to-joint reproduction, visual FK bake, ground, planted-contact, and sampled evaluated-mesh checks. Ground/contact checks run at 80 Hz (237 poses per native phrase, 481 for the loop). Mesh surface intersections are checked at each integer frame, excluding same/adjacent bone interfaces and the ten named original carrier mounts. This is not continuous volumetric collision checking or a dynamics test.

For Orient Loop: planted drift is 1.04e-6 m, minimum evaluated mesh height −9.67e-7 m, maximum control error 4.56e-5 m, and maximum bake error 2.34e-5 m. No tested non-excluded mesh intersections were found. Seam position mismatch is zero; finite-difference seam velocity mismatch is 0.00163 m/s. All 23 repository tests pass. Distal-quaternion hemisphere continuity was repaired after detecting between-frame foot slips; final results use that fix.

The combined master was reopened and verified to retain all eight scenes and four independent baked Actions. Solo scenes are `PILGRIM_Orient`, `PILGRIM_Listen`, `PILGRIM_Unfold`, and `PILGRIM_Orient_Loop`; each has a `_Compare` counterpart sharing its rig. The loop scene is active on opening. Native scenes are short noncyclic phrases, so their endpoint jump when repeatedly played is expected.

Each rig records `control_action`, `baked_action`, and `control_prefix`. Editable controls are active by default (`use_controls=1`). To use a baked Action, assign its recorded Action to the rig and set `use_controls=0`; return to the recorded control Action and `use_controls=1` for editing. Embedded control utilities and the [control guide](pilgrim_devotional_loop_results.md) describe matching controls. Baked names follow `HARVEST_<TITLE>_Final_FK_v001`.

## Reproduction and next decision

Repository scripts cover generation (`run_pilgrim_harvest.py`), analysis/viewer (`analyze_pilgrim_harvest.py`, `plot_pilgrim_harvest.py`), screening (`clean_pilgrim_harvest.py`, `optimize_harvest_clearance.py`), final preparation (`prepare_harvest_assets.py`), Blender build/verification (`build_pilgrim_harvest.py`, `verify_pilgrim_harvest.py`), and packaging/live append. Builders reject existing outputs; use new version directories for future runs. The ShareDrive archive contains script snapshots, logs, manifests, and checksums.

Review whether Orient, Listen, and Unfold feel like useful, distinct Pilgrim behaviors. This harvest supports discovering movement before naming it and retains more identifiable generated primary motion than the genuflection storyboard. The remaining gap is support-role diversity. Choose the next conditioning/morphology experiment from that evidence rather than adding an authored support sequence and counting it as discovery. Keep armor and fabric deferred through this review.
