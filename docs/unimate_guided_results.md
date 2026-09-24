# Pilgrim: animal wording and sparse support guidance

Completed 2026-09-23. Animal wording changes the motion, but neither the six new dog/cat samples nor the six guided samples establish a usable four-limb walking cycle on this Pilgrim reference. Sparse guidance reaches its authored poses accurately, while the intervening motion often remains close to the unguided behavior and introduces abrupt returns to the supplied poses. Full biped → quadruped → biped assembly remains deferred.

## Review

Live Blender scene: **PILGRIM_UniMate_GUIDED**. In **UniMate → Animal wording / support guidance**, select `words_9700` through `words_9702`, or `guidance_9700` through `guidance_9702`.

- Wording columns: **CREATURE / DOG / CAT**.
- Guidance columns: **UNGUIDED EULER / 3 SUPPORT POSES / 3 POSES + ROOT PATH**.
- [Saved Blender master](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_guided_001/guided_review.blend)
- [Six three-way videos, diagnostic sheets and authored poses](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_guided_001/review/index.html)
- [Wording comparison, seed 9700](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_guided_001/review/words_9700.mp4)
- [Guidance comparison, seed 9700](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_guided_001/review/guidance_9700.mp4)

The live append preserved 13 prior scenes, their object memberships, and 423 Actions. It added one scene and 18 Actions. The standalone master embeds `UNIMATE_GUIDED_UI.py`; execute it after reopening to restore the optional selector. Videos track root X/Z for inspection; Blender retains root travel with constant column offsets. Neither grounds the motion, cleans contact nor repairs the playback seam.

## What we prompted

Previous tests used “The creature walks forward slowly.”, “The creature walks on all fours.” and “The creature crawls forward.” The new wording comparison uses:

| Wording | Prompt | Travel in design m, seeds 9700 / 9701 / 9702 |
|---|---|---|
| Creature | The creature walks forward slowly. | 2.459 / 0.108 / 0.070 |
| Dog | A dog walks forward slowly. | 3.177 / 0.270 / 0.296 |
| Cat | A cat walks forward slowly. | 1.823 / 0.106 / 0.059 |

Same quadrupedal reference, front/hind joint labels, topology, scale, weights, 60 frames, 30 fps, CFG 3 and matched initial noise. The three creature clips are reused untouched from the stance study; six dog/cat clips are new. Only prompt wording changes, including its article. No pose guidance enters this comparison. The stock adaptive ODE sampler is unchanged.

Dog wording shifts root-relative joint positions by 0.118–0.167 m RMS versus creature; cat shifts them by 0.075–0.100 m. Seed 9700 still supplies the main translating movement, seed 9701 is mostly stationary, and seed 9702 contains asymmetric limb gestures with little travel. Dog/cat variants change limb excursions and body height but retain significant sinking, floating and weak planted intervals. The wording matters, but this small batch does not show it solving the gait problem. It does not establish that all animal wording is ineffective.

## Explicitly authored guidance

Three analytic four-tip support poses are supplied at Blender frames **1, 30 and 60**. They preserve the reference bone lengths, shift diagonal foot placements by ±0.10 m forward/back, and keep all four tips on the floor in those poses. The first and final root-relative poses match. No intervening limb pose or non-root velocity is constrained.

Two guide strengths are compared against an unguided control for seeds 9700–9702:

| Variant | Supplied values | Fraction of active joint/frame feature scalars |
|---|---|---:|
| Unguided Euler | None; all-false replacement mask | 0% |
| Three poses | Position and rotation channels at the three frames | 3.75% |
| Poses plus root | Same poses, plus root height, facing and velocity throughout | 7.93% |

The final variant explicitly authors **0.60 m forward root travel**. That travel is not credited to the model. UniMate encodes horizontal root displacement as integrated velocity, so sparse pose frames alone cannot fix world X/Z endpoints. Unconstrained entries in the guide array are filler and are ignored by the replacement mask. All masks and authored feature values are saved.

