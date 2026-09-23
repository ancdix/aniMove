# Pilgrim Machine — Creature Design / Motion Lab Spec

## 0. Project intent

**Pilgrim Machine** is a four-limbed robotic creature designed as both:

1. an **art object / character**, and
2. a **motion experiment** for learned and procedural animation.

The goal is not simply to make a robot that walks. The goal is to create a machine whose **movement language feels ritualistic, devotional, nonhuman, and physically intentional**.

Primary visual/motion themes:

- processional
- ceremonial
- restrained
- strange but coherent
- biological hesitation inside a mechanical body
- limbs that can change role
- posture that can move between humanoid and quadrupedal
- motion that can be looped, performed, and used in finished visual work

The character should be useful for:
- short looping animations
- music / audiovisual pieces
- concept-art studies
- motion-trail renders
- still pose sheets
- interactive or generative performance
- later game / installation use

---

# 1. Core identity

## One-sentence character description

> A ritual machine that walks upright like a pilgrim, periodically kneels, re-anchors itself with its arms, and reorganizes its body as though changing between worship, locomotion, and maintenance.

## Movement identity

The Pilgrim Machine should feel like it has a **purpose**, but not necessarily a human one.

Preferred motion qualities:

- deliberate weight transfer
- long pauses between actions
- asymmetric transitions
- controlled collapse
- slow bowing / kneeling
- occasional sudden reorientation
- hands becoming support contacts
- torso rotating independently from the lower body
- head / sensor module remaining fixed on a target while the body reorganizes
- motion that appears "remembered" rather than purely reactive

Avoid:

- generic humanoid walk-cycle behavior
- comedy-robot stiffness
- constant fidgeting
- overly smooth "CG creature" motion
- excessive random limb flailing
- motion that reads as broken rather than intentional

---

# 2. Body-plan philosophy

Use a **neutral four-limb topology** rather than a strictly humanoid naming scheme.

Conceptually:

```text
                  HEAD / SENSOR
                       |
                    NECK
                       |
                  SPINE_3
                 /       \
             LIMB_A     LIMB_B
                    |
                  SPINE_2
                    |
                  SPINE_1
                 /       \
             LIMB_C     LIMB_D
                    |
                   ROOT
```

Each limb should use a common abstract structure:

```text
attachment
   |
proximal
   |
middle
   |
distal
   |
end_effector
```

This allows the same body to support multiple interpretations:

```text
UPRIGHT MODE

A = left arm
B = right arm
C = left leg
D = right leg
```

```text
QUADRUPED / PILGRIM MODE

A = front-left support
B = front-right support
C = rear-left support
D = rear-right support
```

```text
RECONFIGURED MODE

A = anchor
B = manipulator
C = propulsion limb
D = stabilizer
```

The rig should not assume that "arm" and "leg" are permanent identities.

---

# 3. Suggested morphology

This section can be adjusted to match the existing artwork.

## Default proportions

Start with a readable silhouette:

- torso: narrow and vertically elongated
- pelvis / lower chassis: compact
- front limbs: slightly longer than rear limbs
- neck: moderately long
- head / sensor pod: small relative to body
- hands / feet: visually similar enough that limb-role switching feels plausible
- shoulder spacing: wider than pelvis
- distal limbs: slightly long and thin
- central body: heavier visual mass than limbs

Suggested normalized proportions:

```text
overall height          = 1.00
torso length            = 0.32
neck length             = 0.12
head height             = 0.08

front upper segment     = 0.22
front lower segment     = 0.24
front distal segment    = 0.10

rear upper segment      = 0.20
rear lower segment      = 0.22
rear distal segment     = 0.10
```

These do not need to be anatomically realistic.

---

# 4. Joint freedoms

The artistic advantage of the machine is that joints do not need to obey human anatomy.

## Baseline joint types

### Root / pelvis
- translation: free
- yaw: free
- pitch: moderate
- roll: moderate

### Spine
Use 3–5 articulated segments.

