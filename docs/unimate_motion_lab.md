# UniMate Motion Lab

The prompt interface is installed and enabled in Blender. Open the 3D Viewport sidebar with **N**, then select **Motion Lab**. In another scene, click **Open Motion Lab** (or press F3 and search for that command). Previous scenes and animations are preserved.

New generations use **Official UniMate v2** (`Linzhan/UniMate`, `unimate_uniml3d_f60_v2`, step 100,000). The panel shows the generation model and the model that produced the currently viewed animation. History labels distinguish official outputs from **Independent v1** results; old animations retain their original provenance.

## Generate and compare

1. Choose a **Target**.
2. Enter a **Prompt**, such as `An object walks forward on all fours.`, `An object flaps its wings.`, or `An object walks forward on six legs.` These follow the official model card's motion-only wording; they are starting prompts, not guaranteed actions.
3. Choose **Seconds** and **Seed**, then click **Generate**.
4. The result loads and plays automatically. **New variation** generates the same prompt with a new random seed. Keep the seed unchanged to compare wording on the same target.
5. Use **Previous generations → Play selected result** to revisit an earlier output. **Show reference pose** displays the input skeleton, not a generated first frame.
6. **Save current animation .blend** writes an independent Blender file in that result's ShareDrive folder.

For either **Pilgrim** target, **Pilgrim display** offers **Skeleton / Model / Both**. Model shows the existing ivory/brass mechanical blockout on the generated animation; Both draws the colored skeleton in front of the model in the viewport. This works with previous generations and requires no new inference. The display setting is retained when loading another clip. Saved Blender files include the model geometry and its embedded source data.

The overlay reuses 64 rigid parts from the verified Pilgrim blockout, bound to the same 23 motion joints. Its bind geometry is adjusted for the quadrupedal reference pose; it adds no motion joints, IK, grounding or collision correction. Model volume can therefore reveal floor penetration or self-intersection that was less obvious in the skeleton. Overlay checks on both references confirmed zero joint-motion change and mesh attachment errors below `5e-7` design m; see `pilgrim_overlay_validation.json` in the ShareDrive lab folder.

The camera follows horizontal root movement by default so translating clips stay readable. Turn off **Camera follows motion** for a fixed overview, or orbit the viewport normally. Camera tracking changes only the view. Use Space to pause/play and Blender's timeline to scrub. Repeating playback is a hard reset, not a generated seamless loop.

Generation runs in a separate process, leaving Blender responsive. **Cancel generation** terminates that job. Failed runs retain a status and logs. Each new result gets its own folder; existing raw outputs are not overwritten. The worker requires CUDA and reports a driver/GPU error if unavailable; there is no automatic CPU fallback. Status and result metadata identify CUDA and the GPU name. The earlier 14–20 second measurements were GPU runs with the independent checkpoint.

## Available targets

| Target | Motion joints | Structure |
|---|---:|---|
| Mammal quadruped | 48 | Horizontal spine, neck/head/muzzle, ears, six-joint tail, four legs with two articulated toe branches per paw |
| Winged bird | 49 | Spine/neck/head/beak, two articulated wings with feather branches, two legs with three toe branches each, tail |
| Six-legged insect | 43 | Thorax, segmented abdomen, head/mandibles, two antenna chains, six five-joint legs |
| Humanoid | 35 | Two arms, two legs, spine/head and simplified three-digit hands; low-poly mannequin |
| Humanoid · four arms | 55 | Two shoulder pairs, four arms, two legs; distinct colors for each arm |
| Pentaped · radial | 31 | Pentagonal body, central head stalk, five radial legs at 72-degree spacing with broad feet |
| Pentaped · rear tripod | 31 | Three hind support legs, rising torso/head and two longer front arms with ground-reaching hands |
| Pilgrim · upright | 23 | Existing verified upright Pilgrim reference |
| Pilgrim · quadrupedal | 23 | Existing verified lowered quadrupedal reference |

The humanoids use low-poly rigid mannequin parts, including torso, head, limb segments, hands and feet. Both arm pairs on the four-arm target receive ordinary left/right arm and hand semantic labels, with unique bone identifiers for the lower pair. This exposes four independent arm chains to UniMate; it does not guarantee independent text control of each pair. Start with `An object walks forward.` or `An object raises its arms.`

