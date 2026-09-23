# AnyTop + Blender Robot Motion Lab

**Target platform:** Linux + CUDA GPU + Blender + agent using `mcp-for-blender`  
**Primary goal:** use AnyTop as an *organic motion prior*, then use Blender rigging, IK, retargeting, procedural timing, and agent-driven tooling to turn that motion into a four-limbed robot that can move like different species—or in ways biological bodies cannot.

> Core design principle: **do not make AnyTop responsible for everything.** AnyTop should generate biologically informed motion. Blender should provide embodiment, contacts, constraints, retargeting, rhythm, looping, and deliberate “robotic impossibility.”

---

## 1. What we are building

The end system should behave less like a normal animation library and more like a **motion instrument**:

```text
                    AnyTop
          (learned organic motion prior)
                       |
          BVH / XYZ motion + metadata
                       |
                       v
             Motion analysis layer
       contacts / phase / root / quality
                       |
          +------------+-------------+
          |                          |
          v                          v
 task-space retargeting      temporal manipulation
 end-effector paths          rhythm / loops / chaining
          |                          |
          +------------+-------------+
                       v
                Blender robot rig
            IK + joint constraints
                       |
                       v
           deliberately nonhuman logic
    role swaps / inverted joints / wall gait /
     head stabilization / phase remapping / etc.
                       |
                       v
                 baked Actions
```

The important abstraction is that the robot has **four general-purpose limbs**, not hard-coded “arms” and “legs.” A source motion can come from a biped, quadruped, flying animal, or another topology, but we will mostly transfer its *movement structure* rather than blindly copying bone rotations.

---

## 2. Keep AnyTop and Blender in separate Python environments

This is an important implementation detail.

The current AnyTop research repository was tested with **Python 3.8, Conda, Ubuntu, and CUDA**. `mcp-for-blender`, by contrast, currently requires Python >=3.10 and its maintainers recommend pinning its MCP server to Python 3.11 when environment conflicts are possible.

Do **not** try to install AnyTop dependencies into Blender's Python or into the MCP server environment.

Use three separate layers:

```text
anytop conda env       -> diffusion inference / preprocessing
Blender Python         -> rig / IK / Actions / retargeting
MCP server uv env      -> agent <-> Blender transport
```

Recommended layout:

```text
~/projects/robot-motion-lab/
├── external/
│   └── Anytop/                 # cloned upstream repo
├── generated/
│   ├── raw_bvh/
│   ├── previews/
│   ├── processed/
│   └── manifests/
├── rigs/
│   ├── robot_master.blend
│   └── source_test.blend
├── scripts/
│   ├── generate_batch.sh
│   ├── index_anytop_outputs.py
│   └── blender/
│       ├── import_motion.py
│       ├── analyze_motion.py
│       ├── retarget_taskspace.py
│       ├── contact_ik.py
│       ├── rhythm_warp.py
│       ├── loop_builder.py
│       └── bake_action.py
├── configs/
│   ├── rig_mapping.json
│   ├── gait_presets.json
│   └── quality_thresholds.json
└── experiments/
    └── ...
```

This separation prevents dependency breakage and makes the system reproducible.

---

## 3. Phase 0 — AnyTop installation and smoke test

Clone the current upstream repository:

```bash
git clone https://github.com/Anytop2025/Anytop.git
cd Anytop
```

Create the supplied environment:

```bash
conda env create -f environment.yaml
conda activate anytop
pip install git+https://github.com/inbar-2344/Motion.git
```

Download the current checkpoints and dataset dependencies:

```bash
python -m utils.download_dependencies
```

Before hard-coding checkpoint filenames, inspect what the downloader actually installed:

```bash
find save -maxdepth 2 -type f -name 'model*.pt' -print
```

This is preferable to assuming an old checkpoint name from a paper/demo command. The AnyTop repo has had checkpoint/conditioning updates, including a September 2025 preprocessing/unseen-motion fix.

