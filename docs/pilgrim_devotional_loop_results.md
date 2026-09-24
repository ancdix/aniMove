# Pilgrim — Devotional Hold

The first usable Pilgrim settling loop is built: six seconds at 20 fps, with an editable control rig and a separate FK bake. It remains a simple ivory/brass/dark blockout. The clean scene is `PILGRIM_Devotional_Hold`; `PILGRIM_Devotional_Loop` shows the original raw AnyTop skeleton beside the cleaned creature. Both were appended to the live Blender session, preserving its 18 existing scenes and 480 Actions.

[Watch two cycles](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/devotional_loop_v003/preview/two_cycles.mp4) · [Raw versus cleaned comparison](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/devotional_loop_v003/comparison_preview/two_cycles.mp4) · [Editable Blender master](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/devotional_loop_v003/pilgrim_devotional_master.blend)

## Motion source and edits

The source is `pilot_v002/Pilgrim_bipeds_seed5100`, generated directly for the 23-joint Pilgrim graph. Its generation used no guide poses, contact schedule, or path. Hound-derived calibration statistics remain a source of bias; see the [direct-generation report](pilgrim_blockout_results.md).

The original 120-frame timing is retained. A cubic Hermite bridge replaces 23 frames around the boundary; the interior frames 13–109 retain the fitted source before length/contact correction. There is no reversed recovery, new procedural gait, or time warp. Root, spine, neck, head, and sensor positions in those 97 interior frames remain unchanged to numerical precision after cleanup. This is an identifiable model-generated body/head phrase, while the supporting limb configuration is substantially edited.

Explicit authored changes:

- C/D stay planted at median source horizontal positions throughout. A/B remain free.
- B's hand receives a constant source-space offset of `(-0.34, +0.085, 0)` design meters; its bend preference is biased outward. Its time variation outside the boundary region remains from the source.
- Distal segments begin at their rest directions, with world-flat pads. Two-link solves adjust the upper/lower segments to meet those targets.
- The ring mounts to the chest (`SPINE_02`) instead of the neck hinge, with an axial offset of `-0.05` design meters. This changes visual geometry, not the model graph or source generation.

| Position correction across joints/frames | RMS, design meters | Maximum |
| --- | ---: | ---: |
| Raw AnyTop → fixed-length fitting | 0.13153 | 0.31656 |
| Boundary bridge alone | 0.02714 | 0.23633 |
| Contact, hand clearance, and distal cleanup after length restoration | 0.12669 | 0.38974 |
| Final → fitted source | 0.12909 | 0.38974 |
| Final → raw source | 0.19709 | 0.48373 |

The corrections are meaningful, especially the roughly 0.35-meter B-hand offset. They should not be described as negligible or converted into an “AI percentage.” The comparison's raw side intentionally retains the original unclosed seam. `motion.npz` preserves RAW, FITTED, BRIDGED, NORMALIZED, and CLEAN arrays with matching frame indices; CLEAN also contains closing key 121.

[Correction metrics and provenance](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/devotional_loop_v003/loop.json) · [Contact schedule](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/devotional_loop_v003/contacts.json) · [Contribution measurements](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/devotional_loop_v003/contribution_analysis.json)

## Editing the rig

Stop playback and enable viewport Overlays/Extras to see the control objects. The rig is `PILGRIM_LOOP_RIG`; controls use the `PILGRIM_SETTLE_` prefix. The solo and comparison scenes share this rig, so edits affect both.

| Control/property | Use |
| --- | --- |
| `CTRL_ROOT` | Move/orient the body while planted contact anchors remain in world space |
| `CTRL_CHEST` | Rotate the chest/spine section |
| `CTRL_HEAD`, `CTRL_LOOK_TARGET` | Edit head orientation or aim target |
| Rig `head_world_lock`, `head_look_at` | Blend world orientation stabilization or target aiming; both default to zero to preserve generated head motion |
| `CTRL_PALM_A` … `D` | Position/orient each free hand/foot |
| `CONTACT_ANCHOR_A` … `D` | Position/orient the corresponding planted contact |
| `CTRL_DISTAL_A` … `D` | Rotate distal articulation about the palm frame |
| `PILGRIM_LOOP_POLE_A` … `D` | Edit limb bend direction |
| Rig `contact_A` … `D` | Blend free target to planted anchor; defaults A/B=0, C/D=1 |
| Rig `ik_A` … `D` | Blend limb IK/FK; defaults 1 |

