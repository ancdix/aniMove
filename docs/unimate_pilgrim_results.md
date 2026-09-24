# UniMate / Pilgrim raw evaluation

This experiment follows the [requested bring-up](reference/unimate_bringup_request.txt) and [gated plan](unimate_pilgrim_plan.md). It evaluates what text plus Pilgrim morphology generates before Blender cleanup. AnyTop outputs and environments remain separate. No training was performed.

## Result and review artifacts

**P0–P5 completed: the independent checkpoint produces raw text-conditioned motion on the 23-joint Pilgrim skeleton, and all 80 requested samples are preserved. P6 raw comparison is complete. P7 runs, but the two expansion trials do not establish a dependable four-stage behavior. P8–P9 cleanup and final animation are deliberately deferred.**

- [Offline gallery: all 80 clips, ten video grids, pose/contact atlases](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_harvest_001/review/index.html)
- [Walking prompt: all eight seeds](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_harvest_001/review/p07_grid.mp4)
- [Twisting prompt: all eight seeds](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_harvest_001/review/p06_grid.mp4)
- [Raw Blender master](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_harvest_001/unimate_raw_master.blend)
- [Common-view AnyTop / UniMate examples](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_harvest_001/review/anytop_unimate_raw.mp4)
- [Two raw expansion trials](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_expansion_001/expansion_comparison.mp4)

Blender now contains `PILGRIM_UniMate_RAW`, with `UNI_p07_s9400` playing. Open the **UniMate** sidebar tab to choose any of the 80 Actions. The previous nine scenes and 265 Actions were preserved. On reopening the standalone master, run the embedded `UNIMATE_REVIEW_UI.py` text to restore that optional sidebar, or use the Action Editor directly. There are no IK constraints. All 4,800 saved poses were reopened and checked against source FK; maximum joint-position discrepancy is **2.61e-6 design m**. The visible struts are an exact skeleton review proxy, not a detailed or production-ready mesh. Repeating playback has a hard reset, not a generated loop seam.

## What the 80 samples actually show

Each prompt has eight seeds. The observations below combine four-pose screening of every clip, raw trajectories and orientation measurements; this is an initial review, not a blinded perceptual study.

| Prompt | Raw result |
|---|---|
| Stand / weight shift | Mostly quiet, upright variants; median root travel 0.095 m. Several start or remain above the floor. |
| Slowly lower body | Unreliable temporal lowering: median root change **+0.016 m**, with a minimum of only −0.041 m. One seed starts in an inverted/folded pose rather than performing a lowering transition. |
| Crouch and advance | Some compression and stepping, but not a reliable low four-limb gait. Median travel 0.468 m; one initial airborne pose is a failure. |
| Raise torso | Modest, relatively consistent straightening: root rises 0.040–0.135 m in all eight clips. |
| Extend one front limb to ground | Weak response; mostly standing/straightening. No A/B contact candidates satisfy the common comparison thresholds. |
| Twist while standing | Clear turning in five seeds, quiet variants in three. Median torso-yaw range **83.8°**; extreme turns can be abrupt. |
| Walk forward slowly | Strongest locomotion result: median travel **2.923 m** in two seconds (range 0.316–4.482 m). The generated gait reads predominantly as bipedal arm/leg motion. “Slowly” is inconsistent. |
| Lower head and cautiously advance | Several head/body bows, but limited travel (median 0.177 m) and inconsistent combined action. |
| Stumble backward and recover | All eight lose at least 0.9 m of root height; falls/collapses dominate, without the requested recovery by frame 60. |
| Lower and remain still | Mixed: standing, initial lowered poses, straightening, and isolated larger collapses. No reliable sequence. |

`p07/9400` is an illustrative walking source (2.075 m travel, minimum joint −0.032 m). `p06/9400` gives a 95.9° turn with little translation, and `p04/9406` suggests a small unfolding gesture. These are candidates for later artistic review, not accepted production clips. Of the full batch, 20/80 have joints below −0.06 m; 37/80 trigger at least one approximate interlimb centerline-overlap flag. Flags are deliberately exposed rather than solved.

A/B semantic arms and C/D legs strongly influence how this creature reads. The experiment demonstrates text-driven motion on custom proportions and topology, but does **not** demonstrate four equivalent hands/feet, reliable support-role changes, landing physics, or a finished Pilgrim movement language.

## Raw AnyTop comparison

