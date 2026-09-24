# Pilgrim Machine — proposed execution plan

Working plan, 2026-09-23. This translates the supplied spec and reference artwork into implementation milestones. The blockout, direct-generation pilot, Devotional Hold, and a technically verified First Genuflection study are implemented; see [pilot results](pilgrim_blockout_results.md) and [loop results and control guide](pilgrim_devotional_loop_results.md). The [genuflection report](pilgrim_genuflection_results.md) records substantial authored correction: P4’s learned-primary-motion gate remains open. [Motion Harvest 001](pilgrim_motion_harvest_001.md) now supplies three generated phrases and a six-second Orient loop, with exact fitted-body retention through native phrases and measured edits. This advances primary motion discovery but does not establish new support-role transitions. Numerical targets below remain proposed production gates unless a result explicitly reports their measurement.

## Outcome

Deliver a distinctive, reusable **rigged Pilgrim Machine with usable animation**, including an editable Blender master, a finished loop, and renderable artwork. AnyTop should contribute recognizable primary movement. Curation, guidance, timing, contact correction, and secondary motion are explicit production layers whose contribution remains inspectable.

The original first-piece storyboard, **Pilgrim: First Genuflection**, is preserved as an authored study. The current direction is discovery before choreography: generate unguided motion on the Pilgrim condition, identify useful phrases, name them afterward, and develop the strongest into a finished loop. The storyboard no longer determines the next generated behavior.

**Confirmed workflow preference:** keep a simple blocked-out model through rig development, direct AnyTop testing, contact cleanup, and loop development. Detailed modeling, materials, fabric, and secondary ornament motion follow a successful blockout motion pass. The working blockout is an animated asset, not just a static modeling checkpoint.

## Source material and interpretation

- [Supplied design spec, preserved verbatim](reference/pilgrim_machine_motion_lab_spec.md).
- [Clean mechanical reference](../artwork/reference/pilgrim/01_clean_mechanical.png).
- [Weathered, cloth-bearing reference](../artwork/reference/pilgrim/02_weathered_vestments.png).
- [Original motion-lab plan](anytop_blender_robot_motion_lab_plan.md), retained as history and a source of reusable infrastructure.
- [Recent guided-loop results](anytop_rise_land_loop_results.md), documenting substantial cleanup and unsuccessful raw-quality gates.

The supplied document contains proposals and example agent commands. Those examples are design material, not instructions to execute every action now. This plan selects an order and makes implementation assumptions explicit.

## Visual design decisions for the first build

Use the first image to establish mechanical structure and the second as the finish target. The character should remain recognizable without fabric or surface detail.

Initially represent the tower and armor with simple rigid volumes, joints with spheres/cylinders, the waist ring with a low-resolution solid ring, and hands/feet with support pads. Use flat ivory, brass, and dark colors for readability. Preserve plausible thickness and articulation clearances: a stick skeleton alone cannot expose the ring and body collisions that matter here. Detailed digits, panel seams, actuators, engraving, weathering, cloth, and ornament dynamics are deferred.

| Reference feature | Implementation direction | Early check |
| --- | --- | --- |
| Tall, split ivory sensor housing with a small gold orb | Separate rigid armor sections around an articulated neck/spine; small sensor assembly | Bowing must not bend one continuous rigid armor plate |
| Broad brass waist/torso ring | Rigid assembly attached to a defined torso carrier, with clearance around the interior | Arms, thighs, and torso must clear the rim throughout kneeling and return |
| Dark exposed internal mechanism | Modular joint carriers, bearings, and simple actuator housings | Broad rotation must look mechanically supported |
| Ivory faceted limb shells and circular brass joints | Rigid bone-driven components with visible articulation gaps | No rubber-like shell deformation or panel intersections |
| Four hand-like contacts | Palm/sole support pad and initially grouped digits on every limb | Both support and raised-gesture silhouettes must read clearly |
| Halo and suspended ornaments | Independent rigid accessories with optional secondary controls | Clear the head housing during tracking |
| Worn ivory, aged brass, inscriptions, hanging strips | Material and optional cloth layer after primary motion works | Cloth must not conceal contact or clearance failures during evaluation |

