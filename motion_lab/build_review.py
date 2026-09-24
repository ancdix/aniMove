"""Build the native working surface and verify generated Actions on all targets."""
import bpy,json
from pathlib import Path
import numpy as np
REPO=Path('/home/ipsedesktop/Documents/GitHub/aniMove');BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001')
bpy.ops.wm.read_factory_settings(use_empty=True);ns={'__name__':'motion_lab_review'};exec((REPO/'motion_lab/blender_ui.py').read_text(),ns);ns['register']();s=ns['ensure_scene']();bpy.context.window.scene=s;records=[]
for key,t in ns['TARGETS'].items():
    s.ml_target=key;ns['show_target'](s,key,rest=True);s.render.filepath=str(BASE/(key+'_reference.png'));bpy.ops.render.render(write_still=True)
    job=BASE/'jobs'/('demo_'+key.lower())
    if not (job/'result.json').exists():continue
    ns['load_result'](job.name,False);rig=s.objects['ML_RIG_'+key];x=np.load(job/'kinematics.npz')['positions'];err=0.;mesherr=0
    for f in range(len(x)):
        s.frame_set(f+1);bpy.context.view_layer.update();err=max(err,max((rig.pose.bones[n].head-ns['convert'](x[f,j])).length for j,n in enumerate(t['names'])))
        if f in [0,29,59]:
            deps=bpy.context.evaluated_depsgraph_get()
            for obj in bpy.data.collections['ML_TARGET_'+key].objects:
                if 'joint_parent' not in obj:continue
                evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh();verts=[evaluated.matrix_world@v.co for v in mesh.vertices];evaluated.to_mesh_clear();p=ns['convert'](x[f,obj['joint_parent']]);q=ns['convert'](x[f,obj['joint_child']]);axis=(q-p).normalized();verts.sort(key=lambda v:(v-p).dot(axis));v0=sum(verts[:10],ns['Vector']())/10;v1=sum(verts[-10:],ns['Vector']())/10;mesherr=max(mesherr,(v0-p).length,(v1-q).length)
    assert err<2e-4 and mesherr<2e-4,(key,err,mesherr);records.append(dict(target=key,frames=len(x),bone_error_m=err,mesh_error_m=mesherr));s.frame_set(15);s.render.filepath=str(BASE/(key+'_motion.png'));bpy.ops.render.render(write_still=True)
long=BASE/'jobs/demo_mammal_long'
if (long/'result.json').exists():
    ns['load_result'](long.name,False);assert s.frame_end==120;records.append(dict(target='Mammal_long',frames=120,seams=[v.frame for v in s.timeline_markers]))
ns['load_result']('demo_mammal',False);s.ml_history='demo_mammal';s['status']='Ready — choose a target and enter a prompt';bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'motion_lab.blend'));(BASE/'blender_validation.json').write_text(json.dumps(dict(status='passed',records=records),indent=2)+'\n');print(json.dumps(records))
