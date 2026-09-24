"""Append verified stance comparisons without replacing existing live work."""
import json
from pathlib import Path
import bpy

out = Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_stance_001')
validation = json.loads((out / 'saved_blender_validation.json').read_text())
assert validation['status'] == 'passed' and validation['raw_actions'] == 18
name = 'PILGRIM_UniMate_STANCE'
assert name not in bpy.data.scenes, 'Comparison already loaded; do not duplicate it.'
old_scenes = set(bpy.data.scenes.keys())
old_actions = set(bpy.data.actions.keys())
old_objects = {s.name: set(s.objects.keys()) for s in bpy.data.scenes}
if bpy.context.screen.is_animation_playing:
    bpy.ops.screen.animation_cancel(restore_frame=False)
with bpy.data.libraries.load(str(out / 'stance_review.blend'), link=False) as (source, target):
    target.scenes = [name]
    target.actions = [a for a in source.actions if a.startswith(('UNI_stance_', 'STN_REFERENCE_'))]
    target.texts = ['UNIMATE_STANCE_UI.py', 'README_UNIMATE_STANCE']
s = bpy.data.scenes[name]
bpy.context.window.scene = s
s.sync_mode = 'FRAME_DROP'
ns = {'__name__': 'unimate_stance_live'}
exec(bpy.data.texts['UNIMATE_STANCE_UI.py'].as_string(), ns)
bpy.app.driver_namespace['unimate_stance_ui'] = ns
for case in ['REFERENCE', 'walk_9700', 'REFERENCE', 'walk_9700']:
    s.unimate_stance_case = case
    assert s['active_case'] == case
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            space.region_3d.view_perspective = 'CAMERA'
            space.shading.type = 'SOLID'
            space.shading.color_type = 'MATERIAL'
            space.overlay.show_overlays = False
            space.show_region_ui = True
assert old_scenes.issubset(bpy.data.scenes.keys())
assert old_actions.issubset(bpy.data.actions.keys())
assert all(objects == set(bpy.data.scenes[n].objects.keys()) for n, objects in old_objects.items())
new_actions = set(bpy.data.actions.keys()) - old_actions
assert len(new_actions) == 20
bpy.ops.screen.animation_play()
result = dict(status='passed', scene=s.name, case=s['active_case'],
              playing=bpy.context.screen.is_animation_playing,
              preserved_scenes=len(old_scenes), preserved_actions=len(old_actions),
              added_actions=len(new_actions), selector_roundtrip=True)
(out / 'live_session.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