Both cohorts use the first two seconds, native rates (AnyTop 20 fps / UniMate 30 fps), the same 23-joint correspondence, design-meter scale and declared floor. No per-clip grounding, retarget fitting or cleanup is applied. The AnyTop raw source positions can violate the target rest lengths; UniMate uses stock FK with fixed lengths. These are representation differences, not evidence of learned physics. The video holds source frames at their native sample times in a 60 fps presentation, without motion interpolation.

| Across-clip median | AnyTop, 120 raw samples | UniMate, 80 raw samples |
|---|---:|---:|
| Root travel / 2 seconds | 0.048 m | 0.177 m |
| Lowest joint height | +0.006 m | −0.017 m |
| Joint acceleration p95 | 3.61 m/s² | 9.45 m/s² |
| Near-floor tip speed | 0.167 m/s | 0.269 m/s |
| Maximum rest-length discrepancy | 0.371 m | numerical noise |

Near-floor speed is a slip warning proxy, not measured foot slip under known planted contact; clips with no near-floor joints are omitted from that statistic. Contact candidates require |height| < 0.06 m, speed < 0.30 m/s and duration ≥0.1 s, without filtering. Collision screening uses sampled centerlines with a 0.04 m radius, omits the torso/mesh and is not a collision certificate. Full definitions and ranges are in [raw_comparison.json](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_harvest_001/raw_comparison.json).

UniMate produces much more recognizable prompted travel and turning. It also produces abrupt and physically unusable failures. AnyTop's current harvest supplies subtler, often quieter gestures, and was unguided, so it cannot be assigned an equivalent text-adherence score. Organic quality and artistic distinctiveness remain selection judgments. **Correction required is unmeasured**: this phase intentionally contains no cleaned result, so there is no defensible raw-to-final RMS or claim that UniMate needs less correction.

## Text-sequence expansion

Two stock runs, seeds 9500/9501, chain “stand still → slowly lower → forward on all four limbs → slowly rise.” Four 60-frame segments share ten generated overlap frames, producing 210 frames / seven seconds. The clamp comes only from each preceding generated segment; there is no authored choreography or ground-truth pose sequence.

The mechanism executes, but the behavior gate fails in these trials. Seed 9500 shifts/compresses and moves its limbs with only 0.134 m net root travel; it does not clearly perform the requested four-limb advance. Seed 9501 develops severe upward drift in the final segment, ending with its root at **8.20 design m**, about **6.92 m above its initial height**. This is preserved in the [pose/seam diagnostic](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_expansion_001/expansion_poses.png). An overlap clamp alone does not guarantee physical continuity or semantic adherence.

The useful next decision is whether to retain the current arm/leg interpretation. If Pilgrim must move as a four-support creature, first test a small matched-noise naming/rest-pose ablation, recording each morphology variant. If the bipedal reading is acceptable, the walking and turning sources are concrete candidates for a separate, measured cleanup pass. Neither choice needs more mesh detail yet.

## Provenance and environment