The images are concept references rather than dimensioned orthographic drawings. Limb lengths, attachment locations, hidden mechanisms, and exact digit counts will be resolved in a blockout. The spec's normalized dimensions are starting ratios, not additive dimensions that already define a realizable body.

Default appearance: elongated central body, small sensor, slightly longer A/B limbs, compact lower chassis, hand-like A–D effectors, ivory/brass/dark-metal separation. A/B are the upper pair and C/D the lower pair in the initial upright stance; these labels do not prescribe permanent contact roles.

## Rig and motion architecture

Create a new Pilgrim asset. Reuse utilities from the existing lab, but do not treat the old two-link-limb robot as this finished character.

Three related representations need explicit mappings:

1. **Model skeleton:** the joint graph, rest pose, names, offsets, and feature statistics actually supplied to AnyTop.
2. **Animation/deform skeleton:** fixed-length bones driving the mechanical body, including spine, neck, and distal articulation.
3. **Control rig:** artist-facing root, torso, head, limb IK/FK, contact, and bend controls. Controls and ornament bones are not automatically model joints.

Keep the principal limb and torso joints aligned between model and deform skeletons wherever feasible. Finger curls, cloth, bearing covers, and ornaments can be separate production controls, with that distinction recorded.

Use neutral A–D naming in the Blender controls. Preserve a separate model-facing name map: joint names participate in conditioning, so replacing meaningful names with arbitrary labels is an experiment rather than harmless renaming.

For the first rig:

- ROOT/CORE, three articulated spine sections, neck, and sensor/head.
- Four limbs, each with three articulated segments and an end-effector frame.
- Independent IK/FK, end-effector orientation, contact weight, and bend controls for each limb.
- A stable distal-orientation/rest-bend strategy. A three-segment limb has more freedom than the old two-bone solver; adding one pole target is not a complete design for it.
- Head look-at or world-orientation stabilization with adjustable influence. “Head fixed” initially means stable aim/orientation, not a locked world-space head position that could force impossible spine reach.
- Contact locations on the palm/sole surface, not merely the wrist/ankle bone origin.
- Optional joint reversal only after ordinary motion works; explicit joint branches and limits prevent accidental flips. These limits are Blender constraints unless separately implemented in inference.

## Milestones and gates

### P0 — Reference blockout and pose envelope

Build a simple recognizable Pilgrim in a separate Blender scene: tower, ring, orb/halo, four limbs, palms, and minimal joint carriers. Work in declared Blender units and store the model-to-Blender scale explicitly.

Create static checks for upright, bow, one-hand support, four-contact crouch, torso turn, and return. These are authored rig tests, not AnyTop results.

Deliver: blockout `.blend`, front/side/three-quarter views, pose sheet, skeleton JSON, rest BVH, and initial collision proxies.

Gate: readable reference silhouette, a mechanically plausible articulation layout, and reachable support poses without ring/armor collisions. Resolve ring height/radius and shell segmentation here, before surface detailing.

### P1 — Direct AnyTop conditioning and motion proof

Run this on the blockout skeleton before producing the final mesh or full control system.

The local preprocessing entry point is `external/AnyTop/utils/process_new_skeleton.py`. Its `process_object` implementation builds skeleton conditions and computes mean/std from example BVH motion; supplying a static rest pose alone is not an adequate motion-statistics strategy. It also relies on facing joints and name-based foot classification.

Tasks:

1. Verify joint order, parents, rest pose, facing, contact indices, feature shapes, and finite/nondegenerate normalization. Save a condition manifest and explicit name mapping.
2. Prepare documented calibration motion on the Pilgrim graph using available generated reference motion transferred to it. Keep the calibration set separate from the later showcase guides. Validate reach and distortion before accepting its statistics. This requires no new training dataset, but the borrowed source can bias the result.
3. Run a known-skeleton control through the same export/preview path.
4. Generate a small matched pilot: four seeds each for `all`, `quadropeds`, and `bipeds`, conditioned on the actual Pilgrim skeleton. Start with the established 120-frame/20-fps workflow. Checkpoint labels are priors, not commands for particular actions.
5. Display raw XYZ, fixed-length reconstruction, and blockout playback separately. Measure fitting distortion before contact cleanup.
6. Before claiming morphology-specific adaptation, repeat selected seeds with a second documented calibration source/statistics choice. Distinguish conditioning sensitivity from newly discovered behavior.