### First-generation target

Start with built-in skeletons and **do not preprocess a custom robot yet**.

Use one specialist model at a time:

- `bipeds_model...`
- `quadropeds_model...`
- `flying_model...`
- `millipeds_snakes_model...`
- `all_model...` / unified model

The official syntax is:

```bash
python -m sample.generate \
  --model_path <checkpoint.pt> \
  --object_type <known_skeleton_name> \
  --num_repetitions 8 \
  --seed 100
```

Each generated sample should produce approximately:

```text
<object>_rep_<n>_#<sample>.npy   # XYZ joint motion
<object>_rep_<n>_#<sample>.mp4   # stick-figure preview
<object>_rep_<n>_#<sample>.bvh   # skeletal animation
```

### Smoke-test acceptance criteria

Do not proceed until all of these are true:

- a checkpoint loads reliably;
- CUDA inference runs;
- at least 8 samples are generated from one biped or quadruped skeleton;
- the `.mp4` previews make sense;
- the matching `.bvh` files can be opened in Blender;
- changing `--seed` produces visibly different motion.

### Nuance: clip length

Do not architect the first version around arbitrary-duration generation. The released training configs use 120-frame windows, and preprocessing splits long motion at 240 frames. The README exposes `--motion_length`, but labels it “text-to-motion only.” Treat **short fixed motion chunks** as the reliable primitive and solve long-form animation through chaining, loops, and transitions later.

---

## 4. Phase 1 — Blender MCP setup

Current `mcp-for-blender` setup on Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uvx mcp-for-blender install-addon
```

Enable the Blender add-on, then in the 3D viewport:

```text
N sidebar -> MCP for Blender -> Start MCP Server
```

The MCP project exposes scene inspection and arbitrary Blender Python execution, which is exactly what we need for building rigging/retargeting tools.

### Recommended MCP Python isolation

If the agent/client supports an MCP config, prefer:

```json
{
  "mcpServers": {
    "blender": {
      "command": "uvx",
      "args": ["--python", "3.11", "mcp-for-blender"],
      "env": {
        "UV_PYTHON_PREFERENCE": "only-managed"
      }
    }
  }
}
```

That keeps Conda/AnyTop from accidentally influencing the MCP server.

### Security nuance

`mcp-for-blender` can run arbitrary Python inside Blender. Keep the socket on `localhost`; do not expose the port over an untrusted network.

The project also provides:

```text
BLENDER_MCP_SAFE_MODE=1
```

Safe mode is useful for ordinary Blender manipulation, but it deliberately blocks direct filesystem/process/network operations. That means it will also block the convenient but dangerous idea of having Blender itself launch AnyTop with `subprocess`.

**Recommended architecture:** run AnyTop outside Blender, write BVHs to the shared project directory, and let Blender import known files. Do not make the Blender process your ML job launcher.

---

## 5. Phase 2 — Establish a repeatable BVH ingestion path

Before designing the final robot, establish a boring, reliable import pipeline.

Desired command conceptually:

```text
import_generated_motion(path)
  -> armature object
  -> action
  -> normalized scene axes/scale
  -> metadata
```

### Blender import considerations

BVH conventions differ in:

- up axis;
- forward axis;
- units;
- rest orientation;
- root position semantics;
- Euler rotation order.

Never assume imported coordinates are correct simply because the animation “moves.” Create a test scene containing:

```text
+X arrow
+Y arrow
+Z arrow
floor plane at Z=0
```

After import, verify:

1. character is upright;
2. forward motion goes through the expected scene axis;
3. feet are near ground;
4. scale is consistent;
5. root translation is not accidentally applied twice.

If Blender's BVH import operator is unavailable in the installed version, enable/install Blender's BVH import/export support first. Do not implement a custom parser until necessary.

### Agent task

Have the Blender agent build a reusable import function and test it on 5–10 AnyTop outputs, rather than writing a one-off script per file.

---

## 6. Phase 3 — Build the robot as a topology-neutral tetrapod

Do not encode “human” too deeply into the master rig.

Suggested logical hierarchy:

```text
ROOT
└── CORE / pelvis
    ├── SPINE_0 -> SPINE_1 -> CHEST -> NECK -> HEAD
    ├── LIMB_A_0 -> A_1 -> A_2 -> EE_A
    ├── LIMB_B_0 -> B_1 -> B_2 -> EE_B
    ├── LIMB_C_0 -> C_1 -> C_2 -> EE_C
    └── LIMB_D_0 -> D_1 -> D_2 -> EE_D
