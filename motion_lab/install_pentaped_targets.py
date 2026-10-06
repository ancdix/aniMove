"""Install validated pentaped targets into the running lab, preserving user work."""
import bpy,importlib,json,shutil
from pathlib import Path
REPO=Path('/home/ipsedesktop/Documents/GitHub/aniMove')
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001')
assert json.loads((BASE/'pentaped_validation.json').read_text())['status']=='passed'
old=bpy.app.driver_namespace['motion_lab_ui'];assert old['JOB'] is None,'Wait for current generation to finish'
s=bpy.data.scenes[old['SCENE']];bpy.context.window.scene=s
prior_actions=set(bpy.data.actions.keys());prior_scenes=set(bpy.data.scenes.keys());prior_objects=set(s.objects.keys())
if bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT')
old['unregister']();addon=Path(bpy.utils.user_resource('SCRIPTS',path='addons'))/'animove_motion_lab.py';shutil.copy2(REPO/'motion_lab/blender_ui.py',addon)
import animove_motion_lab
module=importlib.reload(animove_motion_lab);module.register()
for key in ['PentapedRadial','PentapedTripod']:
    if 'ML_RIG_'+key not in s.objects:module.build_target(s,module.TARGETS[key])
text=bpy.data.texts.get('MOTION_LAB_UI.py') or bpy.data.texts.new('MOTION_LAB_UI.py');text.use_fake_user=True;text.clear();text.write((REPO/'motion_lab/blender_ui.py').read_text())
for job in json.loads((BASE/'pentaped_target_jobs.json').read_text()):module.load_result(job,False)
s.ml_history=job;s.ml_prompt='An object lowers its body while spreading its legs.';s.ml_seconds=2;s.ml_seed=9811
for key in module.TARGETS:
    module.show_target(s,key)
    assert all(bpy.data.collections['ML_TARGET_'+other].hide_viewport==(other!=key) for other in module.TARGETS)
module.show_target(s,'PentapedTripod');s.frame_set(1)
assert prior_actions.issubset(bpy.data.actions.keys()) and prior_scenes.issubset(bpy.data.scenes.keys()) and prior_objects.issubset(s.objects.keys())
master=BASE/'motion_lab.blend';backup=BASE/'motion_lab_before_pentapeds.blend'
if not backup.exists():shutil.copy2(master,backup)
blocks={s,text}|{a for a in bpy.data.actions if a.name.startswith('ML_')}
asset=bpy.data.texts.get('MOTION_LAB_PILGRIM_MODEL.json')
if asset:blocks.add(asset)
bpy.data.libraries.write(str(master),blocks)
report=dict(status='passed',targets=list(module.TARGETS),active_result=job,preserved_actions=len(prior_actions),preserved_scenes=len(prior_scenes))
(BASE/'pentaped_live_validation.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.screen.animation_play();print('PENTAPEDS_INSTALLED',json.dumps(report))