Deliver: condition, calibration provenance, 12 direct-generation candidates, matched control, and a short comparison sheet identifying usable movement phrases and failures.

Gate: at least one useful phrase survives conversion to the actual skeleton with its timing and movement character recognizable. Model execution alone is not success. Large discontinuities, body collapse, or a need to replace most motion fail this gate.

If direct conditioning fails, diagnose normalization, naming, orientation, and reconstruction before increasing seed count. A compatible animal-source retarget can remain a visibly labeled fallback, but it does not satisfy the direct-Pilgrim-generation milestone. Report that limitation before changing the project approach.

### P2 — Working blockout rig and editable controls

Once the blockout/motion proof is useful, complete the working animation controls while retaining simple geometry: spine articulation, per-limb controls, end-effector orientation, contact targets, and head tracking. Continue changing proportions and attachment placement when motion tests expose problems. Version the skeleton and regenerate its condition when those changes affect model conditioning.

Deliver: `pilgrim_blockout_rig_v001.blend`, rest pose, control guide, pose library, and isolated rig-verification scene. Keep model definition and geometry parameters reproducible so detailed modules can later replace the blockout parts.

Gate: editable support targets and FK controls, stable joint solutions, no pose popping on IK/FK switching, rigid volumes stay rigid, and reference silhouette survives the full pose envelope. Validate evaluated blockout geometry as well as skeletal proxies.

### P3 — First usable motion loop

Finish one generated idle/settling phrase first, ideally a 4–6-second **Devotional Hold**, on the working blockout rig. This is a usable animation before visual detailing and establishes the path to the genuflection target.

Use explicit contact intervals and blended corrections. Preserve RAW, FITTED, CORRECTED, and FINAL stages, with frame correspondence through timing changes.

Deliver: editable and baked Actions, a two-cycle preview, correction report, and saved-file verification.

Gate: a clean loop, convincing planted contacts, no distracting penetration, and a traceable primary AnyTop contribution. Do not add procedural movement and describe it as model output.

### P4 — First Genuflection in blockout

Build the motion for the spec's first artwork on the same simple blockout, using useful generated phrases and sparse authored context:

1. Upright stillness and intentional weight transfer.
2. A distributed bow with sensor aim stabilized.
3. A then B hand placement, leading into four-contact settling.
4. Small torso reorientation and a readable pause.
5. A separately constructed recovery path and return to stillness.

Use in-betweening or subtree editing for bounded transitions where tests support it. Do not assume a single 14-second generation is supported or reliable: begin with established-duration windows, overlapping motion context, and explicit continuity checks when composing them. Contact schedules and guide poses are authored contributions and must be labeled.

Deliver: 8–15-second blockout looping video, pose still, skeleton/onion-skin study, trajectory visualization, and a reusable Blender Action. Review the two-cycle animation in flat materials so silhouette, contacts, and joint behavior remain easy to inspect.

Gate: the sequence reads as deliberate, restrained and ceremonial; the return is not reverse playback; important model-generated motion remains identifiable in the final result. If precise choreography replaces most of the sample, simplify the choreography or label that result as authored instead of claiming the learned-motion goal was met.

### P5 — Detailed Pilgrim asset and finished artwork

After the blockout motion passes, replace simple volumes with segmented ivory armor, brass ring and bearings, dark internal components, and articulated hand/foot modules. Preserve tested attachment points, bone lengths, contact surfaces, and clearance envelopes. Recheck animation against the evaluated detailed mesh; any geometry change that breaks the motion returns to the relevant rig/contact checks.

Add weathering, engraving, cloth, and restrained secondary motion in that order of dependency. Keep cloth switchable and keep the simple blockout available as a diagnostic view.

Deliver: `pilgrim_master_v001.blend`, editable and baked Actions, the finished **Pilgrim: First Genuflection** beauty loop, a strong still, and the diagnostic studies. The motion established in blockout must remain usable on the finished creature.

### P6 — Broaden the vocabulary

