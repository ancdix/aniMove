import bpy,importlib,shutil,json
from pathlib import Path
REPO=Path('/home/ipsedesktop/Documents/GitHub/aniMove');BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001');old=bpy.app.driver_namespace['motion_lab_ui'];assert old['JOB'] is None,'Leave active user generation untouched';s=bpy.data.scenes['UNIMATE_Motion_Lab'];job=s.get('active_result','demo_mammal');addon=Path(bpy.utils.user_resource('SCRIPTS',path='addons'))/'animove_motion_lab.py'
import animove_motion_lab
animove_motion_lab.unregister();shutil.copy2(REPO/'motion_lab/blender_ui.py',addon);module=importlib.reload(animove_motion_lab);module.register();text=bpy.data.texts['MOTION_LAB_UI.py'];text.clear();text.write((REPO/'motion_lab/blender_ui.py').read_text());s.ml_follow=True;module.load_result(job,True)
# Test camera tracking without changing animation.
initial=s.camera.location.copy();s.frame_set(1);start=s.camera.location.copy();rig=s.objects['ML_RIG_'+s.ml_target];root0=rig.pose.bones[module.TARGETS[s.ml_target]['names'][0]].head.copy();s.frame_set(s.frame_end);end=s.camera.location.copy();root1=rig.pose.bones[module.TARGETS[s.ml_target]['names'][0]].head.copy();delta=root1-root0;delta.z=0;assert (end-start-delta).length<1e-5;s.frame_set(1)
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        for region in area.regions:
            if region.type=='UI' and hasattr(region,'active_panel_category'):region.active_panel_category='Motion Lab'
result=dict(status='passed',camera_follow=True,active_result=job,addon_enabled='animove_motion_lab' in bpy.context.preferences.addons);(BASE/'camera_validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