- Official [UniMate source](https://github.com/Friedrich-M/UniMate): commit `9f3076e1db482883edb6f6a37a67f521c3853278`.
- Independent [tarn59/UniMate-Weights](https://huggingface.co/tarn59/UniMate-Weights): revision `31df0920ee13dad80440821b93baf223e43d4c65`, `.pt` step 120000, EMA inference. This is not the authors' official checkpoint and the paper's scores do not establish its performance here.
- Checkpoint SHA256: `116fbc42f2436fbd115e6558dcfa17adc3a614bf937e17bb743a6a31aadf09c7`.
- UniML3D subset revision: `c2b7ad6926b03dd72fae7934656dd4d4b9056029`.
- `google/flan-t5-base` revision: `7bcac572ce56db69c1ea7c8af255c5d7c9672fc2`; safetensors SHA256 `1dfb70afdcedceb9f9fae2f9b68e004ad934361fb35b9b2bd50b45ea90790fc8`.
- Isolated `.venv-unimate`: Python 3.10.20, PyTorch 2.5.1+cu124, Transformers 5.16.1, NumPy 2.2.6. `pip check`, CUDA matrix multiplication and stock EMA loading passed on the RTX 4090.
- All source data, weights, offline model cache and outputs are under `/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate`. Installed-version lock, hashes, commands, seeds and configs accompany the run.

Upstream `bpy==4.0.0` was unavailable from the listed indexes (404/403). Custom-asset processing therefore uses existing Blender 5.2.2 / Python 3.13 with a separate compatible dependency directory, never the inference environment's Python binaries. The adapter discovers Blender 5 layered Actions, disables pruning of the explicitly selected motion skeleton and retains the quiet registration clip (`activity_threshold=0`). Upstream source, model, feature mathematics and sampler are unmodified.

## Known-skeleton gate

Public Objaverse quadruped `4798d8c87a0e4ad8835217fe93ddf67b` retains 28 joints. The stock feature extractor processed its small published subset; this did not require downloading a full training dataset. The smoke test invoked `python -m unimate.inference.sample` directly. A subsequent observation-only wrapper recorded initial noise hashes without changing random draws or sampling.

Twelve samples compare still, walking in place and head lowering with four matched seeds (9200–9203). Identical initial-noise hashes across prompts were verified. Standing remains quiet and walking produces stepping in all four seeds: mean root-relative effector motion RMS is 0.00844 versus 0.13123 canonical units. Head lowering is less reliable, sometimes producing crouching or rearing instead. This passes text response, not universal prompt fidelity or contact quality.

[Known-rig comparison video](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/known_text_001/prompt_comparison.mp4).

## Pilgrim canonicalization

The inference asset contains exactly the existing 23 meaningful motion joints. A/B are semantic arms and C/D are semantic legs; no IK targets, controls or decorative helpers enter conditioning. The mesh is a rigid strut proxy, not the detailed concept-art creature. This semantic choice may bias generated behavior toward arm/leg roles; four interchangeable load-bearing limbs are not established by this test.

A 90-frame loader registration clip supplies tiny torso sway and lateral motion. It is not an authored behavior guide: free sampling passes no known motion or keep mask. The saved model config conditions topology from the T-pose.

The transform is `(source_Y_up - [0, 0.06, 0]) * 0.45726488446964497`; +Y up and +Z forward survive. All joint names, parent chains, A/B/C/D identities and facing annotations were checked. Source-geometry discrepancy is below 5.6e-7 canonical units; reimported GLB and FBX discrepancies are below 4.4e-7. No joints were pruned. [Round-trip overlay](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_canonical_v002/roundtrip.png).

Decoder detail: generated rotations are T-pose-relative. FK offsets must be derived from `tpos_first_frame`, as the stock loader does; exported bone-local `cond['offsets']` are not interchangeable. Identity-pose and translation tests pass. Early derived analysis used the wrong convention; it was replaced. Stock samples and stock preview videos were unaffected.

## Initial Pilgrim gate

Six matched-noise samples (p01 weight shift, p02 lower, p07 walk; seeds 9300–9301) establish raw custom-skeleton text response. Walk travels 5.58 m and 2.52 m in two seconds, whereas weight-shift travel is 0.046 m and 0.129 m. Body lowering is weak and seed-dependent. “Slowly” is not reliably respected. These are original design units, not a measured physical creature scale.

[Matched Pilgrim comparison](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_text_probe_001/prompt_comparison.mp4).

## Reproduction

Use `scripts/setup_unimate.sh` and `scripts/stage_unimate_assets.py` for the separate environment and pinned assets. The checkpoint's saved statistics and dimensions are retained (61 padded joints, 60 frames, 12 features, CFG 3). Runs only alter dataset selection/path and output paths. Existing run directories are protected against overwrite.

The following repository scripts implement the pipeline:

1. `run_unimate_known_test.py`: stock smoke or matched-noise prompt tests.
2. `export_pilgrim_unimate.py`, `preprocess_pilgrim_unimate.py`, `verify_pilgrim_unimate_asset.py`: registration proxy, upstream canonicalization and asset round-trip checks.
3. `run_unimate_harvest.py`: ten requested prompts × eight seeds 9400–9407.
4. `analyze_unimate_raw.py`: stock FK decoding, positions, global quaternions, velocities, accelerations and candidate contacts.
5. `compare_unimate_anytop.py`, `package_unimate_review.py`: common-unit raw comparison and review gallery.
6. `build_unimate_review.py`, `verify_unimate_review.py`, `append_unimate_live.py`: raw native Actions, saved-file verification, non-destructive live append.
7. `run_unimate_expansion.py`: stock text-sequence extension using generated overlap only.

The harvest uses successive noise draws within each seed's ten-prompt run, with hashes and draw indices recorded. It is not a matched-noise prompt benchmark; the earlier known-rig and Pilgrim probes provide that controlled comparison.
