"""Reopen the standalone master and confirm raw animation and controls survive."""
import bpy,json
from pathlib import Path
import numpy as np
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001');REPO=Path('/home/ipsedesktop/Documents/GitHub/aniMove');ns={'__name__':'motion_lab_verify'};exec((REPO/'motion_lab/blender_ui.py').read_text(),ns);ns['register']();s=bpy.data.scenes['UNIMATE_Motion_Lab'];bpy.context.window.scene=s
# Update the embedded fallback to the same installed interface version.
text=bpy.data.texts['MOTION_LAB_UI.py'];text.clear();text.write((REPO/'motion_lab/blender_ui.py').read_text())
errors=[]
for job in ['demo_mammal','demo_mammal_long','demo_bird','demo_insect','demo_pilgrim','demo_pilgrimquad']:
    ns['load_result'](job,False);x=np.load(BASE/'jobs'/job/'kinematics.npz')['positions'];t=ns['TARGETS'][s.ml_target];rig=s.objects['ML_RIG_'+s.ml_target];err=0
    for f in range(len(x)):
        s.frame_set(f+1);bpy.context.view_layer.update();err=max(err,max((rig.pose.bones[n].head-ns['convert'](x[f,j])).length for j,n in enumerate(t['names'])))
    assert err<2e-4;errors.append(dict(job=job,max_error=err,frames=len(x)))
ns['load_result']('demo_mammal',False);s.ml_history='demo_mammal';bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'motion_lab.blend'));(BASE/'saved_validation.json').write_text(json.dumps(dict(status='passed',records=errors,camera_handler_persistent=bool(getattr(ns['follow_frame'],'_bpy_persistent',False))),indent=2)+'\n');print(json.dumps(errors))
