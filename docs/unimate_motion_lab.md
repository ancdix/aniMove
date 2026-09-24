# UniMate Motion Lab

The prompt interface is installed and enabled in Blender. Open the 3D Viewport sidebar with **N**, then select **Motion Lab**. In another scene, click **Open Motion Lab** (or press F3 and search for that command). Previous scenes and animations are preserved.

## Generate and compare

1. Choose a **Target**.
2. Enter a **Prompt**, such as `A dog walks forward.`, `A bird flaps its wings.`, or `An insect walks forward.` These are starting prompts, not guaranteed actions.
3. Choose **Seconds** and **Seed**, then click **Generate**.
4. The result loads and plays automatically. **New variation** generates the same prompt with a new random seed. Keep the seed unchanged to compare wording on the same target.
5. Use **Previous generations → Play selected result** to revisit an earlier output. **Show reference pose** displays the input skeleton, not a generated first frame.
6. **Save current animation .blend** writes an independent Blender file in that result's ShareDrive folder.

The camera follows horizontal root movement by default so translating clips stay readable. Turn off **Camera follows motion** for a fixed overview, or orbit the viewport normally. Camera tracking changes only the view. Use Space to pause/play and Blender's timeline to scrub. Repeating playback is a hard reset, not a generated seamless loop.

Generation runs in a separate process, leaving Blender responsive. **Cancel generation** terminates that job. Failed runs retain a status and logs. Each new result gets its own folder; existing raw outputs are not overwritten. GPU sampling has completed in roughly 14–20 seconds per tested run on this machine, including loading and decoding; duration and system load can change that.

## Available targets

| Target | Motion joints | Structure |
|---|---:|---|
| Mammal quadruped | 48 | Horizontal spine, neck/head/muzzle, ears, six-joint tail, four legs with two articulated toe branches per paw |
| Winged bird | 49 | Spine/neck/head/beak, two articulated wings with feather branches, two legs with three toe branches each, tail |
| Six-legged insect | 43 | Thorax, segmented abdomen, head/mandibles, two antenna chains, six five-joint legs |
| Pilgrim · upright | 23 | Existing verified upright Pilgrim reference |
| Pilgrim · quadrupedal | 23 | Existing verified lowered quadrupedal reference |

These are authored generic test skeletons with simple rigged body volumes, limbs and wing surfaces. They are animation blockouts, not detailed production meshes or copies of training animals. The requested generic joint-count ranges are met; no IK controls or decorative helpers are passed to UniMate. The deepest new hierarchy is nine edges, below this checkpoint's saved depth capacity. All new rigs are breadth-first ordered, Y-up/+Z-forward and normalized to a leaf-to-leaf diameter of two canonical units. Static registration clips satisfy the loader without providing motion guidance.

Every target has a real generated example in history. Successful inference and playback do not certify that every example follows its prompt well; this interface is intended to let you judge and iterate directly.

## Duration: two seconds is the native window

The installed checkpoint was trained/configured for **60 frames**, and the pipeline uses **30 fps**, so its native window is **two seconds**, not three. The interface supports **2–12 seconds** at the original frame rate. Longer clips use UniMate's stock [motion expansion](https://github.com/Friedrich-M/UniMate#motion-expansion): repeat the prompt across two-second windows with ten overlapping frames, condition each continuation on the preceding generated tail, then trim the assembled result to the requested length.

This is new generated motion, not slowed playback. The 12-second maximum is an initial interface limit, not a proven architecture limit. Longer generation can accumulate pose/root drift and discontinuities; it is marked as overlapping continuation in the panel and result metadata. Timeline markers identify where a newly generated segment starts contributing frames. Four-second output was verified both through the worker and through the actual Blender Generate button. We did not establish long-horizon physical reliability.

## What is and is not corrected

The interface uses the existing independently trained `tarn59/UniMate-Weights` checkpoint and its saved statistics. It applies stock feature decoding/FK, coordinate/scale conversion and Blender Action baking. It does **not** apply post-generation IK, foot locking, ground correction, collision cleanup, smoothing or loop repair. In longer clips, overlap constraints come from previous generated motion, not authored poses. The three authored-pose experiments remain in their separate review scenes.

Rigid links, body volumes and wing meshes are display geometry. Bone lengths are preserved by FK; this does not enforce contact, balance or collision freedom.

## Saved work

- [Standalone Motion Lab master](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001/motion_lab.blend)
- [ShareDrive results folder](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001/jobs)
- [Target definitions](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001/targets.json)
- [Blender interface source](/home/ipsedesktop/Documents/GitHub/aniMove/motion_lab/blender_ui.py)
- [Offline generation worker](/home/ipsedesktop/Documents/GitHub/aniMove/motion_lab/worker.py)

Each completed job records its prompt, target, seed, duration, checkpoint/condition/feature hashes, native versus expanded mode, original generated sample, requested-length `motion.npy`, decoded `kinematics.npz`, and logs. The optional `animation.blend` is created by the Save button. All large artifacts remain on ShareDrive; no additional weights or dataset downloads were needed.

The installed add-on is `/home/ipsedesktop/.config/blender/5.2/scripts/addons/animove_motion_lab.py`. It is enabled in saved preferences. The standalone master also contains `MOTION_LAB_UI.py` as a fallback; run it from Blender's Text Editor if the add-on is unavailable. Generation requires this machine's repository, inference environment and mounted ShareDrive; already-baked Blender animation remains playable without running the model.

## Validation

All five targets completed real inference. Their native 60-frame Blender Actions were checked against decoded FK on every frame; maximum joint discrepancy was below `4.91e-6` design m. Every visible rigid limb link was checked at frames 1, 30 and 60; maximum endpoint discrepancy was below `4.06e-6` m. A four-second continuation was loaded with 120 frames and continuation markers at 61 and 111.

Live operator checks passed for asynchronous generation, cancellation, auto-loading, autoplay, exclusive target visibility, history reload, animation saving and camera tracking. The installation preserved all 14 prior scenes, their object memberships and 441 pre-existing Actions. Request validation rejects invalid targets, duration, seeds and empty/overlong prompts; prompts are passed as JSON data, never shell commands. Existing contact/IK unit tests remain unchanged and pass.