```

`EE_*` means **end effector**. The four limbs should have broadly comparable logical interfaces even if their physical shapes differ.

### Each limb should have

- FK controls;
- IK target;
- pole target or equivalent bend-plane control;
- configurable IK/FK influence;
- explicit joint limits;
- optional ability to disable biological joint limits;
- an end-effector contact marker;
- a role property such as `free`, `support`, `propulsion`, `manipulator`.

### Robot-specific advantages

Because this is a robot, explicitly leave room for behaviors biological rigs normally prevent:

- elbow/knee bends in either direction;
- shoulder/hip rotation beyond human limits;
- continuous head or torso rotation where visually appropriate;
- limbs changing support/manipulation roles;
- temporary body inversion;
- floor/wall/ceiling locomotion;
- locomotion where “front” changes dynamically.

Do not enable all impossible DOFs simultaneously. The robot will look random rather than alien if there is no movement grammar.

---

## 7. Phase 4 — Do task-space retargeting, not raw-angle copying

This is the core technical choice.

### Avoid

```text
source dog elbow rotation -> robot elbow rotation
```

This breaks immediately when proportions, rest axes, or topology differ.

### Prefer

Extract from the source:

```text
root trajectory R(t)
end-effector positions E_i(t)
body orientation B(t)
head direction H(t)
contact states C_i(t)
optional spine curve S(t)
```

Then solve the target robot with IK.

For each source frame:

1. evaluate source armature in world space;
2. convert joint/end-effector positions into the source-root frame;
3. normalize scale using a stable body measurement;
4. transform normalized target positions into robot-root space;
5. assign each trajectory to a robot limb according to a mapping;
6. solve the robot's IK;
7. move root/pelvis if necessary to keep active support targets reachable;
8. preserve pole-vector continuity to avoid elbow/knee flips;
9. bake the result to an Action after cleanup.

### Mapping file

Use a simple config rather than hard-coding source semantics:

```json
{
  "source": "Hound",
  "mapping": {
    "front_left": "A",
    "front_right": "B",
    "rear_left": "C",
    "rear_right": "D"
  },
  "root_scale": 1.0,
  "preserve_head": true,
  "preserve_spine": 0.6
}
```

Later, deliberately scramble it:

```json
{
  "front_left": "D",
  "front_right": "A",
  "rear_left": "B",
  "rear_right": "C"
}
```

That preserves biological *timing* while changing anatomical interpretation.

---

## 8. Phase 5 — Contact detection and IK correction

Raw diffusion motion should be treated as a proposal, not ground truth.

For candidate end effector `i`, compute:

```text
height_i(t)
velocity_i(t)
```

A first contact detector can use:

```text
contact if:
    height < H_on
    AND speed < V_on
