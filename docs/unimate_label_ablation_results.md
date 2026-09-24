# UniMate Pilgrim: joint-label experiment 001

Changing semantic joint names changes the generated motion even with identical geometry, prompt and initial noise. Front/hind naming biases these nine matched cases toward lower body postures, but does not reliably produce four-foot contact or a quadrupedal gait. This is a conditioning control worth keeping in the motion-harvest workflow, not a replacement for morphology or contact solving.

## Review

- [All nine matched comparisons and pose sheets](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_labels_001/review/index.html).
- [18-second comparison video](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_labels_001/review/all_pairs.mp4).
- [Three-rig Blender master](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_labels_001/labels_comparison.blend).
- [Accepted labels, normalization examples and published vocabulary evidence](unimate_joint_label_guide.md).

Live Blender scene: `PILGRIM_UniMate_LABELS`. The **UniMate → Matched joint labels** sidebar selects all three versions together. Left is arms/legs, center front/hind legs, right generic `Bone`. The opening live case is `p05_9602`, an illustrative large effect; all nine cases remain available. Playback wraps with a hard reset, not a repaired loop. Reopening the standalone master requires running its embedded `UNIMATE_LABELS_UI.py` to restore the optional selector.

## Controlled experiment

27 raw two-second clips: three name sets × three prompts × three seeds (9600–9602), plus three exact baseline replays at seed 9600. Prompts are “The creature walks forward slowly.”, “The creature crouches low and moves forward.” and “The creature extends one front limb toward the ground.” Native output is 60 frames at 30 fps, CFG 3.0.

Only the 16 limb entries of `clean_joint_names` change. The seven core names, 23-joint rest geometry, raw joint identifiers, graph, canonical facing, registration motion, model, action text and all other conditioning remain identical. We do not rerun canonicalization after relabeling. The generic variant uses `Bone` for every limb joint; it removes side and segment semantics together and is not a zero-embedding or disabled-name control.

An observation-only wrapper hashes the actual initial noise and conditions entering stock `generate_samples`. For each prompt/seed, noise hashes and every condition field except `joint_names_emb` match. No known-motion or keep masks are supplied. All three unchanged baseline replays reproduce the original feature files bit for bit. [Run, hashes and condition audit](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_labels_001/run.json).

No IK, smoothing, ground correction, authored guide, retiming, loop repair or retargeting was applied. Blender uses exact forward kinematics, with constant X offsets only to put the three rigs beside one another. Pose-sheet thumbnails align root X/Z for inspection and retain original height; this is explicitly labeled. Stock-video cameras can differ across samples, so use Blender or the common pose sheets for direct spatial comparison.

## Measured effects

Median across nine matched prompt/seed pairs, in Pilgrim design meters:

| Change from arms/legs | Joint-position RMS | Root-relative pose RMS | Motion-change RMS |
|---|---:|---:|---:|
| Front/hind legs | 0.281 | 0.260 | 0.261 |
| Generic Bone | 0.481 | 0.343 | 0.461 |
| Unchanged replay (3 cases) | 0.000 | — | — |

Joint-position RMS is the square root of the mean squared Euclidean joint displacement across joints and frames. Root-relative RMS subtracts each frame's root position. Motion-change RMS subtracts each clip's own initial pose before comparing, showing that the differences extend beyond initial placement. These measure change, not animation quality. [Full paired metrics](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_labels_001/paired_analysis.json).

Front/hind names lower mean root height in all nine pairs, by a median **0.061 m**, with decreases from 0.020 to 0.372 m. Nevertheless, low-speed floor-contact candidates for A/B remain nearly absent. The candidate heuristic is absolute tip height below 0.06 m and speed below 0.30 m/s; it neither proves load support nor estimates forces. Some relabeled clips have more abrupt motion than the baseline.

Visual observations from all nine four-pose sheets:

- `p05_9602`: the arms/legs baseline stays comparatively upright; front/hind starts deeply compressed and rises. Generic names also change this phrase. This is an illustrative large effect, not a representative median example or verified support transition.
- `p03_9600`: front/hind and generic names produce much deeper late-clip compression, including visible floor penetration. Lowering the body is not automatically better grounding.
- `p03_9601`: names change arm/front-limb folding even though the broad upright progression remains similar.
- The walking cases retain an upright, broadly bipedal appearance across name sets. The common rest pose and high A/B attachment points remain plausible contributors; this experiment does not isolate their effects.

This establishes a causal effect of name conditioning for this checkpoint and skeleton. Three seeds, three prompts and one morphology do not establish a universal semantic mapping or general improvement. Some animal rigs themselves use arm/hand labels; naming is not a binary human-versus-animal switch.

## Vocabulary conclusion

There is no runtime whitelist: one nonblank cleaned string per joint is accepted and encoded, including duplicates. We tested common anatomy, generic labels and invented strings through the active encoder. All produced finite embeddings. That only establishes acceptance. Anatomical terms such as `Left Front Leg`, `Left Hind Knee`, `Tail` and `Left Wing` have direct published annotation evidence; invented mechanical descriptions have much weaker evidence of useful learned behavior. The guide separates accepted strings, rule normalization, and observed annotation frequency.

For the next motion harvest, keep both arms/legs and front/hind variants as deliberate generation conditions and preserve their provenance. If the aim is consistent quadrupedal support, the next independent factor to test is rest pose/morphology with labels held fixed. Do not infer from these results that renaming alone repairs contact or balance.

## Verification and provenance

The saved master was reopened and all 30 Actions checked against their raw source FK at every frame. Maximum joint-position discrepancy is **0.000003392 design m**. Source feature hashes and action prompts match. The comparison selector's next/previous round trip passes. [Saved verification](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_labels_001/saved_blender_validation.json). Existing live scenes, Actions and scene object memberships are preserved on append; [live-session check](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_labels_001/live_session.json).

Generation uses official code commit `9f3076e1db482883edb6f6a37a67f521c3853278` and the same independently trained checkpoint as the prior harvest, SHA256 `116fbc42f2436fbd115e6558dcfa17adc3a614bf937e17bb743a6a31aadf09c7`. Model assets and outputs remain on ShareDrive. No new weights or large dataset download was necessary. Source snapshots and checksums are in the experiment's `reproduction/` folder.

Weights availability checked on 2026-09-23: the [official repository](https://github.com/Friedrich-M/UniMate) still lists pretrained checkpoints as forthcoming. The available [tarn59 independent checkpoint](https://huggingface.co/tarn59/UniMate-Weights) is explicitly not the authors' checkpoint; its revision remains `31df0920ee13dad80440821b93baf223e43d4c65`, already used locally. The 53.4 GB shown on [Linzhan/UniML3D](https://huggingface.co/datasets/Linzhan/UniML3D/tree/main) is dataset storage, not new official weights.
