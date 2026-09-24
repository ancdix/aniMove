"""Append verified harvest scenes without replacing the open Blender file."""
import bpy,json
from pathlib import Path
p=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/motion_harvest_001/curated_v004')
package=json.loads((p/'package_validation.json').read_text());assert package['status']=='passed'
for r in package['assets']:
    assert json.loads((p/r['title']/'saved_validation.json').read_text())['status']=='passed'
names=[n for r in package['assets'] for n in r['scenes']];actions=[r['baked_action'] for r in package['assets']]
assert not any(n in bpy.data.scenes for n in names),'Harvest already loaded; do not duplicate'
old_scenes=set(bpy.data.scenes.keys());old_actions=set(bpy.data.actions.keys())
old_objects={s.name:set(s.objects.keys()) for s in bpy.data.scenes}
if bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
with bpy.data.libraries.load(str(p/'motion_harvest_master.blend'),link=False) as (source,target):
    assert all(n in source.scenes for n in names);assert all(n in source.actions for n in actions)
    target.scenes=list(names);target.actions=list(actions)
    target.texts=[n for n in source.texts if n.startswith('README_') or n.endswith('CONTROL_UTILITIES.py')]
for name in actions:bpy.data.actions[name].use_fake_user=True
scene=bpy.data.scenes['PILGRIM_Orient_Loop'];bpy.context.window.scene=scene;scene.frame_set(1);scene.sync_mode='FRAME_DROP'
rig=scene.objects[scene['rig']];assert rig.animation_data.action.name==scene['control_action'];assert rig['use_controls']==1
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            s=area.spaces.active;s.region_3d.view_perspective='CAMERA';s.shading.type='SOLID';s.shading.color_type='MATERIAL'
            s.overlay.show_extras=False;s.overlay.show_bones=False;s.overlay.show_relationship_lines=False;s.overlay.show_cursor=False
            s.overlay.show_floor=False;s.overlay.show_axis_x=False;s.overlay.show_axis_y=False
assert old_scenes.issubset(bpy.data.scenes.keys());assert old_actions.issubset(bpy.data.actions.keys())
assert all(objects==set(bpy.data.scenes[name].objects.keys()) for name,objects in old_objects.items())
bpy.ops.screen.animation_play()
report=dict(active_scene=scene.name,playing=bpy.context.screen.is_animation_playing,preserved_scenes=len(old_scenes),preserved_actions=len(old_actions),added_scenes=names,baked_actions=actions)
(p/'live_session.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
