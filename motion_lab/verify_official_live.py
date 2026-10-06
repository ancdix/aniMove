"""Validate official Actions and saves, either live or in background Blender."""
import bpy,hashlib,json,shutil
from pathlib import Path
import numpy as np
REPO=Path('/home/ipsedesktop/Documents/GitHub/aniMove')
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001')
jobs_file=BASE/'official_v2_target_jobs.json'
if bpy.app.background:
    ns={'__name__':'motion_lab_review'};exec((REPO/'motion_lab/blender_ui.py').read_text(),ns);ns['register']()
    addon=Path(bpy.utils.user_resource('SCRIPTS',path='addons',create=True))/'animove_motion_lab.py'
    shutil.copy2(REPO/'motion_lab/blender_ui.py',addon)
    pending=dict(job=json.loads(jobs_file.read_text())[0],addon=str(addon))
else:
    ns=bpy.app.driver_namespace['motion_lab_ui'];pending=json.loads((BASE/'official_v2_pending.json').read_text())
s=bpy.data.scenes[ns['SCENE']];bpy.context.window.scene=s
assert ns['JOB'] is None,'Generation has not finished'
job_id=pending['job']
if not bpy.app.background:
    assert s.get('active_result')==job_id,'UI did not automatically load the official result'
    assert bpy.context.screen.is_animation_playing,'Autoplay did not start'
jobs=list(dict.fromkeys([job_id]+(json.loads(jobs_file.read_text()) if jobs_file.exists() else [])))
records=[]
for current in jobs:
    ns['load_result'](current,False)
    result=json.loads((BASE/'jobs'/current/'result.json').read_text())
    assert result['model_repository']=='Linzhan/UniMate'
    assert result['device']=='cuda'
    assert result['checkpoint_sha256']=='cbcfb7a057e45f967d5964fecf6b3f83358096f1306f25831e1644a18a50eb34'
    with np.load(BASE/'jobs'/current/'kinematics.npz') as data:x=data['positions']
    names=ns['TARGETS'][s.ml_target]['names'];rig=s.objects['ML_RIG_'+s.ml_target];error=0
    for frame in range(len(x)):
        s.frame_set(frame+1);bpy.context.view_layer.update()
        error=max(error,max((rig.pose.bones[name].head-ns['convert'](x[frame,j])).length for j,name in enumerate(names)))
    assert error<2e-4,error
    assert rig.animation_data.action['model_label']=='Official UniMate v2'
    records.append(dict(job=current,target=s.ml_target,frames=len(x),max_joint_error_m=error,device=result['device'],elapsed_seconds=result['elapsed_seconds']))
ns['load_result']('demo_mammal',False)
assert s['active_model_label']=='Independent v1'
for key in ns['TARGETS']:
    s.ml_target=key
    assert [k for k in ns['TARGETS'] if not bpy.data.collections['ML_TARGET_'+k].hide_viewport]==[key]
ns['refresh_history']();ns['load_result'](job_id,False);s.ml_history=job_id
assert [m.frame for m in s.timeline_markers]==[61,111]
source=(REPO/'motion_lab/blender_ui.py').read_text();bpy.data.texts['MOTION_LAB_UI.py'].clear();bpy.data.texts['MOTION_LAB_UI.py'].write(source)
assert Path(pending['addon']).read_text()==source
assert bpy.ops.motion_lab.save()=={'FINISHED'}
master=BASE/'motion_lab.blend';backup=BASE/'motion_lab_before_official_v2.blend'
if not backup.exists():shutil.copy2(master,backup)
blocks={s,bpy.data.texts['MOTION_LAB_UI.py']}|{a for a in bpy.data.actions if a.name.startswith('ML_')}
bpy.data.libraries.write(str(master),blocks)
report=dict(status='passed',model='Official UniMate v2',records=records,legacy_history=True,target_visibility=True,autoplay=True if not bpy.app.background else None,addon_matches_source=True,master=str(master),backup=str(backup),gpu_available=all(r['device']=='cuda' for r in records),mode='background' if bpy.app.background else 'live')
report_name='official_v2_saved_validation.json' if bpy.app.background else 'official_v2_validation.json'
(BASE/report_name).write_text(json.dumps(report,indent=2)+'\n')
if not bpy.app.background:ns['load_result'](job_id,True)
print('OFFICIAL_V2_VALIDATED',json.dumps(report))
