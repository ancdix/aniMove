"""Run with Blender --background --factory-startup --python ... -- OUTPUT.blend RUN_DIR..."""
import json
import math
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Quaternion


def import_motion(sidecar):
    """Import one clip into its own source scene and verify every animated bone head."""
    item = json.loads(sidecar.read_text())
    name = 'RAW_%s_seed%04d_rep%02d' % (item['source_skeleton'], item['seed'], item['repetition'])
    scene = bpy.data.scenes.new(name)
    bpy.context.window.scene = scene
    scene.render.fps = item['fps']
    scene.render.fps_base = 1.0
    scene.frame_start = 1
    scene.frame_end = item['frames']
    result = bpy.ops.import_anim.bvh(
        filepath=str(sidecar.parent / item['bvh']), target='ARMATURE',
        global_scale=1.0, frame_start=1, use_fps_scale=False,
        update_scene_fps=True, update_scene_duration=True,
        rotate_mode='NATIVE', axis_forward='-Z', axis_up='Y')
    assert result == {'FINISHED'}, result
    # Blender's duration updater adds frame_start to the frame count; the last
    # keyed frame is frame_start + count - 1. Avoid an extra held frame on playback.
    scene.frame_start = 1
    scene.frame_end = item['frames']
    armature = bpy.context.object
    assert armature.type == 'ARMATURE'
    armature.name = name
    armature.show_in_front = True
    armature.data.display_type = 'STICK'
    collection = bpy.data.collections.new('SRC_ANYTOP_' + name)
    scene.collection.children.link(collection)
    collection.objects.link(armature)
    for old in list(armature.users_collection):
        if old != collection:
            old.objects.unlink(armature)
    action = armature.animation_data.action
    assert action is not None
    action.name = name
    action.use_fake_user = True
    armature['motion_manifest'] = str(sidecar)
    armature['source_up'] = '+Y'
    armature['blender_forward'] = '-Y'
    armature['unit_scale'] = 1.0
    armature['units'] = item['units']
    expected = np.load(sidecar.parent / 'bvh_reference' / (sidecar.stem + '.npy'))
    # Native BVH (+Y up) -> Blender (+Z up), preserving +X: (x, y, z) -> (x, -z, y).
    expected = expected[..., [0, 2, 1]].copy()
    expected[..., 1] *= -1
    observed = np.empty_like(expected)
    for frame in range(1, item['frames'] + 1):
        scene.frame_set(frame)
        evaluated = armature.evaluated_get(bpy.context.evaluated_depsgraph_get())
        for joint, bone_name in enumerate(item['joint_names']):
            observed[frame - 1, joint] = evaluated.matrix_world @ evaluated.pose.bones[bone_name].head
    error = np.linalg.norm(observed - expected, axis=-1)
    tolerance = max(1e-4, float(np.ptp(expected, axis=(0, 1)).max()) * 1e-5)
    assert np.isfinite(observed).all()
    assert float(error.max()) < tolerance, (name, float(error.max()), tolerance)
    assert abs(action.frame_range[0] - 1) < 1e-6
    assert abs(action.frame_range[1] - item['frames']) < 1e-6
    assert scene.render.fps == item['fps']
    assert scene.frame_end - scene.frame_start + 1 == item['frames']
    scene.frame_set(1)
    extent = float(np.ptp(expected, axis=(0, 1)).max())
    center = (expected.min(axis=(0, 1)) + expected.max(axis=(0, 1))) / 2
    # Explicit world axes without changing imported motion; the viewport grid marks Z=0.
    for axis, location in [('X', (1, 0, 0)), ('Y', (0, 1, 0)), ('Z', (0, 0, 1))]:
        empty = bpy.data.objects.new('AXIS_+' + axis, None)
        scene.collection.objects.link(empty)
        empty.empty_display_type = 'PLAIN_AXES'
        empty.empty_display_size = max(extent * 0.03, 0.03)
        empty.location = tuple(v * extent * 0.3 for v in location)
        empty.show_name = True
    scene['source_metadata'] = json.dumps(item)
    scene['import_validation'] = 'All frame/bone positions matched native BVH reconstruction'
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                space.region_3d.view_location = center
                space.region_3d.view_distance = max(extent * 1.7, 2.0)
                space.region_3d.view_rotation = Quaternion((0.8205, 0.4247, 0.1759, 0.3399))
    return dict(scene=name, frames=item['frames'], bones=len(armature.pose.bones),
                action=action.name, action_range=list(action.frame_range),
                source_path=str(sidecar), max_position_error=float(error.max()),
                tolerance=tolerance, fps=scene.render.fps,
                root_first=observed[0, 0].tolist(), root_last=observed[-1, 0].tolist())


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    destination = Path(args[0])
    assert not destination.exists(), 'Refusing to overwrite ' + str(destination)
    reports = []
    for directory in map(Path, args[1:]):
        for sidecar in sorted(directory.glob('*_rep_*.json')):
            reports.append(import_motion(sidecar))
    assert reports, 'No clips found'
    bpy.context.window.scene = bpy.data.scenes[reports[0]['scene']]
    destination.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(destination))
    destination.with_suffix('.validation.json').write_text(json.dumps(dict(status='passed', clips=reports), indent=2) + '\n')
    print('BLENDER_IMPORT_VALIDATED', len(reports), str(destination))


if __name__ == '__main__':
    main()