These are authored generic test skeletons with simple rigged body volumes, limbs and wing surfaces. They are animation blockouts, not detailed production meshes or copies of training animals. The requested generic joint-count ranges are met; no IK controls or decorative helpers are passed to UniMate. The deepest new hierarchy is nine edges, below this checkpoint's saved depth capacity. All new rigs are breadth-first ordered, Y-up/+Z-forward and normalized to a leaf-to-leaf diameter of two canonical units. Static registration clips satisfy the loader without providing motion guidance.

The two pentapeds are morphology experiments with five separate limb chains and colored low-poly body parts. Their ground-level reference endpoints establish a starting geometry, not a physical support constraint. Walking and body-lowering samples are provided for each; generation does not enforce balance, joint limits, ground contact or collision clearance.

Every target has a real generated example in history. Successful inference and playback do not certify that every example follows its prompt well; this interface is intended to let you judge and iterate directly.

## Duration: two seconds is the native window

The installed checkpoint was trained/configured for **60 frames**, and the pipeline uses **30 fps**, so its native window is **two seconds**, not three. The interface supports **2–12 seconds** at the original frame rate. Longer clips use UniMate's stock [motion expansion](https://github.com/Friedrich-M/UniMate#motion-expansion): repeat the prompt across two-second windows with ten overlapping frames, condition each continuation on the preceding generated tail, then trim the assembled result to the requested length.

This is new generated motion, not slowed playback. The 12-second maximum is an initial interface limit, not a proven architecture limit. Longer generation can accumulate pose/root drift and discontinuities; it is marked as overlapping continuation in the panel and result metadata. Timeline markers identify where a newly generated segment starts contributing frames. Four-second output was verified both through the worker and through the actual Blender Generate button. We did not establish long-horizon physical reliability.

## What is and is not corrected

The interface uses the authors' official v2 EMA weights and their matching saved statistics. It applies stock feature decoding/FK, coordinate/scale conversion and Blender Action baking. It does **not** apply post-generation IK, foot locking, ground correction, collision cleanup, smoothing or loop repair. In longer clips, overlap constraints come from previous generated motion, not authored poses. The three authored-pose experiments remain in their separate review scenes.

Rigid links, body volumes and wing meshes are display geometry. Bone lengths are preserved by FK; this does not enforce contact, balance or collision freedom.

## Saved work

- [Standalone Motion Lab master](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001/motion_lab.blend)
- [ShareDrive results folder](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001/jobs)
- [Target definitions](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001/targets.json)
- [Blender interface source](/home/ipsedesktop/Documents/GitHub/aniMove/motion_lab/blender_ui.py)
- [Offline generation worker](/home/ipsedesktop/Documents/GitHub/aniMove/motion_lab/worker.py)

Each completed job records its prompt, target, seed, duration, checkpoint/condition/feature hashes, native versus expanded mode, original generated sample, requested-length `motion.npy`, decoded `kinematics.npz`, and logs. Official jobs additionally record the model repository/revision, code revision, model configuration and normalization hashes, EMA usage and compute device. The optional `animation.blend` is created by the Save button. All large artifacts remain on ShareDrive.

The active model is pinned in [configs/motion_lab_model.json](/home/ipsedesktop/Documents/GitHub/aniMove/configs/motion_lab_model.json). Weights live in `unimate/weights_official_v2` at Hugging Face revision `387a344c3031299bc25fcbef35d36bd186d5afe7`; inference uses the separate `unimate/UniMate_official_v2` checkout at `5d6aabedd947297b5ba6706d8e9113e68c0c3e4f`. Each generation verifies the checkpoint, config and statistics hashes and checks the code revision. The former `weights` and `UniMate` directories are preserved for earlier experiments. This upgrade requires no full training dataset download.

The installed add-on is `/home/ipsedesktop/.config/blender/5.2/scripts/addons/animove_motion_lab.py`. It is enabled in saved preferences. The standalone master also contains `MOTION_LAB_UI.py` as a fallback; run it from Blender's Text Editor if the add-on is unavailable. Generation requires this machine's repository, inference environment and mounted ShareDrive; already-baked Blender animation remains playable without running the model.

## Validation

The following original validation describes the independent-checkpoint baseline. The official upgrade has a separate `official_v2_validation.json` report in the ShareDrive lab folder.

