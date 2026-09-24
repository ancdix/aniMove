import bpy,json
from pathlib import Path
p=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_harvest_001');s=bpy.data.scenes['PILGRIM_UniMate_RAW'];assert bpy.context.scene==s
playing=bpy.context.screen.is_animation_playing
if playing:bpy.ops.screen.animation_cancel(restore_frame=False)
initial=s['active_clip'];bpy.ops.unimate.step_clip(delta=1);next_clip=s['active_clip'];assert next_clip!=initial;bpy.ops.unimate.step_clip(delta=-1);assert s['active_clip']==initial
rig=s.objects[s['rig']];assert rig.animation_data.action.name==initial
if playing:bpy.ops.screen.animation_play()
result=dict(status='passed',next_button=next_clip,restored=initial,sidebar_registered=hasattr(bpy.types,'UNIMATE_PT_raw_review'),playing=bpy.context.screen.is_animation_playing);(p/'live_ui_validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
