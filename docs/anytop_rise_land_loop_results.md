# Rise–lower–settle loop and raw landing investigation

The new `ANYTOP_Rise_Land_Loop` scene plays a six-second closed loop: four supports → upright two-support pose → lower → four supports → repeat. Raw guided AnyTop output is shown beside the corrected robot. The video contains two consecutive cycles.

[Two-cycle video](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/rise_land_bodyguided_v1/robot_loop_v1/loop_two_cycles.mp4) · [Blender file](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/rise_land_bodyguided_v1/robot_loop_v1/rise_land_loop.blend) · [Raw landing charts](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/rise_land_bodyguided_v1/landing_probe.png) · [Saved-loop validation](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/rise_land_bodyguided_v1/robot_loop_v1/saved_loop_validation.json)

## Result

Loop closure and corrected robot geometry work. Sparse guidance did not produce a reliably smooth extreme motion, and the raw samples did not demonstrate consistent landing behavior. Some generated feet slow before crossing their initial rest height; some sequences bend or show a small dip/recovery afterward. Other feet stay raised, go below their rest height, or snap when fixed context is released. These observations do not establish learned physical dynamics.

All landing measurements were computed on raw generated XYZ/features, before smoothing, IK, contact pinning or reach projection. The corrected preview cannot be used as evidence of the model's landing ability.

## Controlled comparison

Twenty completed samples use matched seeds 4200–4203:

| Checkpoint | Guidance | Samples | Run |
|---|---|---:|---|
| Quadruped | Start/top/end pose windows | 4 | `rise_land_loop_v2` |
| Quadruped | Add moving intermediate windows | 4 | `rise_land_loop_v2` |
| Unified | Start/top/end pose windows | 4 | `rise_land_unified_v1` |
| Unified | Add moving intermediate windows | 4 | `rise_land_unified_v1` |
| Quadruped | Intermediate windows plus torso guidance through frame 83 | 4 | `rise_land_bodyguided_v1` |

All runs live under `/media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated`.

Start/top/end windows are frames 1–10, 49–59 and 111–120. Additional intermediate windows are 25–30 and 78–83. Guide windows contain velocity context from a moving guide, not just isolated keyed poses. The last rest window matches the first.

Every experiment preserves an authored horizontal root path and root orientation throughout. This prevents integrated root drift and closes the loop; it is not an emergent model ability. In the strongest-guidance experiment, root height and positions of source spine joints 0, 2, 15, 16 and 17 are also prescribed through frame 83. They are released for frames **84–110 (4.15–5.5 seconds)**, the intended free landing/settling probe. The horizontal path/orientation remain prescribed during that probe.

Unknown guide values were deliberately replaced with an unrelated constant and diffusion repeated using the same seed. Output difference was exactly zero. Thus unknown procedural guide poses do not leak into the free generated motion through the mask. Fixed normalized feature error was exactly zero. Raw loop position error was about 1.32e-9 source units; endpoint velocities matched to numerical precision.

The first `rise_land_loop_v1` attempt caught a 0.00152-unit root-path closure error in the guide and was superseded before accepting samples. The corrected guide retains the first departing velocity outside the stationary prefix.

## Did intermediate guides help?

For the quadruped model, intermediate windows reduced the maximum raw step in three of four matched seeds. They did not eliminate discontinuities. The prototype rejection gate requires a largest monitored single-frame displacement below 0.5 source body lengths and a torso-length range within 0.65–1.4 times its initial length. **None of the twenty raw samples passed that gate.** No threshold was relaxed to call a raw sample successful.

The strongest torso guidance held the body path but did not sufficiently constrain the generated limb motion. Its best sample by maximum monitored step was seed 4203: approximately 0.825 body lengths in one frame, immediately after the apex pose window. That sample was chosen for the labeled cleanup preview, not accepted as a clean raw generation. The unified checkpoint did not resolve the problem.

These are small paired experiments on one authored Hound rearing guide, not a general evaluation of either checkpoint. The unusual fitted guide and its representation can contribute to failure; these results do not prove the model cannot produce good landings under other conditions.

## Landing observations

