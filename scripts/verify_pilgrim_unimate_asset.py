"""Check canonical GLB/FBX against cond.npy, including names, hierarchy and axes."""
import bpy,json,numpy as np
from pathlib import Path
p=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate');out=p/'pilgrim_canonical_v002'
d=np.load(out/'cond.npy',allow_pickle=True).item()['Pilgrim'];r=json.loads((p/'pilgrim_registration_v001/registration.json').read_text());names=list(d['joint_names']);parents=list(d['parents'])
assert set(names)==set(r['names']) and len(names)==23
order=[r['names'].index(n) for n in names];src=np.array(r['rest_source_y_up'])[order];expected=np.array(d['tpos_first_frame']);scale=float(d['scale_factor'])
predicted=(src-[0,.06,0])*scale;error=float(np.linalg.norm(predicted-expected,axis=-1).max());assert error<1e-5,error
for i,name in enumerate(names):
    old_i=r['names'].index(name);old_p=r['parents'][old_i];expected_parent=r['names'][old_p] if old_p>=0 else None
    assert (names[parents[i]] if parents[i]>=0 else None)==expected_parent
checks=[]
for ext in ['glb','fbx']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if ext=='glb':bpy.ops.import_scene.gltf(filepath=str(out/('Pilgrim_canonical.'+ext)))
    else:bpy.ops.import_scene.fbx(filepath=str(out/('Pilgrim_canonical.'+ext)),use_anim=False)
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
    assert set(rig.data.bones.keys())==set(names)
    points=np.array([(rig.matrix_world@rig.data.bones[n].head_local)[:] for n in names]);yup=points[:,[0,2,1]]*np.array([1,1,-1]);e=float(np.linalg.norm(yup-expected,axis=-1).max());assert e<1e-5,(ext,e)
    for i,n in enumerate(names):assert (rig.data.bones[n].parent.name if rig.data.bones[n].parent else None)==(names[parents[i]] if parents[i]>=0 else None)
    checks.append(dict(format=ext,max_joint_error=e,joints=len(rig.data.bones),min_world_z=float(points[:,2].min())))
report=dict(status='passed',joints=23,removed_joints=[],added_helpers=[],scale=scale,source_to_canonical='(source_Y_up - [0,0.06,0]) * scale; +Y up and +Z forward preserved',source_geometry_max_error=error,checks=checks,canonical_to_original={n:r['original_names'][r['names'].index(n)] for n in names},face=d['face_joint_idxs'])
(out/'asset_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