```

Use hysteresis:

```text
enter contact: H_on, V_on
leave contact: H_off > H_on, V_off > V_on
```

This avoids rapid contact flicker.

### When a contact begins

1. store world-space contact point;
2. pin the corresponding IK target there;
3. allow the rest of the body to move around it;
4. release only after contact state ends;
5. blend in/out over a few frames rather than snapping.

### Important nuance

AnyTop's own preprocessing uses joint-name heuristics plus velocity/height thresholds for foot classification/contact detection. Those rules were designed around Truebones and may need adjustment for a custom skeleton. Use AnyTop's contact information as a clue, not as unquestionable truth.

---

## 9. Automatic quality scoring

Because generation is cheap, **oversample and reject** instead of trying to repair every clip.

For each clip calculate at least:

### Contact slip

During detected contact:

```text
slip = mean(||EE(t) - EE(t-1)||)
```

### Ground penetration

```text
penetration = sum(max(0, ground_z - EE_z(t)))
```

### Acceleration / jerk spikes

Large third derivatives often indicate ugly jitter:

```text
jerk(t) ~ x(t+3) - 3x(t+2) + 3x(t+1) - x(t)
```

Score both root and major joints.

### Reach margin

For each target position, estimate whether the robot limb is near full extension. Repeated 99–100% extension is a sign that root placement or scale needs correction.

### Joint-limit violations

Track how often the IK solution wants to leave allowed ranges.

### Periodicity score

For clips intended as loops, compare local pose features across candidate periods and measure start/end pose/velocity mismatch.

Write a manifest per clip:

```json
{
  "seed": 137,
  "model": "quadropeds",
  "source_skeleton": "Hound",
  "frames": 120,
  "fps": 30,
  "scores": {
    "contact_slip": 0.021,
    "jerk": 0.18,
    "penetration": 0.0,
    "periodicity": 0.74
  },
  "accepted": true
}
```

This will make later agent automation much more reliable.

---

## 10. Phase 6 — Use AnyTop editing for transitions, not just generation

The released AnyTop code supports two editing modes:

- `in_between`
- `upper_body`

### In-betweening

Official pattern:

```bash
python -m sample.edit \
  --edit_mode in_between \
  --model_path <biped_checkpoint> \
  --object_type <skeleton> \
  --samples '<input.npy>' \
  --num_repetitions 3
```

By default, the first 25% and last 25% are fixed and the middle 50% is generated. The boundaries can be changed with `--prefix_end` and `--suffix_start`.

Use this for:

```text
walk -> generated bridge -> crouch
crawl -> generated bridge -> upright
loop end -> generated bridge -> loop start
```

### Upper-body / subtree editing

The released mode allows a subtree rooted at one or more joint indices to be regenerated. This is useful for experiments such as:

```text
preserve locomotion + regenerate head/torso
preserve body path + regenerate arms
```

Do not assume the semantic name “upper body” means human-only; the mechanism is subtree-based.

---

## 11. Phase 7 — Loop construction

AnyTop output should not be assumed to loop naturally.

### Basic loop finder

For an accepted clip:

1. compute a pose descriptor for each frame;
2. search for frame pairs with similar pose and compatible root velocity;
3. prefer boundaries with matching contact state;
4. crop a candidate cycle;
5. remove global root displacement from the local pose loop;
6. preserve root displacement as a separate trajectory.

Conceptually:

```text
local cyclic pose(t) + continuous root translation(t)
```

This prevents the character from teleporting backward at every repeat.

### Diffusion-assisted seam repair

For a nearly good loop:

```text
end segment + beginning segment -> AnyTop in-between -> bake seam
```

Then re-run contact correction.

### Avoid perfect periodicity by default

For “organic” results, keep controlled microvariation:

- 1–3% timing drift;
- small amplitude variation;
- occasional asymmetric head/torso motion;
- phase-preserving but non-identical cycles.

The goal is a cyclic *motor pattern*, not a GIF loop.

---

## 12. Phase 8 — Motion chaining / motion graph

Build a small graph of accepted motions:

```text
idle -> walk -> trot -> run
  |       |       |
look    crouch   bound
  |       |       |
  +---- crawl ----+
```

Represent each clip boundary with:

- root velocity;
- root heading;
- contact mask;
- end-effector locations;
- compact pose vector;
- estimated gait phase.

Transition cost might be:

```text
cost =
  w_pose    * pose_difference
