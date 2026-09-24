"""Install the native panel and append its reviewed scene, preserving prior work."""
import bpy,json,shutil,sys,importlib
from pathlib import Path
REPO=Path('/home/ipsedesktop/Documents/GitHub/aniMove');BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001');assert json.loads((BASE/'blender_validation.json').read_text())['status']=='passed'
old_scenes=set(bpy.data.scenes.keys());old_actions=set(bpy.data.actions.keys());old_objects={s.name:set(s.objects.keys()) for s in bpy.data.scenes};name='UNIMATE_Motion_Lab';assert name not in bpy.data.scenes
if bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
with bpy.data.libraries.load(str(BASE/'motion_lab.blend'),link=False) as (source,target):
    target.scenes=[name];target.actions=[a for a in source.actions if a.startswith('ML_')];target.texts=['MOTION_LAB_UI.py']
s=bpy.data.scenes[name];bpy.context.window.scene=s;s.sync_mode='FRAME_DROP'
addon_dir=Path(bpy.utils.user_resource('SCRIPTS',path='addons',create=True));addon_file=addon_dir/'animove_motion_lab.py';shutil.copy2(REPO/'motion_lab/blender_ui.py',addon_file);bpy.utils.refresh_script_paths();importlib.invalidate_caches();bpy.ops.preferences.addon_enable(module='animove_motion_lab');bpy.ops.wm.save_userpref();ns=bpy.app.driver_namespace['motion_lab_ui'];ns['refresh_history']();s.ml_history='demo_mammal';ns['load_result']('demo_mammal',True)
assert old_scenes.issubset(bpy.data.scenes.keys()) and old_actions.issubset(bpy.data.actions.keys());assert all(objects==set(bpy.data.scenes[n].objects.keys()) for n,objects in old_objects.items());assert 'animove_motion_lab' in bpy.context.preferences.addons
result=dict(status='passed',scene=s.name,installed_addon=str(addon_file),preserved_scenes=len(old_scenes),preserved_actions=len(old_actions),active_result=s['active_result'],targets=list(ns['TARGETS']));(BASE/'live_validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
