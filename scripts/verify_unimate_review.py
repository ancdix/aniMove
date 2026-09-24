"""Reopen the saved raw master and verify every Action against source FK."""
import bpy,json
from pathlib import Path
import numpy as np
from mathutils import Vector
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate');run=BASE/'pilgrim_harvest_001';scale=json.loads((BASE/'pilgrim_canonical_v002/asset_validation.json').read_text())['scale'];manifest=json.loads((run/'run.json').read_text());scene=bpy.data.scenes['PILGRIM_UniMate_RAW'];rig=scene.objects[scene['rig']];records=[]
for r in manifest['runs']:
    name='UNI_'+r['label']+'_s'+str(r['seed']);a=bpy.data.actions[name];rig.animation_data.action=a
    if a.slots:rig.animation_data.action_slot=a.slots[0]
    data=np.load(Path(r['path'])/'raw_kinematics.npz');x=data['positions']/scale;names=list(data['names']);error=0.
    assert len(rig.pose.bones)==23 and not any(b.constraints for b in rig.pose.bones)
    for f in range(len(x)):
        scene.frame_set(f+1);bpy.context.view_layer.update()
        for j,n in enumerate(names):error=max(error,(rig.pose.bones[n].head-Vector((x[f,j,0],-x[f,j,2],x[f,j,1]))).length)
    assert error<2e-4,(name,error);assert a['prompt']==r['prompt'] and a['feature_sha256']==r['feature_sha256'];records.append(dict(action=name,max_error_design_m=error))
result=dict(status='passed',saved_actions=len(records),max_joint_error_design_m=max(r['max_error_design_m'] for r in records),constraints=0,records=records);(run/'saved_blender_validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='records'}))