Official-v2 GPU validation (2026-09-29): NVIDIA driver `580.178.04` restored CUDA on the RTX 4090 under kernel `7.0.0-34-generic`. All five targets completed generation with official EMA weights and matching normalization statistics. Four two-second samples took 14–16.4 seconds each; the four-second mammal continuation took 22.6 seconds, including model loading and decoding. All 360 generated frames were checked against Blender bone positions; maximum discrepancy was below `4.44e-6` design m. Legacy history, target switching, installed add-on source and standalone saving also passed. See `official_v2_saved_validation.json` for the full saved-file report. Generation now requires CUDA; the temporary CPU fallback was removed.

The actual live Generate operator then completed a second four-second CUDA run in 19.6 seconds, automatically loaded it and started playback. Its full 120-frame bake, history reload, all target visibility switches and Save operator passed. The updated master and installed add-on include the official model label and embedded interface. `official_v2_validation.json` records the live checks and all six GPU jobs. These validate integration and motion preservation, not artistic quality or physical correctness.

All five targets completed real inference. Their native 60-frame Blender Actions were checked against decoded FK on every frame; maximum joint discrepancy was below `4.91e-6` design m. Every visible rigid limb link was checked at frames 1, 30 and 60; maximum endpoint discrepancy was below `4.06e-6` m. A four-second continuation was loaded with 120 frames and continuation markers at 61 and 111.

Live operator checks passed for asynchronous generation, cancellation, auto-loading, autoplay, exclusive target visibility, history reload, animation saving and camera tracking. The installation preserved all 14 prior scenes, their object memberships and 441 pre-existing Actions. Request validation rejects invalid targets, duration, seeds and empty/overlong prompts; prompts are passed as JSON data, never shell commands. Existing contact/IK unit tests remain unchanged and pass.


## Essential Motion Survey 001 — unattended run

The 2026-09-30 survey runs all 40 prompts across all nine targets with four seeds (12001–12004): 1,440 independent two-second clips. Its prompt matrix is in `configs/essential_motion_survey_001.json`. It executes the entire queue without review gates, one GPU call at a time, ordered by seed → prompt → target. Failed clips receive one automatic retry after the initial pass. Completed clips are recovered after interruption and never deliberately regenerated. The worker, model specification, target definitions, condition hashes and prompt matrix are captured with the survey.

Output lives at `/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001/surveys/essential_motion_001_20260930`. Each raw generation also has a normal Motion Lab job folder and can be loaded through the existing history. `state.json`, `runner.log` and `web/index.json` record progress and any failures; final state is either `complete` or `complete_with_failures`, never silently successful after missing clips.

Open [the local review page](http://127.0.0.1:8766/) to compare four synchronized seeds using the actual exported low-poly blockout geometry. Select a creature and prompt; drag to orbit, scroll to zoom, scrub or pause all views together. Rate action match, physical plausibility and keep/cleanup/reject independently; ratings are saved in `ratings.json` on ShareDrive and can be exported. Anatomy-specific prompts on other body plans are explicitly marked experimental. No ratings or motion-quality verdicts are inferred automatically. Camera following changes only the view; playback wraps with a hard reset.

The browser review and generation do not require Blender to be open. **Open in Blender** requires the Motion Lab add-on and Blender MCP server running; it loads the selected raw result without regenerating it.

The user services are `animove-essential-motion-001.service` (GPU run) and `animove-motion-review-001.service` (loopback-only web review). The run has automatic restart on process failure and a temporary `sleep:idle` inhibitor that is released when the run ends. Keep the machine powered on. Transient services are not boot-persistent; after a reboot, the saved runner can resume using the same survey root. A process restart does not erase successful clips. Do not alter the target definitions or checkpoint during the survey.

Implementation: `motion_lab/survey.py`, `survey_server.py`, `export_survey_models.py` and `survey_web/`. Coverage, interrupted-result recovery and bounded retry behavior are tested in `tests/test_survey.py`. `verify_survey_models.py` checks the browser bind geometry against Blender evaluated meshes on generated motion for every target; all nine passed at frame 30 with maximum discrepancy below 9e-6 design m (`viewer_geometry_validation.json`). The web viewer vendors Three.js 0.160.0 under its MIT license and does not require an external CDN at review time.
