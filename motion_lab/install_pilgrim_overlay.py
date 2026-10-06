"""Refresh the live panel and enable the Pilgrim model without regenerating motion."""
import bpy,importlib,json,shutil
from pathlib import Path
REPO=Path('/home/ipsedesktop/Documents/GitHub/aniMove')
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001')
assert json.loads((BASE/'pilgrim_overlay_validation.json').read_text())['status']=='passed'
old=bpy.app.driver_namespace['motion_lab_ui'];assert old['JOB'] is None,'A user generation is running; retry after it finishes'
s=bpy.data.scenes[old['SCENE']];bpy.context.window.scene=s
previous_job=s.get('active_result','');previous_frame=s.frame_current;previous_target=s.ml_target
preserved={name:getattr(s,name) for name in ['ml_prompt','ml_seconds','ml_seed','ml_autoplay','ml_follow']}
prior_actions=set(bpy.data.actions.keys());prior_scenes=set(bpy.data.scenes.keys())
if bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
old['unregister']();addon=Path(bpy.utils.user_resource('SCRIPTS',path='addons'))/'animove_motion_lab.py';shutil.copy2(REPO/'motion_lab/blender_ui.py',addon)
import animove_motion_lab
module=importlib.reload(animove_motion_lab);module.register()
text=bpy.data.texts['MOTION_LAB_UI.py'];text.clear();text.write((REPO/'motion_lab/blender_ui.py').read_text())
for key in ['Pilgrim','PilgrimQuad']:module.ensure_pilgrim_model(s,key)
job=previous_job
if previous_target not in ('Pilgrim','PilgrimQuad') or not job:
    results=[json.loads(p.read_text()) for p in (BASE/'jobs').glob('*/result.json')]
    job=max((r for r in results if r['request']['target']=='Pilgrim'),key=lambda r:r['created'])['id']
module.load_result(job,False);s.ml_history=job;s.ml_pilgrim_view='MODEL'
if job==previous_job:
    for name,value in preserved.items():setattr(s,name,value)
    s.frame_set(previous_frame)
assert prior_actions.issubset(bpy.data.actions.keys()) and prior_scenes.issubset(bpy.data.scenes.keys())
assert s.objects['ML_RIG_'+s.ml_target].animation_data.action['result_path']==str(BASE/'jobs'/job/'result.json')
master=BASE/'motion_lab.blend';backup=BASE/'motion_lab_before_pilgrim_overlay.blend'
if not backup.exists():shutil.copy2(master,backup)
blocks={s,text,bpy.data.texts['MOTION_LAB_PILGRIM_MODEL.json']}|{a for a in bpy.data.actions if a.name.startswith('ML_')}
bpy.data.libraries.write(str(master),blocks)
report=dict(status='passed',active_result=job,target=s.ml_target,display=s.ml_pilgrim_view,preserved_actions=len(prior_actions),installed_addon=str(addon),master=str(master))
(BASE/'pilgrim_overlay_live_validation.json').write_text(json.dumps(report,indent=2)+'\n')
if not bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_play()
print('PILGRIM_OVERLAY_INSTALLED',json.dumps(report))