Each segment should allow:
- pitch
- yaw
- roll

Prefer distributed motion over one giant torso joint.

### Neck / head
Allow:
- large yaw
- moderate pitch
- moderate roll

Optional:
- near-continuous yaw if the visual design supports it

### Limb proximal joints
Prefer approximately ball-joint behavior:
- broad pitch
- broad yaw
- moderate roll

### Middle joints
Begin hinge-like, but allow unusual reversal if desired.

Example:
- normal flexion range
- optional limited hyperextension
- experimental bidirectional mode

### Distal joints
Allow:
- pitch
- roll
- modest yaw

### End effectors
Should support both:
- support/contact
- manipulation/gesture

---

# 5. "Impossible" machine capabilities

Choose only a few. These should feel authored, not random.

Recommended Pilgrim Machine traits:

## A. Bidirectional elbow / knee mode

Some middle joints can bend in either direction.

Use sparingly.

Purpose:
- allows strange transitions
- enables body inversion without full repositioning
- gives the machine a non-biological signature

## B. Independent torso rotation

Upper torso can rotate significantly relative to the pelvis.

Purpose:
- ceremonial turning
- head/body decoupling
- ritual poses

## C. Limb-role switching

A limb can transition:

```text
gesture limb
    ↓
support limb
    ↓
anchor
    ↓
gesture limb
```

## D. Stable head / unstable body

Head or sensor pod can remain world-oriented while the torso bows, rotates, crawls, or kneels.

## E. Temporary multi-contact mode

The machine can move with:

- 2 contacts
- 3 contacts
- 4 contacts

without changing rigs.

---

# 6. Rig structure in Blender

## Deform skeleton

Keep the deform skeleton simple and stable.

Suggested bone groups:

```text
ROOT
PELVIS / CORE

SPINE_01
SPINE_02
SPINE_03
CHEST

NECK_01
NECK_02
HEAD

LIMB_A_01
LIMB_A_02
LIMB_A_03
LIMB_A_EE

LIMB_B_01
LIMB_B_02
LIMB_B_03
LIMB_B_EE

LIMB_C_01
LIMB_C_02
LIMB_C_03
LIMB_C_EE

LIMB_D_01
LIMB_D_02
LIMB_D_03
LIMB_D_EE
```

Optional:
- clavicle / shoulder carrier bones
- hip carrier bones
- extra torso twist bones
- tail / counterweight
- antenna / secondary appendages

---

# 7. Control rig

Use separate control bones for animation.

Minimum controls:

```text
CTRL_ROOT
CTRL_CORE
CTRL_CHEST
CTRL_HEAD

IK_A
IK_B
IK_C
IK_D

POLE_A
POLE_B
POLE_C
POLE_D
```

Optional:
- FK limb controls
- IK/FK switches
- spine spline controls
- shoulder / hip offset controls
- head look-at
- contact-state custom properties

Recommended custom properties:

```text
ik_fk_A
ik_fk_B
ik_fk_C
ik_fk_D

contact_A
contact_B
contact_C
contact_D

joint_reverse_A
joint_reverse_B
joint_reverse_C
joint_reverse_D

head_world_lock
torso_twist_gain
```

---

# 8. Blender / MCP architecture

Use Blender as the central artistic and cleanup environment.

The agent should be able to:

- create or modify the skeleton
- generate control bones
- create IK constraints
- import BVH
- retarget motion
- inspect keyframes
- create guide poses
- add contact markers
- bake final Actions
- render previews
- export diagnostics

The Blender MCP repository in use:

```text
https://github.com/ahujasid/mcp-for-blender
```

Recommended division of responsibility:

```text
AnyTop
  ↓
raw motion proposal
  ↓
Blender / MCP
  ├─ retarget
  ├─ timing edits
  ├─ contact correction
  ├─ IK
  ├─ smoothing
  ├─ loop construction
  └─ artistic direction
```

Do not run the AnyTop environment inside Blender's Python unless there is a strong reason.

Keep:

```text
AnyTop environment
```

