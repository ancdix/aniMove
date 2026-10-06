"""Build five-limbed targets and verify their generated motion in a saved lab."""
import bpy,json
import numpy as np
from pathlib import Path
REPO=Path('/home/ipsedesktop/Documents/GitHub/aniMove')
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001')
ns={'__name__':'motion_lab_review'};exec((REPO/'motion_lab/blender_ui.py').read_text(),ns);ns['register']()
s=bpy.data.scenes[ns['SCENE']];bpy.context.window.scene=s
if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT')
for key in ['PentapedRadial','PentapedTripod']:
    if 'ML_RIG_'+key not in s.objects:ns['build_target'](s,ns['TARGETS'][key])
records=[]
for job in json.loads((BASE/'pentaped_target_jobs.json').read_text()):
    result=json.loads((BASE/'jobs'/job/'result.json').read_text());key=result['request']['target'];ns['load_result'](job,False)
    rig=s.objects['ML_RIG_'+key];t=ns['TARGETS'][key];x=np.load(BASE/'jobs'/job/'kinematics.npz')['positions'];error=0;mesh_error=0
    for f in range(len(x)):
        s.frame_set(f+1);bpy.context.view_layer.update()
        error=max(error,max((rig.pose.bones[n].head-ns['convert'](x[f,j])).length for j,n in enumerate(t['names'])))
        if f in (0,29,59):
            deps=bpy.context.evaluated_depsgraph_get()
            for obj in bpy.data.collections['ML_TARGET_'+key].objects:
                if obj.type!='MESH':continue
                assert len(obj.vertex_groups)==1
                bone=obj.vertex_groups[0].name;transform=rig.matrix_world@rig.pose.bones[bone].matrix@rig.data.bones[bone].matrix_local.inverted()@obj.matrix_local
                evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh()
                mesh_error=max(mesh_error,max((evaluated.matrix_world@a.co-transform@b.co).length for a,b in zip(mesh.vertices,obj.data.vertices)))
                evaluated.to_mesh_clear()
    assert error<2e-5 and mesh_error<2e-5,(key,error,mesh_error)
    assert result['device']=='cuda' and len(rig.data.bones)==t['joints']
    records.append(dict(target=key,joints=t['joints'],job=job,frames=len(x),fk_error_m=error,mesh_error_m=mesh_error,device=result['device']))
    s.frame_set(30);s.render.resolution_percentage=65;s.render.filepath=str(BASE/(key+'_motion.png'));bpy.ops.render.render(write_still=True)
    ns['show_target'](s,key,rest=True);s.render.filepath=str(BASE/(key+'_reference.png'));bpy.ops.render.render(write_still=True)
ns['load_result'](records[-1]['job'],False);s.frame_set(1);s.render.resolution_percentage=100
text=bpy.data.texts.get('MOTION_LAB_UI.py') or bpy.data.texts.new('MOTION_LAB_UI.py');text.use_fake_user=True;text.clear();text.write((REPO/'motion_lab/blender_ui.py').read_text())
bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'motion_lab_pentapeds_preview.blend'))
report=dict(status='passed',records=records);(BASE/'pentaped_validation.json').write_text(json.dumps(report,indent=2)+'\n');print('PENTAPEDS_VALIDATED',json.dumps(report))