After the first finished artwork, develop processional travel, four-contact crawl, role switching, and **Change of Species**. Then test three controlled morphology variants. Add rhythm/audio as a later performance layer once contact-preserving retiming works.

The pilot and review pipeline now support a 120-sample harvest, explicitly requested after the genuflection study. Keep detailed cloth simulation and topology changes deferred until the discovered motion vocabulary is artistically convincing.

## Validation and contribution accounting

Use separate technical and artistic reviews; neither substitutes for the other.

- **Coordinate integrity:** fixed joint order, declared scale/up axis, matching frame rate, feature/XYZ/BVH consistency, and all-finite values.
- **Contacts:** palm/sole position and orientation, slip over support intervals, penetration, and smooth constraint release/engagement. A stable support silhouette is not proof of physical balance.
- **Mechanics:** fixed segment lengths, intentional joint limits, ring/torso/head clearance, and shell collisions sampled between frames. Approved adjacent mechanical interfaces need explicit exclusions.
- **Continuity:** pose, rotation, velocity, root travel, and contact state at transitions and the repeated-loop seam. Check at least two displayed cycles. A translating locomotion loop needs continuous root displacement rather than forced return to its starting world position.
- **Correction magnitude:** report root-aligned joint RMS/p95/max displacement normalized by rest-body length, absolute root drift/correction, end-effector changes, orientation differences, contact-timing changes, and any time warp. Separate fitting, smoothing, contact fixes, and artistic edits. Root alignment must not hide root corrections.
- **Authorship:** preserve guidance masks and list which joints, channels, intervals, paths, contacts, and secondary layers were prescribed. An inpainting mask's free percentage is not a defensible percentage of final artistic contribution.
- **Artistic review:** recognizable Pilgrim silhouette, readable support changes, deliberate pauses, restrained motion, and usefulness in the intended shot.

Initial engineering targets: fixed-length error below 0.1% of segment length; planted-contact drift below 0.5% of standing height per interval; penetration below 0.1% of standing height; stationary-loop seam position mismatch below 0.1% of standing height and rotation mismatch below 1 degree. Velocity continuity and the final close-up render also require inspection. Record measurements and any revised thresholds rather than silently relaxing them. There is no validated universal correction threshold for “meaningful AnyTop contribution”; use measured changes plus aligned raw/final playback to judge it.

## Storage, reproducibility, and preservation

Keep source scripts, compact rig definitions, design notes, the supplied spec, and these reference images in the repository. Store generated assets and large files under:

```text
/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/
  blender/       # Versioned master, lab, and finished scene files
  rigs/          # Rest BVH and exported skeleton/mapping snapshots
  anytop/        # Conditions, raw samples, previews, logs
  motion/        # Calibration, guides, fitted, corrected, loops, final
  metadata/      # Contacts, constraints, scores, manifests
  renders/       # Beauty, skeleton, trails, silhouettes, pose sheets
```

Reuse existing weights on ShareDrive. Every generation run records checkpoint/source hashes, skeleton/condition hash, statistics provenance, seed, timing, scale, guidance, and fitting/correction settings. Use new run directories and versioned Actions; never overwrite raw material.

Build and validate in background Blender before appending a named Pilgrim scene into the live session. Preserve existing scenes and Actions. Keep AnyTop's Python environment separate from Blender's.

## Immediate next implementation

**Review Motion Harvest 001 before more generation or detailing.** Orient, Listen, and Unfold were selected after unguided generation, with native timing and every fitted body/head frame retained. Orient also has a six-second loop: uniform half speed, a short boundary bridge, inferred contacts, and constant limb-clearance adjustments. All four assets pass saved-file contact, ground, mesh-sampling, and FK-bake checks. Review the aligned raw/final comparisons and measured corrections in the [harvest report](pilgrim_motion_harvest_001.md).

The next artistic gate is whether these three upper-body gestures feel sufficiently distinct and usable. Their labels are interpretations, not generated semantics. Genuine contact-role diversity remains open: two candidates keep C/D supports and the third has only a short threshold-sensitive D break. Use that evidence to select the next conditioning or morphology experiment; do not add a prescribed support sequence and count it as discovered. Armor, fabric, and new storyboard choreography remain deferred.