+ w_vel     * root_velocity_difference
+ w_contact * contact_mismatch
+ w_phase   * phase_difference
```

Low-cost transitions can crossfade directly. Higher-cost transitions can be sent through AnyTop in-betweening.

AnyTop also releases **temporal correspondence** tooling that matches similar frames across motions; treat that as an experimental aid for discovering splice points, not a requirement for the first build.

---

## 13. Phase 9 — Rhythmically cued movement

AnyTop does **not** provide a native BPM/beat-conditioning interface. Build rhythm on top of generated motion first.

### Audio/beat representation

Use a simple event timeline:

```json
{
  "bpm": 120,
  "beats": [0.0, 0.5, 1.0, 1.5],
  "subdivision": 4
}
```

Then detect source events:

- foot/hand contact onset;
- body compression minimum;
- head-direction snap;
- spine curvature extrema;
- root acceleration peaks.

### Local time warp

Do **not** simply scale the entire clip to the BPM.

Instead create a monotonic mapping:

```text
source event time s_k -> musical event time m_k
```

Interpolate smoothly between anchor pairs. This keeps the organic motion between beats while causing meaningful events to land rhythmically.

### Rhythm-coupling control

Implement:

```text
coupling = 0.0   original AnyTop timing
coupling = 0.25  subtle entrainment
coupling = 0.5   obvious rhythmic relation
coupling = 1.0   hard event lock
```

Mathematically, interpolate between original and beat-warped event times rather than between raw poses.

### Multi-rate body clocks

Useful experimental mappings:

```text
limb contacts    -> quarter notes
spine compression -> half notes
head snaps       -> syncopated eighths
small appendage  -> sixteenths
breathing/body sway -> 2–4 bar period
```

This should make the robot feel rhythmically organized without reading as a conventional dance.

---

## 14. Phase 10 — Deliberately strange robot motion operators

After retargeting works, add these as **separate, parameterized operators** rather than baking weirdness into the rig.

### A. Limb-role permutation

Change mapping over time:

```text
A B C D -> B D A C -> D C B A
```

Transition only when support remains feasible.

### B. Animal gait transposition

Map quadruped contact phases onto arbitrary robot limbs while retaining the original relative timing.

### C. Reversible joints

Allow selected joints to cross the ordinary biological bend direction. Add continuity penalties so the joint does not flip randomly every frame.

### D. Head stabilization

Hold head orientation in world space while torso/root move aggressively. Blend rather than hard-lock to avoid numerical-looking motion.

### E. Spine lead/lag

Offset spine motion temporally relative to root:

```text
spine(t) = source_spine(t - delay)
```

Use fractional-frame interpolation.

### F. Limb latency

Different limbs can have different temporal offsets while contacts remain corrected by IK.

### G. Surface-relative locomotion

Generalize ground contacts from fixed `Z=0` to a surface frame:

```text
surface point P
surface normal N
local tangent basis T1,T2
```

Then wall and ceiling gaits become the same contact/IK problem in a rotated frame.

### H. Orientation ambiguity

Let “front” switch after a maneuver. For a symmetrical robot, heading can be reassigned without turning the whole body conventionally.

### I. Freeze/burst modulation

Time-warp a segment so posture changes almost imperceptibly, then release accumulated motion over a short burst. Preserve contact constraints during the burst.

---

## 15. Phase 11 — Custom robot skeleton in AnyTop

Only after the source-motion pipeline is useful should we try zero-shot generation **directly on the robot topology**.

AnyTop supports new skeleton preprocessing from BVH.

You need:

- one or more BVHs using the robot skeleton;
- preferably a natural rest/T pose BVH;
- four named joints that define facing/orientation (rough analogs of right hip, left hip, right shoulder, left shoulder);
- a unique `object_name`.

Official pattern:

```bash
python -m utils.process_new_skeleton \
  --object_name RobotTetrapod \
  --bvh_dir assets/RobotTetrapod \
  --save_dir dataset/custom/RobotTetrapod \
  --face_joints_names <rear_R> <rear_L> <front_R> <front_L> \
  --tpos_bvh assets/RobotTetrapod/rest.bvh
