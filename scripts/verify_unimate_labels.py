"""Verify every saved label Action against original raw FK and provenance."""
import bpy,json
from pathlib import Path
import numpy as np
from mathutils import Vector
base=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate')
out=base/'pilgrim_labels_001';manifest=json.loads((out/'run.json').read_text())
scale=json.loads((base/'pilgrim_canonical_v002/asset_validation.json').read_text())['scale']
s=bpy.data.scenes['PILGRIM_UniMate_LABELS'];rigs=json.loads(s['rigs']);checks=[]
for run in manifest['runs']:
    variant=run['variant'] if not run['repeat_control'] else 'arms_legs'
    rig=s.objects[rigs[variant]];a=bpy.data.actions['UNI_'+run['label']+'_s'+str(run['seed'])]
    rig.animation_data.action=a
    if a.slots:rig.animation_data.action_slot=a.slots[0]
    assert not any(b.constraints for b in rig.pose.bones)
    assert a['feature_sha256']==run['feature_sha256'] and a['prompt']==run['prompt']
    d=np.load(Path(run['path'])/'raw_kinematics.npz');error=0.
    for frame,x in enumerate(d['positions']/scale,1):
        s.frame_set(frame);bpy.context.view_layer.update()
        for j,name in enumerate(d['names']):error=max(error,(rig.pose.bones[name].head-Vector((x[j,0],-x[j,2],x[j,1]))).length)
    assert error<2e-4,(a.name,error)
    checks.append(dict(action=a.name,max_joint_error_design_m=error))
ns={'__name__':'verify_labels_ui'};exec(bpy.data.texts['UNIMATE_LABELS_UI.py'].as_string(),ns)
s.unimate_label_case='p05_9602';bpy.ops.unimate.label_step(delta=1);assert s['active_case']=='p07_9600';bpy.ops.unimate.label_step(delta=-1);assert s['active_case']=='p05_9602'
result=dict(status='passed',saved_actions=len(checks),max_joint_error_design_m=max(c['max_joint_error_design_m'] for c in checks),selector_roundtrip=True,checks=checks)
(out/'saved_blender_validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
