"""Execute through Blender MCP only after saved-artifact verification."""
import bpy,json
from pathlib import Path
base=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine')
old_scenes=set(bpy.data.scenes.keys());old_actions=set(bpy.data.actions.keys())
original_objects=set(bpy.data.scenes['Scene'].objects.keys()) if 'Scene' in bpy.data.scenes else set()
if bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
for filename,name in [(base/'blockout_v004/pilgrim_blockout.blend','PILGRIM_Blockout'),(base/'pilot_v002/comparison/pilgrim_direct_anytop.blend','PILGRIM_Direct_AnyTop')]:
    if name in bpy.data.scenes:raise RuntimeError('Scene already exists; do not silently duplicate: '+name)
    with bpy.data.libraries.load(str(filename),link=False) as (source,target):
        assert name in source.scenes;target.scenes=[name]
scene=bpy.data.scenes['PILGRIM_Blockout'];bpy.context.window.scene=scene;scene.frame_set(1);scene.sync_mode='FRAME_DROP'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            s=area.spaces.active;s.region_3d.view_perspective='CAMERA';s.shading.type='SOLID';s.shading.color_type='MATERIAL';s.overlay.show_extras=False;s.overlay.show_bones=False;s.overlay.show_relationship_lines=False;s.overlay.show_cursor=False;s.overlay.show_floor=False;s.overlay.show_axis_x=False;s.overlay.show_axis_y=False
assert old_scenes.issubset(bpy.data.scenes.keys());assert old_actions.issubset(bpy.data.actions.keys())
if original_objects:assert original_objects==set(bpy.data.scenes['Scene'].objects.keys())
bpy.ops.screen.animation_play()
result=dict(active_scene=scene.name,playing=bpy.context.screen.is_animation_playing,added_scenes=sorted(set(bpy.data.scenes.keys())-old_scenes),preserved_scenes=len(old_scenes),preserved_actions=len(old_actions),original_scene_objects=sorted(original_objects))
(base/'live_session.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
