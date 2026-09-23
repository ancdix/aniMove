"""Independently verify saved source/robot correspondence and subframe clearance."""
import json,sys,hashlib
from pathlib import Path
import bpy
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from collision import audit
from motion_lab import to_blender,normalize

p=Path(sys.argv[sys.argv.index('--')+1]);r=json.loads((p/'retarget.json').read_text());m=np.load(p/'motion.npz')
source_path=Path(r['source_xyz_path']);assert hashlib.sha256(source_path.read_bytes()).hexdigest()==r['source_xyz_sha256']
xyz=(to_blender(np.load(source_path))-r['origin_blender_units'])*r['source_to_robot_scale'];xyz[...,2]+=r['config']['robot']['foot_radius']
bpy.ops.wm.open_mainfile(filepath=str(p/'anytop_transfer.blend'));scene=bpy.data.scenes['ANYTOP_Source_to_Robot'];bpy.context.window.scene=scene
rig=bpy.data.objects['ANYTOP_ROBOT_'+r['source']['id']]
assert (scene.frame_start,scene.frame_end,scene.render.fps)==(1,r['frames'],r['fps'])
indices=[r['joint_names'].index(l['endpoint']) for l in r['config']['limbs'].values()]
root=r['joint_names'].index(r['config']['root']);chest=r['joint_names'].index(r['config']['chest']);head=r['joint_names'].index(r['config']['head']);nose=r['joint_names'].index(r['config']['nose'])
report={'status':'passed','frames':r['frames'],'fps':r['fps']}
for blend in [0.,1.]:
    rig['ik_fk']=blend;rig.update_tag();errors=[];source_errors=[];core_errors=[];head_errors=[]
    for f in range(r['frames']):
        scene.frame_set(f+1);bpy.context.view_layer.update()
        for j in range(len(r['joint_names'])):source_errors.append(np.linalg.norm(np.array(bpy.data.objects['SOURCE_JOINT_'+str(j)].location)-[-1.65,0,0]-xyz[f,j]))
        for i,key in enumerate('ABCD'):errors.append(np.linalg.norm(np.array(rig.pose.bones['LIMB_'+key+'_1'].tail)-xyz[f,indices[i]]))
        transform=rig.pose.bones['ROOT'].matrix@rig.data.bones['ROOT'].matrix_local.inverted()
        core_errors.append(np.linalg.norm(np.array(transform.translation)-(xyz[f,root]+xyz[f,chest])/2))
        bone=rig.pose.bones['HEAD'];head_errors.append(np.linalg.norm(np.array((bone.tail-bone.head).normalized())-normalize(xyz[f,nose]-xyz[f,head])))
    result=dict(max_foot_error=max(errors),max_displayed_source_error=max(source_errors),max_core_error=max(core_errors),max_head_direction_error=max(head_errors))
    assert max(result.values())<1e-4,result
    report['FK' if blend==0 else 'IK']=result
rig['ik_fk']=0.;rig.update_tag();poses=[];cores=[];rotations=[];headings=[];minz=float('inf')
for f in np.arange(1,r['frames']+.001,.25):
    scene.frame_set(int(f),subframe=float(f-int(f)));bpy.context.view_layer.update();graph=bpy.context.evaluated_depsgraph_get();ev=rig.evaluated_get(graph)
    poses.append([[list(ev.pose.bones['LIMB_'+k+'_0'].head),list(ev.pose.bones['LIMB_'+k+'_1'].head),list(ev.pose.bones['LIMB_'+k+'_1'].tail)] for k in 'ABCD'])
    transform=ev.pose.bones['ROOT'].matrix@ev.data.bones['ROOT'].matrix_local.inverted();cores.append(list(transform.translation));rotations.append(np.array(transform.to_3x3()))
    bone=ev.pose.bones['HEAD'];headings.append(list((bone.tail-bone.head).normalized()))
    for obj in rig.users_collection[0].objects:
        if obj.type=='MESH':
            mesh=obj.evaluated_get(graph);minz=min(minz,min((mesh.matrix_world@v.co).z for v in mesh.data.vertices))
collisions=audit(np.array(poses),np.array(cores),np.array(rotations),np.array(headings));assert collisions['margin_violation_count']==0,collisions['worst']
assert minz>=scene['display_floor_z']-1e-5
report.update(dense_samples=len(poses),sample_rate=r['fps']*4,collision=collisions,minimum_robot_mesh_z=minz,display_floor_z=scene['display_floor_z'],floor_note='Display plinth below the raw source feet; not a contact-corrected physical floor. Source drift/height remains.')
(p/'transfer_validation.json').write_text(json.dumps(report,indent=2)+'\n');print('TRANSFER_VERIFIED',json.dumps(report))
