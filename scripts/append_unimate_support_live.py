"""Append the verified support study and retain every prior scene and Action."""
import bpy,json
from pathlib import Path
out=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_support_review_001');v=json.loads((out/'saved_blender_validation.json').read_text());assert v['status']=='passed' and v['saved_actions']==28
name='PILGRIM_UniMate_SUPPORT';assert name not in bpy.data.scenes
old_scenes=set(bpy.data.scenes.keys());old_actions=set(bpy.data.actions.keys());old_objects={s.name:set(s.objects.keys()) for s in bpy.data.scenes}
if bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
with bpy.data.libraries.load(str(out/'support_review.blend'),link=False) as (source,target):
    target.scenes=[name];target.actions=[a for a in source.actions if a.startswith('UNI_support_') or a.startswith('UNI_pilgrim_support_short_')];target.texts=['UNIMATE_SUPPORT_UI.py','UNIMATE_SUPPORT_UTILITIES.py','README_UNIMATE_SUPPORT']
s=bpy.data.scenes[name];bpy.context.window.scene=s;s.sync_mode='FRAME_DROP';ns={'__name__':'unimate_support_live'};exec(bpy.data.texts['UNIMATE_SUPPORT_UI.py'].as_string(),ns);bpy.app.driver_namespace['unimate_support_ui']=ns
s.unimate_support_clip=json.loads((out/'selection.json').read_text())['action']
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='SOLID';area.spaces.active.shading.color_type='MATERIAL';area.spaces.active.overlay.show_overlays=False;area.spaces.active.show_region_ui=True
assert old_scenes.issubset(bpy.data.scenes.keys()) and old_actions.issubset(bpy.data.actions.keys());assert all(objects==set(bpy.data.scenes[n].objects.keys()) for n,objects in old_objects.items())
bpy.ops.screen.animation_play();result=dict(status='passed',scene=s.name,clip=s['active_clip'],playing=bpy.context.screen.is_animation_playing,preserved_scenes=len(old_scenes),preserved_actions=len(old_actions));(out/'live_session.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