```

Expected output:

```text
dataset/custom/RobotTetrapod/
├── motions/
├── animations/
├── bvhs/
└── cond.npy
```

Then generate with:

```bash
python -m sample.generate \
  --model_path <chosen_checkpoint> \
  --object_type RobotTetrapod \
  --cond_path dataset/custom/RobotTetrapod/cond.npy \
  --num_repetitions 16
```

### Critical nuance

The preprocessing pipeline was originally tailored to Truebones. The authors explicitly note that new skeletons may require changes to:

- foot-name heuristics;
- contact velocity thresholds;
- contact height thresholds;
- facing-joint choices;
- rest-pose selection.

Inspect the generated preprocessing MP4s before trusting `cond.npy`. The preview marks facing joints and detected foot contacts, making it a useful debugging step.

### Which model should condition the robot?

Test multiple priors:

```text
biped model      -> humanoid tendencies
quadruped model  -> animal support/gait tendencies
unified model    -> broader motion vocabulary
flying model     -> interesting non-grounded structure
```

This becomes an artistic control: **same robot topology, different learned species prior**.

---

## 16. Agent workflow with Blender MCP

The agent should operate as an iterative technical operator, not as an unconstrained “make it cool” generator.

### Recommended agent loop

```text
1. inspect scene
2. inspect armature names / hierarchy
3. execute one small Python transformation
4. inspect result numerically and visually
5. save checkpoint .blend
6. continue
```

The MCP project itself recommends breaking complex operations into smaller steps because long operations can time out.

### Give the agent explicit contracts

For example:

```text
Do not rename deform bones without updating rig_mapping.json.
Do not destructively bake over source Actions.
Create a new Action for every generated/processed version.
Prefix generated controls with CTRL_.
Prefix IK targets with IK_.
Prefix contact empties with CONTACT_.
Report frames with IK reach failure instead of silently clamping them.
```

### Scene organization

Use collections:

```text
SRC_ANYTOP
ROBOT_RIG
IK_TARGETS
DEBUG_CONTACTS
DEBUG_TRAJECTORIES
CAMERA_LIGHTS
```

### Action naming

```text
RAW_Hound_seed0137
RETARGET_Hound_seed0137
CLEAN_Hound_seed0137
RHYTHM120_Hound_seed0137
WEIRD_roleperm02_seed0137
```

This makes agent operations reversible and debuggable.

---

## 17. Useful Blender debug visualizations

Have the agent generate temporary visualization geometry:

### End-effector trails

Curves showing each limb's path through space.

### Contact markers

```text
green = contact
orange = transition
red = penetration / slip failure
```

### Root path

A curve for translation and small axes showing heading.

### Pole-vector diagnostics

Show elbow/knee bend planes so flips are obvious.

### Support polygon

For frames with multiple contacts, draw the convex hull of the active contact points and display the projected root/COM proxy. Do not overinterpret this as true biomechanics; it is a stability heuristic.

These debug views will be much more useful to the agent than judging everything from a rendered mesh.

---

## 18. What not to build initially

Avoid these until the baseline works:

- retraining AnyTop;
- full audio-conditioned diffusion;
- physically accurate rigid-body dynamics;
- automatic semantic text prompting;
- one monolithic Blender add-on UI;
- perfect universal retargeting across every topology;
- real-time diffusion generation during playback.

The early objective is **offline generation + fast retargeting + controllable transformation**.

---

## 19. Suggested implementation milestones

### Milestone A — Raw AnyTop

Deliverable:

- 50 generated BVHs from at least two model families;
- preview contact sheet or simple index;
- seed/checkpoint metadata.

Success criterion: at least ~50% are recognizably coherent enough to merit inspection in Blender.

### Milestone B — Blender ingestion

Deliverable:

- one agent-callable import routine;
- standardized axes/scale;
- source Actions preserved.

Success criterion: ten arbitrary generated BVHs import without manual repair.

### Milestone C — Robot rig

Deliverable:

- four interchangeable IK limbs;
- spine/head controls;
- contact markers;
- one master `.blend`.

Success criterion: the robot can be posed upright and quadrupedally using the same four limb chains.

### Milestone D — Task-space retargeter

Deliverable:

- map quadruped source to robot;
- map biped source to robot;
- configurable limb permutation.

Success criterion: changing source morphology does not require rewriting the rig.

### Milestone E — Contact cleanup

Deliverable:

- contact detector;
- IK pinning;
- slip/penetration metrics;
- baked clean Action.

Success criterion: obvious foot/hand sliding is substantially reduced without destroying the source motion character.

### Milestone F — Loops/chaining

Deliverable:

- automatic candidate cycle finder;
- root-motion separation;
- seam repair;
- clip transition graph.

Success criterion: continuous 30–60 second motion can be assembled without obvious hard cuts.

### Milestone G — Rhythm

Deliverable:

- beat-grid input;
- contact/event detection;
- local temporal warp;
- `rhythm_coupling` parameter.

Success criterion: motion clearly entrains at high coupling and remains natural at low coupling.

### Milestone H — Robot impossibility layer

Deliverable:

At least five controllable operators from:

- role permutation;
- reverse-joint bending;
- head stabilization;
- spine delay;
- limb phase offsets;
- surface-relative gait;
- freeze/burst timing;
- front/back reassignment.

Success criterion: the robot can retain coherent contact and intent while moving in a way no ordinary animal could.

### Milestone I — Direct AnyTop robot conditioning

Deliverable:

- robot BVH rest/sanity motions;
- valid `cond.npy`;
- generated robot-topology BVHs from at least unified + quadruped models.

Success criterion: compare direct robot generation against task-space retargeting and determine which produces more useful motion.

---

## 20. First experiments I would run

### Experiment 1 — Does the prior matter?

Same robot, four inputs:

```text
biped source
quadruped source
flying source
unified source
```

Use identical cleanup and compare motion character.

### Experiment 2 — Biological timing, scrambled anatomy

Take one strong quadruped clip and render:

```text
normal limb mapping
one cyclic permutation
one cross-body permutation
```

If the scrambled versions still read as purposeful, task-space transfer is working.

### Experiment 3 — Animal -> eerie humanoid robot

Use a humanoid-looking robot but retarget quadruped contact timing so hands become occasional support limbs. Preserve head orientation toward a fixed target.

### Experiment 4 — Rhythm without dancing

Use a walking/crawling motion at three coupling values:

```text
0.0
0.25
0.7
```

Only align contact events and torso compression; do not quantize every keyframe.

### Experiment 5 — No fixed ground

Take the same gait and apply it to:

```text
floor
45-degree plane
wall
ceiling
```

All contact targets should be defined in the local surface frame.

### Experiment 6 — “Nervous system remap”

During a continuous sequence, change which physical robot limb receives each source limb trajectory. Perform the swap only at a high-contact/stable pose and use diffusion/in-betweening or a procedural bridge for the transition.

---

## 21. Data to preserve for every experiment

Never save only the final Blender file.

Keep:

```text
AnyTop checkpoint
seed
source skeleton
source BVH
source NPY
robot rig revision
mapping config
contact thresholds
IK settings
rhythm settings
weirdness operators
quality metrics
resulting Action name
render/preview
```

This turns subjective visual experiments into something reproducible.

---

## 22. Recommended first-week build order

```text
DAY 1
AnyTop install -> pretrained generation -> inspect MP4/BVH