The active Action is `PILGRIM_Devotional_Controls_v001`. Controls themselves also have animation. To use the independent baked Action, select `PILGRIM_Devotional_Final_FK_v001` and set rig `use_controls=0`; restore the controls Action and `use_controls=1` for editing. The FK bake samples at 80 Hz and plays at the scene's 20 fps. Playback uses frames 1–120; key 121 closes the six-second cycle. Periodic curves have matching boundary derivatives.

The embedded `PILGRIM_CONTROL_UTILITIES.py` Text and repository `scripts/pilgrim_controls.py` provide matching helpers:

```python
import bpy
from pilgrim_controls import snap_fk_to_ik, snap_ik_to_fk, set_contact
rig = bpy.data.objects['PILGRIM_LOOP_RIG']
snap_fk_to_ik(rig, 'A')  # Match FK to current IK pose; switch to FK.
snap_ik_to_fk(rig, 'A')  # Match IK to current FK pose; switch to free IK.
set_contact(rig, 'A', True, keyframe=True)  # Match anchor, then plant.
```

Run the embedded Text once to load its helpers or add the repository's `scripts` directory to Python's module path before importing. Snap helpers match the current evaluated pose; they do not automatically key the changed transforms. Key edits deliberately. Normal animation playback uses built-in constraints/property drivers and does not need these helpers to execute.

## Verification and limits

[Saved-file checks](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/devotional_loop_v003/saved_validation.json) · [Packaged master checks](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/devotional_loop_v003/package_validation.json)

- All 19 repository unit tests pass, including boundary-bridge preservation tests.
- Reopened control rig matches corrected joint positions within `5.09e-6` design meters; the FK bake matches evaluated controls within `3.31e-6`.
- Across 481 subframe poses, maximum planted-foot drift is `1.58e-6`; minimum mesh Z is `-6.20e-7`.
- Measured seam position and head orientation mismatch are zero. Finite-difference seam velocity mismatch is `0.00132` design meters/second.
- Evaluated mesh surfaces checked every two frames contain no non-excluded intersections. Same/adjacent-bone interfaces and ten explicit carrier/bearing interfaces are excluded. This is sampled surface testing, not continuous volumetric collision proof.
- Root, free palm, anchor, distal orientation, contact switching, head lock/aim, and IK/FK snapping were exercised. Snapping after an actual hand edit produces at most `2.81e-6` position change.
- Reopening the packaged master preserves both Actions' key/handle signatures. Both videos are verified at 20 fps: 120 frames for one cycle and 240 for two.

The loop establishes a usable settling phrase, not simulated balance or landing physics. Arbitrary future edits require renewed reach/collision checks. Diagnostic versions 001/002 are retained; **003 is the validated asset**.

## Reproduction and next milestone

Use `prepare_pilgrim_loop.py` with the pilot, blockout, and a new output directory; then run `build_pilgrim_loop.py`, `verify_pilgrim_loop.py`, and `package_pilgrim_loop.py` in separate background Blender processes with that directory after `--`. `render_pilgrim_previews.py` renders the saved master. Implementation snapshots, logs, and a hash manifest are stored with the output. No new weights or datasets were downloaded.

The loop-specific P2 controls and P3 deliverable are complete. Next is **P4: First Genuflection in blockout**—distributed bow, sequential A/B hand placement, four-contact settling, reorientation, and a distinct recovery. The new rig must be rechecked across that broader pose envelope; passing this idle does not establish those transition gates. Detailed armor, fabric, and surface finishing remain deferred.
