"""Append verified raw review, preserving all existing live scenes and Actions."""
import bpy,json
from pathlib import Path
p=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_harvest_001');report=json.loads((p/'saved_blender_validation.json').read_text());assert report['status']=='passed' and report['saved_actions']==80
name='PILGRIM_UniMate_RAW';assert name not in bpy.data.scenes,'Raw review is already loaded'
old_scenes=set(bpy.data.scenes.keys());old_actions=set(bpy.data.actions.keys());old_objects={s.name:set(s.objects.keys()) for s in bpy.data.scenes}
if bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
with bpy.data.libraries.load(str(p/'unimate_raw_master.blend'),link=False) as (source,target):
    target.scenes=[name];target.actions=[a for a in source.actions if a.startswith('UNI_')];target.texts=[t for t in source.texts if t.startswith('UNIMATE_') or t=='README_UNIMATE_RAW']
scene=bpy.data.scenes[name];bpy.context.window.scene=scene;scene.sync_mode='FRAME_DROP';scene.frame_set(1)
# Keep module globals alive for EnumProperty strings and callback functions.
namespace={'__name__':'unimate_raw_review_live'};exec(bpy.data.texts['UNIMATE_REVIEW_UI.py'].as_string(),namespace);bpy.app.driver_namespace['unimate_raw_review_ui']=namespace
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='SOLID';area.spaces.active.shading.color_type='MATERIAL';area.spaces.active.overlay.show_overlays=False;area.spaces.active.show_region_ui=True
assert old_scenes.issubset(bpy.data.scenes.keys()) and old_actions.issubset(bpy.data.actions.keys());assert all(objects==set(bpy.data.scenes[n].objects.keys()) for n,objects in old_objects.items())
bpy.ops.screen.animation_play();result=dict(scene=scene.name,playing=bpy.context.screen.is_animation_playing,active_clip=scene['active_clip'],prompt=scene['active_prompt'],raw_actions=len(json.loads(scene['action_names'])),preserved_scenes=len(old_scenes),preserved_actions=len(old_actions));(p/'live_session.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