and

```text
Blender environment
```

separate.

Exchange data through:
- BVH
- `.npy`
- JSON constraint metadata
- optionally FBX / glTF after baking

---

# 9. AnyTop usage modes

## Mode A — Unconditional motion discovery

Goal:

> "What does this body naturally want to do according to the learned prior?"

Process:

```text
Pilgrim skeleton
    ↓
AnyTop condition
    ↓
N random seeds
    ↓
motion candidates
    ↓
Blender preview
```

Use this for:
- discovering unexpected motion
- ambient movement
- strange poses
- locomotor ideas
- secondary-motion language

Recommended batch:
- 20–100 seeds per morphology

Do not expect:
- exact semantic action
- reliable contact
- perfect physics
- exact loops

## Mode B — In-betweening

Use when start/end behavior matters.

Example:

```text
UPRIGHT
  ↓
generated transition
  ↓
KNEELING
```

Prefer small guided windows rather than only one start frame and one end frame.

Example:

```text
frames 0–8     = authored upright departure
frames 9–50    = generated
frames 51–60   = authored kneeling arrival
```

This gives the model motion context at both ends.

## Mode C — Partial-body regeneration

Use when:

```text
legs = good
torso = good
arms = boring
```

Preserve the good regions and regenerate selected body parts.

Artistically this can function like:

> generative fill for motion

Useful targets:
- head
- torso
- one limb
- upper body
- appendage subtree

---

# 10. Motion generation philosophy

AnyTop should not be treated as the final animator.

Use it as:

- motion prior
- variation generator
- strange-transition generator
- secondary-motion source
- morphology-response experiment

Final motion should be composed from:

```text
AnyTop
+
procedural timing
+
contact logic
+
IK
+
curation
+
manual or agent-authored sparse guidance
```

---

# 11. Contact system

Each end effector should have explicit contact state.

Example:

```text
frame 0:
C = contact
D = contact

frame 20:
A = contact
C = contact
D = contact

frame 40:
A = contact
B = contact
C = contact
D = contact

frame 70:
C = contact
D = contact
```

Store contact schedule independently from bone rotations.

Example JSON:

```json
{
  "contacts": [
    {"frame": 0, "A": 0, "B": 0, "C": 1, "D": 1},
    {"frame": 20, "A": 1, "B": 0, "C": 1, "D": 1},
    {"frame": 40, "A": 1, "B": 1, "C": 1, "D": 1},
    {"frame": 70, "A": 0, "B": 0, "C": 1, "D": 1}
  ]
}
```

When contact is active:
- lock end effector in world space
- solve limb using IK
- adjust root / pelvis if necessary
- avoid hard snapping into constraint

Blend constraint strength over several frames.

---

# 12. Core artistic movement set

Start with a small motion vocabulary.

## 01 — Processional Walk

Characteristics:
- slow
- upright
- small stride
- deliberate foot placement
- arms mostly quiet
- torso subtly oscillates

Purpose:
- baseline identity
- allows comparison with later strange modes

## 02 — Ritual Bow

Sequence:

```text
upright
  ↓
head remains fixed
  ↓
chest rotates down
  ↓
pelvis follows
  ↓
front limbs approach floor
  ↓
hold
  ↓
return
```

Important:
- avoid simple waist hinge
- distribute motion through spine

## 03 — Kneel / Re-anchor

Sequence:

```text
upright
  ↓
one front limb contacts ground
  ↓
second front limb contacts
  ↓
rear body compresses
  ↓
four-contact state
```

This is a central Pilgrim Machine behavior.

## 04 — Four-limb Crawl

Use:
- deliberate diagonal or pace-like contact sequences
- low torso
- stable head
- reduced bounce

Possible gait patterns:

```text
TROT:
A + D
B + C
```

```text
PACE:
A + C
B + D
```

```text
BOUND:
A + B
C + D
```

Try all three.

## 05 — Torso Reorientation

Feet remain planted while:
- torso rotates
- head remains on target
- limbs absorb twist
- one contact may temporarily release

