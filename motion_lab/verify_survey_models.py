import bpy,json
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
repo=Path('/home/ipsedesktop/Documents/GitHub/aniMove');base=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001');root=base/'surveys/essential_motion_001_20260930'
ns={'__name__':'motion_lab_review'};exec((repo/'motion_lab/blender_ui.py').read_text(),ns);ns['register']();s=bpy.data.scenes[ns['SCENE']];bpy.context.window.scene=s
entries=json.loads((root/'state.json').read_text())['entries'];report=[]
for key in ns['TARGETS']:
 e=next(e for e in entries if e['target']==key and e['status']=='complete');ns['load_result'](e['job'],False);s.frame_set(30);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
 a=json.loads((root/'web/models'/(key+'.json')).read_text());d=np.load(base/'jobs'/e['job']/'kinematics.npz');x=d['positions'][29];q=d['global_quaternions_wxyz'][29]
 expected=[ns['convert'](Vector(x[j])+Quaternion(tuple(q[j]))@Vector(a['offsets'][i*3:i*3+3])) for i,j in enumerate(a['joints'])]
 coll=ns['ensure_pilgrim_model'](s,key) if key in ('Pilgrim','PilgrimQuad') else bpy.data.collections['ML_TARGET_'+key]
 actual=[]
 for obj in coll.objects:
  if obj.type!='MESH':continue
  evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh();actual.extend([evaluated.matrix_world@v.co for v in mesh.vertices]);evaluated.to_mesh_clear()
 assert len(expected)==len(actual);error=max((a-b).length for a,b in zip(actual,expected));assert error<2e-5,(key,error)
 report.append(dict(target=key,vertices=len(expected),frame=30,error_m=error))
(root/'viewer_geometry_validation.json').write_text(json.dumps(dict(status='passed',records=report),indent=2));print('VIEWER_MODELS_VALIDATED',json.dumps(report))
