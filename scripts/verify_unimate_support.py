"""Reopen and check all support-review Actions against their raw FK."""
import bpy,json
from pathlib import Path
import numpy as np
from mathutils import Vector
base=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate');out=base/'pilgrim_support_review_001';manifest=json.loads((out/'run.json').read_text());scale=json.loads((base/'pilgrim_canonical_v002/asset_validation.json').read_text())['scale'];s=bpy.data.scenes['PILGRIM_UniMate_SUPPORT'];rig=s.objects[s['rig']];checks=[]
for r in manifest['runs']:
    a=bpy.data.actions['UNI_'+r['label']+'_s'+str(r['seed'])];rig.animation_data.action=a
    if a.slots:rig.animation_data.action_slot=a.slots[0]
    assert not any(b.constraints for b in rig.pose.bones)
    assert a['feature_sha256']==r['feature_sha256'] and a['prompt']==r['prompt']
    d=np.load(Path(r['path'])/'raw_kinematics.npz');error=0.
    for frame,x in enumerate(d['positions']/scale,1):
        s.frame_set(frame);bpy.context.view_layer.update()
        for j,name in enumerate(d['names']):error=max(error,(rig.pose.bones[name].head-Vector((x[j,0],-x[j,2],x[j,1]))).length)
    assert error<2e-4,(a.name,error);checks.append(dict(action=a.name,max_error_design_m=error))
ns={'__name__':'support_verify'};exec(bpy.data.texts['UNIMATE_SUPPORT_UI.py'].as_string(),ns);first=json.loads(s['action_names'])[0];s.unimate_support_clip=first;bpy.ops.unimate.support_step(delta=1);assert s['active_clip']!=first;bpy.ops.unimate.support_step(delta=-1);assert s['active_clip']==first
result=dict(status='passed',saved_actions=len(checks),max_joint_error_design_m=max(c['max_error_design_m'] for c in checks),selector_roundtrip=True,checks=checks);(out/'saved_blender_validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
