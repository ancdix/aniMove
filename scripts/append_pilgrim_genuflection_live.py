"""Append only the verified genuflection asset and comparison; preserve live work."""
import bpy,json
from pathlib import Path
p=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/genuflection_loop_v003')
assert json.loads((p/'saved_validation.json').read_text())['status']=='passed'
scene_names=['PILGRIM_First_Genuflection','PILGRIM_Genuflection_Loop'];baked='PILGRIM_Genuflection_Final_FK_v001'
assert not any(n in bpy.data.scenes for n in scene_names),'Genuflection scene already loaded; do not duplicate'
old_scenes=set(bpy.data.scenes.keys());old_actions=set(bpy.data.actions.keys());original=set(bpy.data.scenes['Scene'].objects.keys()) if 'Scene' in bpy.data.scenes else set()
if bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
with bpy.data.libraries.load(str(p/'pilgrim_genuflection_master.blend'),link=False) as (source,target):
    assert all(n in source.scenes for n in scene_names);assert baked in source.actions
    target.scenes=list(scene_names);target.actions=[baked];target.texts=[n for n in source.texts if n in ['README_PILGRIM_GENUFLECTION','PILGRIM_GENU_CONTROL_UTILITIES.py']]
scene=bpy.data.scenes['PILGRIM_First_Genuflection'];bpy.context.window.scene=scene;scene.frame_set(1);scene.sync_mode='FRAME_DROP';rig=bpy.data.objects[scene['rig']]
assert scene['baked_action'] in bpy.data.actions;assert rig.animation_data.action.name==scene['control_action'];assert rig['use_controls']==1
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            s=area.spaces.active;s.region_3d.view_perspective='CAMERA';s.shading.type='SOLID';s.shading.color_type='MATERIAL';s.overlay.show_extras=False;s.overlay.show_bones=False;s.overlay.show_relationship_lines=False;s.overlay.show_cursor=False;s.overlay.show_floor=False;s.overlay.show_axis_x=False;s.overlay.show_axis_y=False
assert old_scenes.issubset(bpy.data.scenes.keys());assert old_actions.issubset(bpy.data.actions.keys())
if original:assert original==set(bpy.data.scenes['Scene'].objects.keys())
bpy.ops.screen.animation_play();report=dict(active_scene=scene.name,playing=bpy.context.screen.is_animation_playing,preserved_scenes=len(old_scenes),preserved_actions=len(old_actions),added_scenes=scene_names,baked_action=baked,original_scene_objects=sorted(original))
(p/'live_session.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
