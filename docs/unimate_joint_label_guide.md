# UniMate joint labels: accepted strings versus learned meaning

Verified against pinned UniMate commit `9f3076e1db482883edb6f6a37a67f521c3853278`, the active independent checkpoint, its Flan-T5-base encoder and the published Objaverse annotations at dataset revision `c2b7ad6926b03dd72fae7934656dd4d4b9056029`.

## What can be supplied

There is **no closed runtime enumeration of allowed anatomical labels**. The loader uses `clean_joint_names` when it has one nonblank name per joint. It allows repeated names. If the field is missing, the wrong length, or contains a blank name, it falls back to the entire list of raw rig names; it does not repair just the one blank entry.

The encoder receives those cleaned strings as-is and turns each into a 768-dimensional vector. Its active factory disables text normalization and word dropout. We verified finite embeddings for common labels, `Bone`, `Wheel`, `Sacred Hydraulic Actuator`, and even `xyzzy`. **Encoding successfully does not demonstrate a learned motion role.** These are conditioning signals, not hard joint types, constraints or physical rules. Calling a joint “load-bearing paw” does not pin it to the floor.

The model also receives the rest pose, graph connectivity and action prompt. Joint labels neither replace that structure nor impose a skeleton template. Repeated `Spine` or `Bone` labels are distinguishable through the skeleton graph and pose. There is no separate input declaring “exactly two arms and two legs” in our run.

## What preprocessing does

The standard name cleaner strips namespaces and rig counters, expands side markers and maps synonyms. It is not an exhaustive inference whitelist. Our label-only experiment writes `clean_joint_names` directly after canonicalization so naming cannot also change facing, joint order or geometry. Raw bone identifiers remain unchanged.

| Raw name | Rule-cleaned name |
|---|---|
| `LeftUpperArm` | `Left Upper Arm` |
| `mixamorig:LeftArm` | `Left Upper Arm` |
| `Bip01_L_Thigh` | `Left Thigh` |
| `L_Foreleg` | `Left Front Leg` |
| `LeftFrontPaw` | `Left Front Paw` |
| `LeftHindFoot` | `Left Hind Foot` |
| `Tail03` | `Tail` |
| `Tentacle02` | `Tentacle` |
| `joint_014` or `Bone.003` | `Bone` |
| `Wheel_FL` | `Wheel` (this suffix does not preserve front/left) |

Inspect the final cleaned names before generation. Changing only a Blender display name while retaining old `clean_joint_names` will not change name conditioning. Cached embeddings are keyed by the cleaned string; changing a label requires the corresponding embedding, not renaming a cache entry.

## Evidence for useful labels

The staged public Objaverse annotation file contains **844 distinct cleaned labels across 7,355 rigs**, before filtering. These are annotation frequencies, **not the exact training exposure of the third-party checkpoint**, and not performance guarantees.

| Exact label | Annotated rigs containing it |
|---|---:|
| `Left Upper Arm` | 6,488 |
| `Left Front Leg` | 79 |
| `Left Hind Leg` | 62 |
| `Left Front Paw` | 20 |
| `Left Wing` | 83 |
| `Tail` | 451 |
| `Tentacle` | 3 |
| `Bone` | 775 |
| `Wheel` | 0 |
| `Sacred Hydraulic Actuator` | 0 |

This particular Objaverse table is dominated by humanoid labels. Other source families add animal coverage, and some quadrupeds use `Upper Arm`, `Forearm`, `Hand` and `Finger` on their front limbs. An arm label is therefore not proof that a rig is human or bipedal. Front/hind names are plausible alternatives, but their effect must be tested.

The complete searchable label list, joint-occurrence counts, rig counts and exact source hash are in [published_objaverse_vocabulary.json](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_labels_001/published_objaverse_vocabulary.json). Acceptance probes and normalization examples are in [label_acceptance.json](/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_labels_001/label_acceptance.json).

## Pilgrim comparison

Keep its 23-joint geometry and seven core labels unchanged. Change only the sixteen limb labels:

| Variant | A/B chains, with Left/Right | C/D chains, with Left/Right |
|---|---|---|
| Arms + legs | Upper Arm → Forearm → Hand → Finger | Thigh → Shin → Foot → Toe |
| Front + hind legs | Front Leg → Front Knee → Front Ankle → Front Foot | Hind Leg → Hind Knee → Hind Ankle → Hind Foot |
| Generic limbs | Bone → Bone → Bone → Bone | Bone → Bone → Bone → Bone |

The generic variant removes side and segment semantics too. `Bone` is a real text embedding; this is not the same as disabling the name-conditioning pathway. Every chosen front/hind label appears in the published annotations. All three variants retain the upright rest pose and high front-limb attachment points, which may still favor upright movement.

Three prompts (walk, crouch/advance, reach toward ground), three seeds and three label sets give 27 raw samples. Three unchanged baseline replays test reproducibility. Noise and every non-name conditioning field are hashed at the actual stock sampling call, rather than assuming a shared seed is enough. No IK, authored guide, smoothing, retargeting or grounding correction is applied.

## Measured outcome

The [completed matched experiment](unimate_label_ablation_results.md) found a median 0.281 m joint-position change for front/hind names and 0.481 m for generic limb names across nine matched cases. Unchanged replays were exact. Names alter generated movement, but do not guarantee four-foot contact. The report links all raw comparisons and the three-rig Blender master.

## Sources

- [Official name-selection implementation](https://github.com/Friedrich-M/UniMate/blob/9f3076e1db482883edb6f6a37a67f521c3853278/unimate/dataset/mixture/dataset.py): `model_joint_names` and `_precompute_object_type_meta`.
- [Text encoder factory](https://github.com/Friedrich-M/UniMate/blob/9f3076e1db482883edb6f6a37a67f521c3853278/unimate/models/text_encoder/factory.py).
- [Rule vocabulary](https://github.com/Friedrich-M/UniMate/blob/9f3076e1db482883edb6f6a37a67f521c3853278/data_process/joint_annotation/vocab.py) and [cleaner](https://github.com/Friedrich-M/UniMate/blob/9f3076e1db482883edb6f6a37a67f521c3853278/data_process/joint_annotation/names_clean_rule.py).
- [Published joint-label annotations](https://huggingface.co/datasets/Linzhan/UniML3D/blob/c2b7ad6926b03dd72fae7934656dd4d4b9056029/export/objaverse/clean_joint_names.json).