This can become a signature behavior.

## 06 — Devotional Hold

Very little movement.

Use:
- tiny weight shifts
- subtle mechanical settling
- low-amplitude torso motion
- head stabilization
- occasional limb correction

Important for contrast.

## 07 — Collapse / Recover

Not a ragdoll fall.

Instead:

```text
controlled release
    ↓
joint sequence folds
    ↓
contact catches body
    ↓
pause
    ↓
recovery through another support pattern
```

This should feel intentional.

## 08 — Role-Swap Transition

Example:

```text
A/B = gesture limbs
C/D = support
```

becomes:

```text
A/B = support
C/D = propulsion
```

without changing the skeleton.

This is one of the most important experimental motions.

---

# 13. Rhythm system

The Pilgrim Machine is well suited for rhythmic / audiovisual work.

Use a motion phase layer independent of raw animation.

Possible mappings:

```text
kick
→ support transfer

snare
→ chest compression

bass envelope
→ crouch depth

high-frequency transient
→ head / sensor snap

slow musical phrase
→ torso rotation

tempo
→ gait phase rate
```

Do not hard-sync everything.

Use separate phase ratios:

```text
feet     = 1x
torso    = 1/2x
head     = sparse / event-driven
arms     = 1/4x or syncopated
```

This prevents "robot dancing" and makes the movement feel internally rhythmic.

---

# 14. Loop construction

Preferred loop classes:

## Idle loop
- 4–12 s
- tiny weight shift
- subtle torso movement
- occasional head correction

## Ritual loop
- 6–20 s
- bow
- hold
- recover

## Locomotion loop
- one or more gait cycles
- local pose loops
- root translation remains continuous

## Contact loop
- change support pattern
- return to original support arrangement

Do not simply duplicate the first frame at the end.

Check:
- pose continuity
- velocity continuity
- root continuity
- contact continuity

---

# 15. Quality metrics

For each generated candidate calculate or inspect:

## Mechanical
- foot / hand sliding
- ground penetration
- joint-limit violations
- self-intersection
- root discontinuity
- abrupt acceleration
- jerk spikes

## Motion
- loop seam quality
- contact timing
- readable support changes
- amount of correction required
- silhouette variation
- stability vs useful instability

## Artistic
Score manually:
- distinctive?
- intentional?
- readable?
- strange without becoming noise?
- useful for a finished shot?
- does it reinforce Pilgrim identity?

---

# 16. Correction-energy metric

Track how much cleanup is required.

Conceptually:

```text
raw AnyTop
   ↓
corrected final
```

Measure average pose difference.

Purpose:

> Determine whether AnyTop contributes meaningful motion or merely creates noise that gets replaced by cleanup.

Keep:
- raw motion
- corrected motion
- final baked motion

side-by-side for evaluation.

---

# 17. Morphology variants

Once the baseline works, create controlled variants.

Do not immediately change topology.

Keep the same four-limb graph and vary geometry.

## Variant axes

### Forelimb length

```text
0.7 → 1.5
```

### Rear-limb length

```text
0.7 → 1.3
```

### Spine length

```text
0.7 → 1.8
```

### Shoulder width

```text
0.5 → 1.5
```

### Pelvis width

```text
0.5 → 1.5
```

### Neck length

```text
0.4 → 1.8
```

### Upright bias

```text
1.0 = humanoid
0.0 = horizontal tetrapod
```

### Symmetry

```text
1.0 = symmetric
0.0 = strongly asymmetric
```

This creates a continuous family rather than unrelated creatures.

---

# 18. Morphology experiment matrix

Example:

```text
P0 = baseline pilgrim
P1 = long forelimb
P2 = compressed rear body
P3 = elongated spine
P4 = narrow torso
P5 = asymmetric shoulder
```

For each:

```text
20 AnyTop seeds
×
3 motion families
=
60 clips
```

Then compare:

- how morphology changes motion character
- whether the prior adapts meaningfully
- which variants produce artistically usable movement