DAY 2
Blender MCP -> reliable BVH import -> debug trajectories

DAY 3
build 4-limb robot master rig -> IK/FK -> contact targets

DAY 4
quadruped task-space retargeting -> root scaling -> pole-vector stability

DAY 5
contact detection -> foot/hand locking -> quality metrics

DAY 6
biped vs quadruped sources -> limb permutation experiments

DAY 7
loop finder + simple rhythm time-warp -> render comparison grid
```

Only after this should we spend time on direct custom-skeleton AnyTop conditioning.

---

## 23. Expected failure modes

### AnyTop environment breaks on modern Linux

Because the upstream environment is old, prefer repairing the isolated Conda environment rather than modernizing the whole codebase immediately. Record every changed package version.

### Specialized checkpoint path/load problems

There have been user reports of checkpoint/path issues in specialized models. First verify actual downloaded paths and current repo state; if necessary, test the unified or biped model to isolate whether the problem is data conditioning or model loading.

### Floating/sliding contacts

Expected. Reject poor generations early and correct good ones with contact IK.

### IK limb flips

Maintain pole-vector continuity, use bend-plane memory from the previous frame, and avoid solving each frame independently with no temporal prior.

### Robot target is unreachable

Move the root/core as part of the solver. Do not simply clamp the end effector; clamping destroys the source timing and often causes pops.

### Skin deformation explodes under non-biological bending

Separate **mechanical joint motion** from organic skin assumptions. For a robot, rigid segmented geometry or carefully weighted mechanical pieces are easier than a continuous human-like skin mesh.

### Motion becomes random rather than eerie

Limit each shot/sequence to a few strong rule violations. Example:

```text
quadruped timing
+ head stabilization
+ reverse elbows
```

is more legible than enabling eight independent weirdness operators simultaneously.

### Agent makes destructive changes

Require new Actions, save checkpoints, and keep source collections locked/non-destructive.

---

## 24. Final architecture target

Long-term, the tool should expose controls like:

```text
SOURCE PRIOR       [quadruped]
SOURCE SKELETON    [Hound]
SEED               [0137]