Touchdown candidates are identified relative to each foot's initial rest height, with a 0.035-body-length proximity threshold, sustained near-contact samples, and prior elevation. This is a kinematic heuristic, not measured ground force or a calibrated floor. Early contacts before the intended probe are recorded separately. Contacts that appear only in the fixed final window are not counted as generated landings.

For the strongest-guidance samples:

- Seed 4201 has both front feet cross the near-rest threshold at frames 89 and 90. Both slow beforehand, but torso compression is only about 0.012–0.013 body lengths over the following free window, with no measured rebound. The feet also move below their initial rest heights.
- Seed 4203 has a left-front event at frame 88, approximately 0.054-body-length torso drop and 0.011-body-length recovery over the measured free post-contact window. The right front foot remains above its rest plane, so this is not a coherent two-front-foot landing.
- Other seeds miss a front-foot contact or show inconsistent settling. Model contact-channel values are recorded but are not treated as probabilities or physical contact truth.

The useful conclusion is that there are occasional landing-like motion cues, but **no robust evidence of coordinated impact absorption in this test**. No mass model, friction, impulses, contact forces, center-of-mass dynamics or perturbation response was tested.

## What makes the displayed robot loop usable

The selected stronger-guidance sample receives explicitly recorded corrections:

- Five cyclic binomial smoothing passes (11-frame support).
- Rear foot anchors throughout the loop.
- Front feet released over frames 11–23 and pinned again over 96–108.
- Body-center shift toward the rear support as torso pitch increases.
- Root reach correction, outward knees, and projection of unreachable free end-effectors to the reachable shell.
- Continuous IK playback rather than interpolated FK for reliable planted contacts.

Measured maximum changes, in robot design units with 0.9-unit body length:

| Correction | Maximum |
|---|---:|
| Body correction relative to smoothed source | 0.191 |
| Foot correction including pinning/reach | 0.899 |
| Free-endpoint reach projection | 0.511 |
| XYZ smoothing displacement | 0.449 |

These remain substantial corrections. The body correction is smaller than in the earlier one-way test, but the guides, duration and task differ, so that is not a controlled claim that model quality improved. No impact squash, recoil or physics simulation was added and attributed to AnyTop.

## Saved Blender validation

The saved file was reopened and evaluated against independent solver arrays:

- Both FK and IK match numerical joints within 1e-4 units; measured maxima approximately 4.46e-7 FK and 4.11e-6 IK.
- IK loop pose error approximately 1.72e-7 units; endpoint velocity mismatch zero.
- Six samples spanning the repeated-playback seam differ by at most 1.72e-7 units.
- 477 IK poses at 80 Hz, including subframes: no conservative limb/body/head proxy intersections or clearance-margin violations; minimum clearance 0.03707 units (required 0.01).
- Rear-foot drift approximately 1.05e-6 units.
- Minimum evaluated robot mesh height approximately -5.37e-7 units, within the 1e-4 numerical floor tolerance.
- Raw displayed source points match saved XYZ within 1.63e-7 units.
- Fourteen repository tests pass, including regression checks that forced final-window contacts are not counted as generated landings.

Intended hip mounts and adjacent segments within a limb are excluded from the collision proxy. Saved motion checks do not validate arbitrary subsequent user edits or physical balance.

## Reproduction and next experiment

`run_rise_land_loop.py` creates fresh ShareDrive runs and accepts `--family quadropeds|all|bipeds`, `--body-guided`, and `--seeds ...`. `analyze_rise_land_loop.py` measures raw quality and contact cues. `prepare_rise_land_robot.py` writes a separate corrected robot directory with raw/filtered/requested/solved trajectories retained. `build_rise_land_blender.py` saves the scene and renders one and two cycles; `verify_rise_land_blender.py` checks the saved animation. `plot_landing_probe.py` plots raw data across all seeds. Exact script snapshots and checkpoint/source hashes accompany the result.

A useful next experiment is compatible reference motion containing a real rearing-and-landing segment: first test whether the editor preserves and reconnects its contact/velocity context, then progressively reduce that context. This isolates guide/representation mismatch from limitations of the motion prior. A physical-balance claim would additionally require a mass/contact model and dynamics testing.
