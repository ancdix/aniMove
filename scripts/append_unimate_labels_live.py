"""Append the matched comparison without replacing previous Blender work."""
import bpy,json
from pathlib import Path
out=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_labels_001')
v=json.loads((out/'saved_blender_validation.json').read_text());assert v['status']=='passed' and v['saved_actions']==30
name='PILGRIM_UniMate_LABELS';assert name not in bpy.data.scenes,'Label comparison already loaded'
old_scenes=set(bpy.data.scenes.keys());old_actions=set(bpy.data.actions.keys());old_objects={s.name:set(s.objects.keys()) for s in bpy.data.scenes}
if bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
with bpy.data.libraries.load(str(out/'labels_comparison.blend'),link=False) as (source,target):
    target.scenes=[name];target.actions=[a for a in source.actions if a.startswith('UNI_')];target.texts=['UNIMATE_LABELS_UI.py','README_UNIMATE_LABELS']
s=bpy.data.scenes[name];bpy.context.window.scene=s;s.sync_mode='FRAME_DROP'
ns={'__name__':'unimate_labels_live'};exec(bpy.data.texts['UNIMATE_LABELS_UI.py'].as_string(),ns);bpy.app.driver_namespace['unimate_labels_ui']=ns
s.unimate_label_case='p05_9602';bpy.ops.unimate.label_step(delta=1);assert s['active_case']=='p07_9600';bpy.ops.unimate.label_step(delta=-1);assert s['active_case']=='p05_9602'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='SOLID';area.spaces.active.shading.color_type='MATERIAL';area.spaces.active.overlay.show_overlays=False;area.spaces.active.show_region_ui=True
assert old_scenes.issubset(bpy.data.scenes.keys()) and old_actions.issubset(bpy.data.actions.keys())
assert all(objects==set(bpy.data.scenes[n].objects.keys()) for n,objects in old_objects.items())
active={v:s.objects[n].animation_data.action.name for v,n in json.loads(s['rigs']).items()}
assert all(a=='UNI_'+v+'_p05_s9602' for v,a in active.items())
bpy.ops.screen.animation_play()
r=dict(status='passed',scene=s.name,playing=bpy.context.screen.is_animation_playing,case=s['active_case'],active_actions=active,selector_roundtrip=True,preserved_scenes=len(old_scenes),preserved_actions=len(old_actions))
(out/'live_session.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