---

# 19. Visual design integration

The existing artwork should drive:

- limb thickness
- actuator placement
- joint-cover geometry
- silhouette
- material separation
- head shape
- mechanical logic

Do **not** let the visual mesh dictate every joint literally.

Use a clean animation skeleton underneath.

A joint can visually appear as:
- rotary actuator
- ring bearing
- tendon cable
- piston
- sliding carriage
- magnetic coupling

while still being represented as a normal Blender bone/constraint internally.

---

# 20. Mesh strategy

Recommended:

```text
control skeleton
    ↓
deform skeleton
    ↓
mechanical mesh modules
```

Prefer modular rigid components where possible.

Advantages:
- easy to redesign
- easy to vary proportions
- avoids difficult organic skin deformation
- supports unusual joint rotation
- suits robotic aesthetic

For flexible zones:
- cables
- cloth
- membrane
- exposed tendon
- soft bellows

can provide secondary motion.

---

# 21. Secondary motion

Do not bake all life into the main skeleton.

Add layers such as:

- hanging cables
- antenna
- cloth strips
- flexible neck covering
- suspended ornaments
- inertial panels
- piston lag
- spring elements

These can respond procedurally to:
- velocity
- acceleration
- rhythm
- body orientation

This can make relatively sparse primary animation look much richer.

---

# 22. Render outputs

Each successful motion should produce more than one asset.

## A. Beauty render
Finished character.

## B. Skeleton render
Bones / joints visible.

## C. Motion-trail render
Show end-effector / head / root paths.

## D. Onion-skin render
Several poses simultaneously.

## E. Contact visualization
Highlight active support limbs.

## F. Silhouette render
Black/white form study.

## G. Rhythm-reactive version
Optional audiovisual output.

This turns experiments into usable artwork even when the generated motion itself is imperfect.

---

# 23. Suggested first finished artwork

## "Pilgrim: First Genuflection"

Duration:
- 8–15 seconds

Sequence:

```text
0–2 s
upright stillness

2–4 s
head remains fixed
torso bows

4–6 s
first hand plants
second hand follows

6–9 s
machine settles into four-contact posture

9–11 s
torso rotates slightly while head remains fixed

11–14 s
machine rises via a different path
```

Important:
- return should not simply reverse the descent
- asymmetry is desirable
- pauses matter
- movement should feel ceremonial

Output:
- one looping video
- one still frame
- one skeleton/onion-skin study
- one trajectory visualization

---

# 24. Suggested second finished artwork

## "Pilgrim: Change of Species"

Same machine, same topology.

Sequence:

```text
upright processional walk
        ↓
front limbs gradually begin carrying weight
        ↓
torso pitches forward
        ↓
contact schedule changes
        ↓
quadrupedal gait emerges
        ↓
movement becomes animal-like
```

Do not morph the mesh initially.

Let **movement alone** change the apparent species.

This directly tests one of the project's strongest ideas.

---

# 25. Suggested third finished artwork

## "Pilgrim: Litany"

Audio-reactive performance.

Inputs:
- BPM
- bass envelope
- onset events

Outputs:
- gait phase
- torso compression
- head events
- support-state transitions

Target:
- avoid literal dance
- preserve ritual / machine identity
- use repetition with small variation

---

# 26. Agent task decomposition

The Blender agent should work through narrow tasks.

Example commands:

```text
Create a neutral four-limb Pilgrim Machine control rig.
Use three-segment limbs with IK targets and pole controls.
Keep front/rear semantic labels out of the control abstraction.
```

```text
Create an Action called PILGRIM_Bow_Guide.
Pose upright at frame 1.
At frame 40 lower the chest while keeping the head aimed at Empty_HEAD_TARGET.
At frame 60 place limb A end effector on the floor.
At frame 75 place limb B end effector on the floor.
```

```text
Import AnyTop BVH sample 17.
Retarget it onto the Pilgrim deform skeleton.
Do not bake IK yet.
Create a side-by-side duplicate showing the raw source.
```

