# UniMate / Pilgrim bring-up

Requested 2026-09-23; [original request](reference/unimate_bringup_request.txt). This is a separate raw-generation experiment. Keep AnyTop, Blender Python, and the UniMate inference environment isolated. Reuse the Pilgrim blockout, but do not reuse its authored action guidance or contact corrections for the first evaluation.

## Current state

P0–P5 completed; P6 raw comparison completed. P7 stock expansion executes, but neither of the two trials establishes the requested coherent sequence; one develops severe upward drift. P8–P9 remain deferred. See [measured results and review assets](unimate_pilgrim_results.md).

The [joint-label study](unimate_label_ablation_results.md) and [support-transition feasibility probe](unimate_support_transition_results.md) are now complete. The probe generated 27 raw samples; the four-limb gait gate remains unmet, so a biped → quadruped → biped sequence has not been assembled. The [reference-stance comparison](unimate_stance_results.md) is also complete: nine matched pairs show strong posture changes, but no accepted four-limb walking cycle. Sparse guidance was subsequently tested; see the latest outcome below.

## Gates

1. P0: clone and pin the official UniMate code; install an isolated Python 3.10 environment.
2. P1: load the requested independently trained `tarn59/UniMate-Weights` `.pt` checkpoint using stock inference and its saved training statistics.
3. P2: generate known-skeleton previews and establish recognizable text response. Opposing prompts use matched seeds. A changed array alone does not pass this gate.
4. P3: export only Pilgrim motion joints, retain semantic names, run canonicalization, and inspect facing, grounding, limb identity, ordering, pruning, and fixed-length geometry. Include a small registration clip only for the stock data loader.
5. P4: raw text-conditioned Pilgrim generation, with no IK, guide, contact correction, smoothing, or loop correction.
6. P5: only after P4, the proposed ten-prompt/eight-seed harvest.
7. P6: compare raw UniMate against raw AnyTop with declared axes, scale, timing, and morphology differences. AnyTop has no equivalent text command in the current harvest, so this is not a symmetric prompt benchmark.
8. P7: try text-sequence expansion if the earlier gates support it.
9. P8–P9: defer cleanup and finished loops until raw contribution is assessed.

Stop progression when a gate fails and preserve the evidence. Do not train. Do not substitute the paper's reported performance for evaluation of the independent checkpoint.

## Storage and setup

Code, weights, raw data, outputs, and model caches: `/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/`.

Inference environment: repository `.venv-unimate`, Python 3.10. Build cache stays on Linux in `.cache/uv` because ShareDrive is exFAT. The upstream repository is pinned at `9f3076e1db482883edb6f6a37a67f521c3853278`.

The local requirements snapshot follows upstream except that `bpy==4.0.0` is omitted: PyPI returns 404 for that release and the listed Blender wheel index returns 403. Existing background Blender handles asset export. This is an environment compatibility adjustment, not a model or sampler change. Exact installed versions, source revisions, and checkpoint/data checksums accompany the results.

## First test

Use public UniML3D Objaverse quadruped `4798d8c87a0e4ad8835217fe93ddf67b` (28 source joints), with its published motion exports, joint annotations, and captions. Its vocabulary in the user's `clips.csv` includes standing still, walking in place, running in place, and lowering its head. Process that small subset using the stock feature extractor, respecting its rejection lists.

Use independent prompt runs with the same seed and CFG to compare standing, walking, and lowering the head. Preserve untouched `(T,J,12)` features, stock FK previews, reconstructed joint positions, prompts, random seeds/repetition indices, CFG, source conditioning, and configuration changes. The released renderer uses 30 fps, so 60 frames represent two seconds; do not inherit AnyTop's 20 fps convention.

Assess visible macro-behavior plus displacement, body/head orientation, limb trajectories, velocity/acceleration, ground penetration, candidate contacts/slip, and geometry failures. Candidate contacts are not evidence of load or balance. No cleanup is allowed during this stage. Do not report a correction magnitude before an actual correction pass exists.

## Pilgrim scope after P2

Expose the existing 23 motion joints, without IK controls, poles, widgets, or decorative mechanism bones. Keep an explicit mapping between A/B/C/D and semantic arm/leg names. The checkpoint supports at most 61 padded joints; preserve its saved depth and feature dimensions.

Before sampling, show original and canonical skeletons and verify the similarity transform. Audit every retained/removed joint, chain, and facing annotation. A registration animation is loader scaffolding, not generated motion or a behavior guide; keep it short and record it separately.

The critical result is whether text creates recognizable raw macro-behavior on Pilgrim. Mesh detail and production cleanup remain deferred.

## Animal wording and sparse guidance outcome

The [matched animal-wording and sparse-guidance tests](unimate_guided_results.md) are complete: 15 new generations plus three reused controls, 18 reviewed clips. Dog/cat wording affects motion but does not establish a usable four-limb gait. Three support poses are reached accurately; intervening support remains poor and acceleration increases. Root-path guidance authors travel but does not fix contact. Full transition assembly remains deferred. The next diagnostic is the same forward-walk prompts on the existing ordinary quadruped control versus Pilgrim; no training or larger prompt sweep is required.
