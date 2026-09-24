# Pilgrim support-transition feasibility: first raw gate

**The biped → quadruped → biped target remains useful, but this probe did not produce an acceptable quadrupedal walking phrase.** We generated 27 new raw samples and retained the earlier successful bipedal walk as a reference. Short walking prompts still produce recognizable bipedal travel. More explicit four-legged wording does not reliably change the support pattern on the existing upright Pilgrim skeleton.

No transition sequence or finished loop was assembled: there is no accepted middle gait yet. The output is a diagnostic review, with failures retained. The next experiment in the [transition plan](unimate_support_transition_plan.md) is a versioned quadrupedal reference stance, followed by consistent conditioning/FK checks and a small matched comparison. This is a proposed next experiment, not already executed in this probe.

## Review assets

- [Combined review index](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_support_review_001/index.html).
- [Blender master: 28 raw Actions](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_support_review_001/support_review.blend).
- [18 detailed-prompt samples and diagnostics](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_support_001/review/index.html).
- [9 short-prompt samples and diagnostics](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_support_short_001/review/index.html).
- [Combined support measurements](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_support_review_001/support_analysis.json).

Live scene: `PILGRIM_UniMate_SUPPORT`. The UniMate sidebar offers the **support feasibility** selector and explicitly says the four-limb gait gate is not met. The selected `crawl / 9702` from the short-prompt batch illustrates an automated-screen false positive: it starts near the floor and then tumbles. It is not an accepted gait. The prior reference is `UNI_support_prior_biped_s9400`; all other Actions identify name variant, prompt and seed. Saved-file reopening requires running the embedded `UNIMATE_SUPPORT_UI.py` to restore the optional selector.

All clips are 60 frames at 30 fps, CFG 3. Repeated playback jumps back to frame 1. There is no generated return or seamless loop. Proxy struts display raw FK; no IK, smoothing, ground correction, retiming or collision repair was applied. Contact plots retain original ground height; pose thumbnails only align root X/Z for viewing.

## Experiment and controls

First batch: three prompts × two name schemes × three seeds (9700–9702) = 18 clips. Geometry, rest stance, scale, facing, registration motion, statistics and checkpoint are unchanged from the label study. Names are either arms/legs or front/hind legs. Identical initial noise and every non-name model condition are verified across the two naming schemes for each prompt/seed.

Detailed prompts:

- “The creature walks forward upright on its two hind legs, with its front limbs held off the ground.”
- “The creature walks forward on all four legs, alternately planting its front and hind feet on the ground.”
- “The creature crawls forward on its hands and feet with its body held low over the ground.”

Because even the explicit biped control was unreliable, a nine-clip follow-up kept front/hind names and shortened the corresponding prompts:

- “The creature walks forward slowly.”
- “The creature walks on all fours.”
- “The creature crawls forward.”

For all nine detailed-versus-short pairs, the recorded initial noise matches and only caption text/embeddings/masks differ in the sampler conditions. Thus this is a controlled wording comparison for these examples. Different prompts within a batch use successive noise draws; this is not a matched-noise comparison between walking and crawling. Both batches have `x1_known=None` and `keep_mask=None`: no starting pose or target pose is imposed.

The earlier `p07 / 9400` bipedal walk is included unchanged as a separate visual reference; it is not part of the matched controls.

## Findings

| Group | Cases | Raw observation |
|---|---:|---|
| Detailed upright walking | 6 | Poor response: floating, folded or mostly stationary examples. Travel only 0.099–0.162 m; explicit role wording is not a reliable gait control. |
| Detailed four-leg walking | 6 | Upright stepping, large arm/limb swings and airborne failures; no accepted four-limb gait. |
| Detailed hands/feet crawling | 6 | Frequently inverted/folded or nearly stationary; no accepted four-limb gait. |
| Short ordinary walking | 3 | Recognizable upright stepping and travel in all three, 1.934–4.717 m in two seconds. Sliding and penetration remain; “slowly” is inconsistent. |
| Short all-fours walking | 3 | Predominantly upright movement or airborne failure; no accepted four-limb gait. |
| Short crawling | 3 | Quiet folded pose, tumble, or initial floor approaches followed by a tumble; no accepted four-limb gait. |

All 27 six-pose/contact sheets were inspected. This is an initial visual and kinematic screen, not a blinded study. The finding is limited to this checkpoint, morphology, prompts and seeds; it does not establish that UniMate cannot animate quadrupeds generally. Earlier known-quadruped tests did show recognizable stepping.

The most instructive result is short `crawl / 9702`. A permissive screen finds 22/21/10/15 candidate stance frames for A/B/C/D, plus later lifted frames, and 4.511 m of travel. However, the supposed lifted phases include the whole creature becoming airborne and rotating. Stricter contacts find only A intervals; joint penetration reaches −0.226 m and joint-acceleration p95 is 104.21 m/s². The full phrase is rejected. This demonstrates why floor proximity, travel and lifted-frame counts alone cannot classify a four-legged gait.

The unchanged rest geometry still favors an upright interpretation in these samples, but this experiment does not isolate geometry as the cause. Names alone and these prompt changes were insufficient. A rest-stance comparison is the next independent factor to test before assembling endpoint-conditioned transitions.

## Screening limits

Strict candidates require absolute tip height below 0.06 design m and speed below 0.30 m/s. Permissive candidates use 0.12 m and 0.60 m/s; intervals must last at least three frames. The permissive walk screen requires travel above 0.15 m, at least six stance frames per limb, three lifted frames per limb above 0.17 m, and at least 30% of frames with two or more candidates. This is an intentionally loose triage filter, not a contact-force model or semantic gait classifier. It produced one false positive, rejected visually. None of the 18 requested quadrupedal/crawling samples was accepted for transition assembly.

Candidate stance intervals do not measure load, center-of-mass support or physical balance. Interlimb checks are approximate sampled centerlines, not full mechanical-body collision tests. Neither consistent bone lengths nor exact Blender reproduction demonstrates physical plausibility.

## Integrity and preservation

Every saved Action was reopened and compared against all 60 frames of its source FK. All 28 pass; maximum discrepancy is **0.000002906 design m**. Source feature hashes and prompts match, and selector next/previous round-trip checks pass. [Saved verification](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_support_review_001/saved_blender_validation.json). [Live append preservation](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_support_review_001/live_session.json).

The official-code revision and independent checkpoint are unchanged from the prior study: source `9f3076e1db482883edb6f6a37a67f521c3853278`, checkpoint SHA256 `116fbc42f2436fbd115e6558dcfa17adc3a614bf937e17bb743a6a31aadf09c7`. No training or new weights/data download was required. Raw batches, noise/condition audits, source snapshots and checksums remain on ShareDrive. The combined review references original clip files without concatenating or overwriting them.

## Follow-up

The [reference-stance experiment](unimate_stance_results.md) is complete. It generated 18 matched clips and verified both bind frames through Blender. The changed reference produces lower posture and useful partial gestures, but no accepted quadrupedal walking cycle.
