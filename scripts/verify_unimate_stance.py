"""Reopen the saved comparison: raw FK, rest frames, rigid links and selector."""
import bpy,json
from pathlib import Path
import numpy as np
from mathutils import Vector
base=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate');out=base/'pilgrim_stance_001';m=json.loads((out/'run.json').read_text());scale=json.loads((out/'asset_validation.json').read_text())['scale'];s=bpy.data.scenes['PILGRIM_UniMate_STANCE'];rigs=json.loads(s['rigs']);records=[];max_mesh=0.;max_reference=0.
ns={'__name__':'stance_verify'};exec(bpy.data.texts['UNIMATE_STANCE_UI.py'].as_string(),ns);s.unimate_stance_case='REFERENCE';bpy.context.view_layer.update()
for variant,name in rigs.items():
    rig=s.objects[name];c=np.load(out/'conditions'/variant/'cond.npy',allow_pickle=True).item()['Pilgrim']
    for j,n in enumerate(c['joint_names']):
        x=c['tpos_first_frame'][j]/scale;max_reference=max(max_reference,(rig.pose.bones[n].head-Vector((x[0],-x[2],x[1]))).length)
assert max_reference<2e-5,max_reference
for r in m['runs']:
    rig=s.objects[rigs[r['variant']]];a=bpy.data.actions['UNI_'+r['label']+'_s'+str(r['seed'])];assert a['feature_sha256']==r['feature_sha256'] and a['cond_path']==r['cond_path'];rig.animation_data.action=a
    if a.slots:rig.animation_data.action_slot=a.slots[0]
    assert not any(b.constraints for b in rig.pose.bones);d=np.load(Path(r['path'])/'raw_kinematics.npz');names=list(d['names']);error=0.
    links=[o for o in s.objects if o.name.startswith('STANCE_'+r['variant']+'_LINK_')]
    for frame,x in enumerate(d['positions']/scale,1):
        s.frame_set(frame);bpy.context.view_layer.update();positions={n:Vector((x[j,0],-x[j,2],x[j,1])) for j,n in enumerate(names)}
        for n in names:error=max(error,(rig.pose.bones[n].head-positions[n]).length)
        # Evaluate every visible link at six spread-out frames per clip.
        if frame in [1,12,24,36,48,60]:
            deps=bpy.context.evaluated_depsgraph_get()
            for o in links:
                obj=o.evaluated_get(deps);mesh=obj.to_mesh();verts=[obj.matrix_world@v.co for v in mesh.vertices];obj.to_mesh_clear();p=rig.matrix_world@positions[o['source_parent_joint']];q=rig.matrix_world@positions[o['source_child_joint']];axis=(q-p).normalized();verts.sort(key=lambda v:(v-p).dot(axis));a0=sum(verts[:8],Vector())/8;a1=sum(verts[-8:],Vector())/8;max_mesh=max(max_mesh,(a0-p).length,(a1-q).length)
    assert error<2e-4,(a.name,error);records.append(dict(action=a.name,max_joint_error_design_m=error))
assert max_mesh<2e-4,max_mesh
s.unimate_stance_case='REFERENCE';bpy.ops.unimate.stance_step(delta=1);assert s['active_case']=='walk_9700';bpy.ops.unimate.stance_step(delta=-1);assert s['active_case']=='REFERENCE'
result=dict(status='passed',raw_actions=18,reference_actions=2,reference_joint_max_error_design_m=max_reference,max_raw_joint_error_design_m=max(r['max_joint_error_design_m'] for r in records),max_link_cap_error_design_m=max_mesh,link_sampling='All22rigid links at frames1,12,24,36,48,60 for every clip; all bone heads every frame.',selector_roundtrip=True,records=records);(out/'saved_blender_validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='records'}))
