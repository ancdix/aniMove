# Pilgrim reference-stance experiment

Completed 2026-09-23. Changing the reference stance changes both generated posture and behavior, but this batch does **not** establish a usable quadrupedal walking cycle. The requested biped → quadruped → biped sequence remains unassembled. Two samples provide useful partial movement to review: `quadruped/walk/9700` and `quadruped/crawl/9701`.

## Review in Blender

The live scene is `PILGRIM_UniMate_STANCE`, playing `walk_9700`. In **UniMate → Reference stance comparison**, select a case or use Previous/Next. Left uses the upright reference; right uses the quadrupedal reference. Select **Input reference poses** to see the authored static inputs. They are not generated animation frames, and neither is imposed as the first frame. Playback repeats by hard reset; these are not seamless loops.

- [Saved comparison master](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_stance_001/stance_review.blend)
- [Nine paired videos and pose/contact sheets](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_stance_001/review/index.html)
- [Walking comparison, seed 9700](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_stance_001/review/walk_9700.mp4)
- [Crawling comparison, seed 9701](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_stance_001/review/crawl_9701.mp4)

The append preserved all 12 prior scenes, their object memberships, and 403 Actions; it added one scene and 20 Actions. The standalone master starts in reference-pose mode. Its embedded `UNIMATE_STANCE_UI.py` supplies the selector when executed; the live session has already registered it.

## Controlled inputs

Generated 18 raw two-second clips: two reference stances × three prompts × seeds 9700–9702, 60 frames at 30 fps, CFG 3, EMA. Prompts were “The creature walks forward slowly.”, “The creature walks on all fours.” and “The creature crawls forward.” Both variants retain the same front/hind semantic joint labels.

The authored quadrupedal reference lowers the root to 0.90 design m, tilts the core 70°, counter-rotates the neck, and analytically places A/B foretips at `(±0.72, 0, 0.95)` and C/D hindtips at `(±0.58, 0, -0.65)`, in X/Y-up/Z-forward coordinates. This is static reference construction, not gait choreography. All 23 joints, graph connections, branch geometry, bone lengths and original canonical scale remain unchanged. Maximum length change is `2.78e-16` design m. Reference tip heights are zero; this does not establish balance, load, joint limits or armor clearance.

Each reference has consistent bind offsets and rotations. Its 90-frame static registration repeat exists only to satisfy the stock loader. Free generation used `x1_known=None` and `keep_mask=None`: no motion frames, contact schedule, IK, smoothing or loop correction were supplied.

All nine upright controls reproduce the previous short-prompt outputs **exactly**, including feature SHA256. Paired noise, names, caption embeddings, topology and masks match. Actual model inputs differ only in `tpos_first_frame`, `tpos_first_frame_parents` and `offsets`. Each output is decoded and baked against its own reference; changing a displayed Blender pose alone would not be a valid test.

Uses the existing independent `tarn59/UniMate-Weights` checkpoint, not authors' official weights. Checkpoint SHA256: `116fbc42f2436fbd115e6558dcfa17adc3a614bf937e17bb743a6a31aadf09c7`; upstream revision: `9f3076e1db482883edb6f6a37a67f521c3853278`. No downloads or training were needed. Assets remain on ShareDrive.

## Observed results

All nine paired pose/contact sheets and the Blender reference render were inspected. The new-reference outputs generally look lower and more horizontally organized, but grounding and gait remain unreliable.

| Prompt / seed | New-reference travel | Visual assessment |
|---|---:|---|
| walk / 9700 | 2.46 m | Strongest translating candidate; stepping gestures, but forefoot penetration/sliding and insufficient planted intervals. |
| walk / 9701 | 0.11 m | Low, mostly stationary posture; foretip sinks and hindtips float. |
| walk / 9702 | 0.07 m | Low posture and forelimb gesture; little travel, penetration. |
| all fours / 9700 | 0.66 m | Starts lower, then floats/tumbles. |
| all fours / 9701 | 1.38 m | Limb swings without convincing floor support. |
| all fours / 9702 | 0.43 m | Floating crouched postures rather than grounded locomotion. |
| crawl / 9700 | 0.31 m | Crawling-like limb movement in the air; no sustained floor candidates. |
| crawl / 9701 | 0.31 m | Useful alternating forelimb gesture, but hindlimbs do not form a walking cycle; penetration remains. |
| crawl / 9702 | 0.13 m | Large foretip penetration, followed by floating/folding. |

For `walk/9700`, relaxed A/B/C/D stance candidates occupy only `4/0/8/9` frames. For `crawl/9701`, they occupy `10/8/55/9` frames, but C has no lift frames: this is a partial gesture, not four-limb gait. Relaxed candidates require absolute tip height below 0.12 m, speed below 0.60 m/s and an interval of at least three frames. Strict thresholds are 0.06 m and 0.30 m/s. These are kinematic triage measures, not physical contacts or proof of balance.

No new-reference sample passes the permissive walking screen. The only screen pass across all 18 is the exactly replayed upright `crawl/9702`, already rejected for tumbling in the previous study. Visual inspection, not the screen alone, determines acceptance. **Accepted quadrupedal walks: 0/9 new-reference samples.**

Median paired root-relative joint-position RMS is **0.798 design m**. Reference geometry also changes how relative rotations are interpreted, so that number alone cannot isolate the model's response. As a diagnostic, re-decoding the identical upright-generated features in the new reference still differs from actual new-reference generation by median **1.444 m** world-joint RMS. Thus this is not merely the same feature sequence displayed in a different bind pose. That control is a re-decoding, not another generated sample or evidence of learned physics.

Redundant predicted-position versus fixed-length FK disagreement has median RMS 0.185 m for upright and 0.221 m for new-reference samples. FK remains the displayed representation. These discrepancies and contact failures argue against treating the outputs as production-ready.

## Verification and decision

Reference loader/FK roundtrip error is at most `2.78e-17` canonical units. The saved Blender file reproduces every raw bone head on every frame within `2.91e-6` design m. All 22 visible links per rig were also checked at six frames for every clip, with maximum endpoint error `2.68e-6` m. Both reference poses and the selector roundtrip passed. The visible geometry agrees with the decoded output; support failures are present in the raw motion.

This completes the reference-stance gate in the [support-transition plan](unimate_support_transition_plan.md). It establishes useful posture control, not the requested walking transition. Keep the two partial candidates available for artistic review, and defer full sequence assembly.

The next bounded option is a lightly constrained, short quadrupedal phrase using explicitly chosen support poses, with an unconstrained matched control and raw results preserved. This would test whether limited guidance can repair support while retaining generated limb motion; it must be labeled as guided generation. Before combining it with upright clips, convert both into one consistent reference frame and verify FK. Direct concatenation of feature arrays from different bind references is invalid. If meaningful gait still requires authoring most of the motion, record that limitation rather than presenting it as discovered behavior.

Reproduction scripts and checksums are archived under `pilgrim_stance_001/reproduction/`; `run.json`, `analysis.json`, `stance_validation.json`, `saved_blender_validation.json`, `live_session.json` and `package_validation.json` preserve the detailed evidence.
