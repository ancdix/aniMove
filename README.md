# aniMove

AnyTop motion generation and Blender ingestion for the robot motion lab.

The current direction is [Pilgrim Machine: a rigged creature and finished animation](docs/pilgrim_machine_execution_plan.md), based on the supplied design spec and artwork. The **first blockout and direct custom-skeleton AnyTop pilot are built**: a verified authored pose envelope and a separate raw-versus-fitted generated-motion comparison are loaded in Blender. See [Pilgrim results, previews, and remaining rig/motion work](docs/pilgrim_blockout_results.md). Detailed modeling and fabric remain deferred until usable blockout animation is established.

The earlier design is in [the original plan](docs/anytop_blender_robot_motion_lab_plan.md); source-level caveats are in [the implementation review](docs/anytop_blender_robot_motion_lab_review.md).

The first CUDA generation and nine-clip Blender import are complete. See [smoke-test results and output links](docs/anytop_smoke_test_results.md) for verification, timings, and raw-motion quality limitations.

The first **contact-aware robot baseline** is also built and loaded in Blender. Nine clips were screened; four pass the initial prototype gates. The selected weight-shift clip drives an editable four-limb robot, with separate transferred and cleaned Actions. Contact sliding falls by 96.9% on this clip. See [baseline results, preview, controls, and reproduction commands](docs/contact_robot_baseline_results.md).

A **collision-checked forward walk** is now available in `WALK_Collision_Checked`: eight seconds at 30 fps, using controlled footsteps with AnyTop body detail. No limb/body intersections were detected across 957 evaluated poses. See [walking results, video, controls, and verification](docs/walking_collision_results.md). The earlier baseline is retained for comparison and does not include this collision cleanup.

A **genuine AnyTop source-to-robot comparison** is available in `ANYTOP_Source_to_Robot`: the original 44-joint Hound sequence beside the robot, with matching foot paths, body trajectory, head direction and original timing. Outward IK knees prevent clipping; no procedural gait or contact pinning is used. See [source-transfer results and validation](docs/anytop_source_transfer_results.md).

**Controlled editing is now tested**: four AnyTop-generated middle-section variations and an experimental four-support-to-two-support transition. The upright goal is authored; the robot needs substantial contact/body cleanup, and physical balance is unverified. See [editing results, videos and limitations](docs/anytop_inbetween_extreme_results.md).

A **closed rise–lower–settle loop** is now available in `ANYTOP_Rise_Land_Loop`, with raw AnyTop output beside the corrected robot. Twenty paired raw samples tested intermediate guidance and landing cues; they did not establish reliable landing physics. See [loop, landing charts and measured corrections](docs/anytop_rise_land_loop_results.md).

## Storage and setup

Code, the isolated Python environment, and uv's package-build cache live in this repository. Models, conditioning data, reusable wheels, logs, and generated motion live at:

```text
/media/ipsedesktop/ShareDrive1/ModelData/aniMove
```

The ShareDrive must be mounted and writable. It contains the verified, revision-pinned `AnyTop/`, `t5-base/`, and `asset_manifest.json` assets. No complete Truebones training dataset is needed for this inference workflow.

uv's cache uses `.cache/uv` on the Linux filesystem because build environments need symlinks that ShareDrive's exFAT filesystem cannot provide. The original Conda/Python pins are preserved; uv installs the same pinned Python packages.

```bash
bash scripts/setup_anytop.sh
```

The setup script expects the pinned upstream revisions documented in the review. It applies the saved local patches and installs Motion into `.venv-anytop`. Blender and MCP have separate environments.

## Generate and validate

Run from the repository root with the isolated interpreter:

```bash
.venv-anytop/bin/python scripts/generate_batch.py \
  --family quadropeds --object Hound --seed 100 --repetitions 1 \
  --name hound-first
```

Every run must have a new name; existing outputs are never overwritten. The script loads the staged models offline and writes output under `ShareDrive1/ModelData/aniMove/generated/<name>/`. A run includes:

- `run.json`: exact command, source patch, environment, seed and checkpoint hash.
- `generation.log`: inference and export diagnostics.
- Per-clip motion features, explicit `.xyz.npy`, 20 fps BVH, MP4, and metadata.
- `validation.json`: numeric, joint-order, video-timing, and BVH-timing checks plus BVH-fitting errors.
- `bvh_reference/`: reconstructed positions used to verify the Blender import.

`status: generated` means the inference subprocess succeeded; `validation.json` must also say `passed`. These checks do not establish foot-contact quality or physical feasibility.

## Blender import validation

Use a separate background Blender instance to preserve the open workspace. Each clip is imported into a new scene and Action; every joint position is compared against the BVH reconstruction for every frame.

```bash
/snap/blender/7803/blender --background --factory-startup --python-exit-code 1 \
  --python scripts/blender_import_smoke.py -- \
  /media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/hound-smoke.blend \
  /media/ipsedesktop/ShareDrive1/ModelData/aniMove/generated/hound-first
```

The output `.blend` must not already exist. Its adjacent `.validation.json` records the import checks. Coordinates map from source `(x, y, z)` to Blender `(x, -z, y)`, with scale 1 in upstream normalized units. This is not a claim that the units are meters. The source moves toward Blender `-Y`, and `+Z` is up.

## Local compatibility patches

`patches/anytop-generation.patch` corrects frame timing, exports explicit XYZ arrays, and records metadata and stage timings. `patches/motion-named-leaf-joints.patch` adds an opt-in export that preserves terminal joints as named Blender bones instead of losing them as unnamed BVH End Sites. Original upstream behavior remains the default for other callers.

```bash
.venv-anytop/bin/python -m unittest discover -s tests -v
```

The editing input defect is repaired and tested through the in-betweening experiment; see its report for the exact validation scope. Generation, ingestion, contact screening, Hound-to-robot transfer and controlled in-betweening are implemented. Broader morphology/gait validation, loops, and rhythm remain later milestones.