LIMB MAP           [A<-FL B<-FR C<-RL D<-RR]
CONTACT STRENGTH   [0.85]
ROOT FOLLOW        [0.70]
SPINE TRANSFER     [0.55]
HEAD STABILIZE     [0.80]

RHYTHM BPM         [120]
RHYTHM COUPLING    [0.30]
GAIT PHASE OFFSET  [0.10]

JOINT BIOLOGY      [0.40]
ROLE SWAP          [off]
REVERSE BENDS      [0.25]
SURFACE MODE       [floor]

[GENERATE BATCH]
[RETARGET]
[CLEAN CONTACTS]
[FIND LOOP]
[BAKE ACTION]
```

AnyTop remains a **source of organic possibilities**. The interesting system is the layer around it that can reinterpret those possibilities through a robot body.

---

## 25. Source/version notes

Plan written against the repositories as they stood on **2026-09-22**.

- AnyTop official repository: https://github.com/Anytop2025/Anytop
- AnyTop project page: https://anytop2025.github.io/Anytop-page/
- AnyTop pretrained model repository: https://huggingface.co/Inbar2344/AnyTop
- Blender MCP repository: https://github.com/ahujasid/mcp-for-blender

Current upstream details worth remembering:

- AnyTop README currently specifies Python 3.8 + Conda + CUDA and includes pretrained inference, custom-skeleton preprocessing, spatial/temporal correspondence, in-betweening, subtree editing, and a Blender visualization script.
- AnyTop's preprocessing for unseen skeletons relies partly on skeleton-specific naming/contact heuristics; inspect its preprocessing visualizations.
- `mcp-for-blender` currently exposes arbitrary Blender Python execution, recommends `uv`, and supports a safe mode; keep its socket local.
- The two projects should remain separate runtime environments.