```text
Detect likely contact intervals from end-effector vertical velocity and floor distance.
Create contact marker empties.
Do not change animation.
```

```text
Apply IK contact correction only during marked support intervals.
Bake to a new Action.
Preserve the raw Action.
```

Keep each agent step reversible.

---

# 27. File organization

Suggested project structure:

```text
pilgrim_machine/
│
├── blender/
│   ├── pilgrim_master.blend
│   ├── pilgrim_motion_lab.blend
│   └── renders/
│
├── rigs/
│   ├── pilgrim_skeleton.json
│   ├── pilgrim_rest.bvh
│   └── mappings/
│
├── anytop/
│   ├── conditions/
│   ├── raw_samples/
│   ├── previews/
│   └── logs/
│
├── motion/
│   ├── guides/
│   ├── raw/
│   ├── corrected/
│   ├── loops/
│   └── final/
│
├── metadata/
│   ├── contacts/
│   ├── constraints/
│   └── scores/
│
├── artwork/
│   ├── reference/
│   └── design_notes/
│
└── docs/
    └── PILGRIM_MACHINE.md
```

---

# 28. Naming convention

Examples:

```text
PILGRIM_Upright_Idle_v001
PILGRIM_Bow_Guide_v003
PILGRIM_Bow_AnyTop_s0042
PILGRIM_Bow_Corrected_s0042
PILGRIM_Bow_Final_v002

PILGRIM_Crawl_Trot_s0017
PILGRIM_Crawl_Pace_s0088
PILGRIM_RoleSwap_v001
```

Never overwrite raw generated material.

---

# 29. First implementation milestones

## Milestone 1 — Rig

Success criteria:
- four limbs
- working IK
- neutral naming
- stable torso
- head tracking
- contact targets

## Milestone 2 — AnyTop connection

Success criteria:
- custom or compatible skeleton condition
- batch generation
- BVH import
- raw preview Actions

## Milestone 3 — Contact cleanup

Success criteria:
- detect support periods
- lock end effectors
- reduce sliding
- preserve generated character

## Milestone 4 — First finished loop

Build:

```text
Pilgrim: First Genuflection
```

Must be artistically presentable, not merely technically valid.

## Milestone 5 — Morphology variation

Create at least 3 geometry variants using the same topology.

## Milestone 6 — Species-shift motion

Create:

```text
upright → quadruped
```

using the same machine.

## Milestone 7 — Audio/rhythm system

Drive selected motion parameters from musical features.

---

# 30. What to avoid early

Do not begin with:

- six or eight limbs
- changing bone topology mid-animation
- complex muscles
- full physics simulation
- fully procedural locomotion
- exact biomechanical validation
- giant custom UI
- training AnyTop from scratch

First prove that the Pilgrim Machine produces **distinctive finished motion**.

---

# 31. Core research / artistic questions

Keep these questions visible during development.

### Q1
Does learned motion on an unusual morphology produce genuinely interesting movement, or merely artifacts?

### Q2
How much correction can be applied before the learned character is erased?

### Q3
Can the same four-limbed skeleton convincingly move between humanoid and quadrupedal movement languages?

### Q4
Can changing limb roles make the machine appear to change "species" without changing topology?

### Q5
Can rhythm entrainment produce coherent ritual motion without becoming conventional dance?

### Q6
Which morphology parameters have the greatest effect on perceived motion identity?

### Q7
Can technically failed motion samples still produce valuable artistic poses, trails, or loops?

---

# 32. Definition of success

The project is successful if it produces:

- a visually distinctive machine
- a reusable four-limb rig
- multiple believable but nonhuman motion modes
- at least one polished loop
- at least one strong still / pose study
- a meaningful AnyTop contribution to the motion
- an animation system that remains useful even when AnyTop output is imperfect

The strongest outcome is not:

> "AnyTop perfectly animates arbitrary robots."

It is:

> **"A strange body and a learned motion prior interact to produce a movement language that can become finished art."**
