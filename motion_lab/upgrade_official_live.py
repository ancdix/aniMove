"""Refresh the installed UI, preserve the user's scenes, and test official generation."""
import bpy,importlib,json,shutil,time
from pathlib import Path
REPO=Path('/home/ipsedesktop/Documents/GitHub/aniMove')
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001')
old=bpy.app.driver_namespace.get('motion_lab_ui')
assert not old or old.get('JOB') is None,'A user generation is still running'
prior_scenes={s.name:set(s.objects.keys()) for s in bpy.data.scenes}
prior_actions=set(bpy.data.actions.keys())
addon_dir=Path(bpy.utils.user_resource('SCRIPTS',path='addons',create=True))
if old:old['unregister']()
shutil.copy2(REPO/'motion_lab/blender_ui.py',addon_dir/'animove_motion_lab.py')
bpy.utils.refresh_script_paths();importlib.invalidate_caches()
import animove_motion_lab
module=importlib.reload(animove_motion_lab)
if 'animove_motion_lab' in bpy.context.preferences.addons:module.register()
else:bpy.ops.preferences.addon_enable(module='animove_motion_lab')
if module.SCENE not in bpy.data.scenes:
    with bpy.data.libraries.load(str(BASE/'motion_lab.blend'),link=False) as (source,target):
        target.scenes=[module.SCENE]
        target.actions=[name for name in source.actions if name.startswith('ML_') and name not in bpy.data.actions]
s=bpy.data.scenes[module.SCENE];bpy.context.window.scene=s
text=bpy.data.texts.get('MOTION_LAB_UI.py') or bpy.data.texts.new('MOTION_LAB_UI.py')
text.clear();text.write((REPO/'motion_lab/blender_ui.py').read_text())
bpy.ops.wm.save_userpref()
assert all(objects==set(bpy.data.scenes[name].objects.keys()) for name,objects in prior_scenes.items())
assert prior_actions.issubset(bpy.data.actions.keys())
s.ml_target='Mammal';s.ml_prompt='An object walks forward on all fours.';s.ml_seed=9801;s.ml_seconds=4;s.ml_autoplay=True;s.ml_follow=True
module.show_target(s,'Mammal',rest=True)
assert bpy.ops.motion_lab.generate()=={'FINISHED'}
pending=dict(job=module.JOB[1].name,started=time.time(),preserved_scenes=list(prior_scenes),preserved_actions=len(prior_actions),addon=str(addon_dir/'animove_motion_lab.py'))
(BASE/'official_v2_pending.json').write_text(json.dumps(pending,indent=2)+'\n')
print('OFFICIAL_V2_UI_STARTED',json.dumps(pending))