The stock guided sampler uses 50 fixed Euler steps, unlike free sampling's adaptive solver. All three guidance variants use that same stock Euler path, including the all-false-mask control. The adapter only supplies the documented known-motion tensor/mask and restores identical RNG states between variants; it does not change the network, weights or integration code. Actual initial-noise hashes and tensor conditioning hashes match within each seed.

## What guidance achieved

All six guided clips hit the supplied root-relative poses within **4.03e-6 design m**. Root-guided clips also follow the supplied path. This validates replacement and feature conversion, not natural in-betweening. The guide's independent FK roundtrip error was below `1e-12` m.

Visual inspection of all six comparison sheets shows that unconstrained frames often resume much of the original motion, with conspicuous local changes around the constrained frames. Imposing the lower root path frequently sinks otherwise similar limb motion farther into the floor.

| Across-seed median | Unguided Euler | Three poses | Poses + root |
|---|---:|---:|---:|
| Tip samples below −0.06 m in free spans | 21.2% | 27.8% | 65.6% |
| Joint acceleration p95, m/s² | 11.49 | 71.03 | 66.76 |

Free-span penetration excludes the three constrained frames and their immediate neighbors. Acceleration uses the full raw clip, intentionally exposing abrupt changes near guides. These diagnostics use design meters; they are not force measurements or a physical simulation.

None of the 18 reviewed outputs passes the permissive four-limb walking screen, and none was visually accepted as a usable quadrupedal walking cycle. That total comprises nine wording samples (three reused), three new unguided Euler controls, and six new guided outputs: **15 new generations, 18 reviewed clips**. Partial generated stepping remains visible; no authored gait or post-generation contact repair has been substituted.

## How this relates to the website

The [authors' project page](https://linzhanmou.com/unimate/) presents diverse-skeleton text generation and zero-shot editing/in-betweening. Those demonstrations support investigating this capability. They do not establish the reliability of every custom skeleton and checkpoint. I could not independently locate the exact quoted cheetah caption in the current parsed page or public interactive catalog, so this experiment makes no claim about reproducing that particular clip.

Checked 2026-09-23: the [official repository](https://github.com/Friedrich-M/UniMate) still lists pretrained checkpoints, their exact training configuration/data manifest, evaluation scripts and demo prompts as forthcoming. We use the independently trained [tarn59 checkpoint](https://huggingface.co/tarn59/UniMate-Weights). Its model card reports 120,000 training steps, 10,204 clips from 5,756 object types, and no quantitative evaluation. These are the uploader's reported training details, not performance we independently measured.

A checkpoint mismatch is therefore a plausible contributor. This study cannot separate that from Pilgrim's unusual anatomy/reference distribution or shortcomings of this sparse-guide construction. Our earlier known-quadruped control did produce recognizable walking-in-place motion, so the checkpoint is not wholly unable to generate quadrupedal movement. We should not assume that more elaborate prompting will bridge the remaining gap.

## Verification and next decision

All 18 saved Blender Actions were reopened and checked against their own decoded FK on every frame. Maximum bone-head error is `2.15e-6` m; every visible link was checked at six frames per clip, with maximum endpoint error `1.71e-6` m. Selector roundtrip and live preservation checks passed. Raw feature hashes, known tensors, masks, condition/noise audits and reproducible scripts are retained on ShareDrive.

The current diagnostic stage is complete. Before spending more time on a long transition or denser authored guidance, the most informative next comparison is the same forward-walking prompts on the existing ordinary quadruped control and Pilgrim, using the same checkpoint and solver. That can distinguish a broadly weak forward-gait result from difficulty transferring it to Pilgrim. The earlier ordinary-rig test asked for walking in place, so it is not yet that exact control. A separate artistic route is to clean a selected generated stepping phrase and measure how much motion must change; that would be an explicit production cleanup experiment, not evidence of unguided support discovery.

All large assets are on ShareDrive under `unimate/pilgrim_guided_001` and `unimate/pilgrim_animal_words_001`. No new weights or datasets were downloaded. Checkpoint SHA256 remains `116fbc42f2436fbd115e6558dcfa17adc3a614bf937e17bb743a6a31aadf09c7`; source revision remains `9f3076e1db482883edb6f6a37a67f521c3853278`.
