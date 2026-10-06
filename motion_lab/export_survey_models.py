"""Export actual lab blockout bind geometry for the local browser review."""
import bpy,json
from pathlib import Path
REPO=Path('/home/ipsedesktop/Documents/GitHub/aniMove')
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001')
OUT=BASE/'surveys/essential_motion_001_20260930/web/models';OUT.mkdir(parents=True,exist_ok=True)
ns=bpy.app.driver_namespace.get('motion_lab_ui')
if ns is None:
    ns={'__name__':'motion_lab_review'};exec((REPO/'motion_lab/blender_ui.py').read_text(),ns);ns['register']()
s=bpy.data.scenes['UNIMATE_Motion_Lab']
for key,t in ns['TARGETS'].items():
    rig=s.objects['ML_RIG_'+key];rest=t['rest'];names=t['names']
    coll=ns['ensure_pilgrim_model'](s,key) if key in ('Pilgrim','PilgrimQuad') else bpy.data.collections['ML_TARGET_'+key]
    offsets=[];joints=[];colors=[];triangles=[]
    for obj in coll.objects:
        if obj.type!='MESH':continue
        mesh=obj.data;mesh.calc_loop_triangles();start=len(joints)
        color=list(mesh.materials[0].diffuse_color[:3]) if mesh.materials else [.5,.6,.65]
        for vertex in mesh.vertices:
            weights=[g for g in vertex.groups if g.weight>1e-6];assert len(weights)==1 and abs(weights[0].weight-1)<1e-5
            bone=obj.vertex_groups[weights[0].group].name;j=names.index(bone)
            # Hidden target objects can have unevaluated identity matrix_world after
            # a background file load. Reconstruct their authored object transform.
            assert obj.parent==rig and rig.parent is None
            v=rig.matrix_basis@obj.matrix_basis@vertex.co
            p=[v.x,v.z,-v.y]
            offsets.extend([round(p[a]-rest[j][a],7) for a in range(3)]);joints.append(j);colors.extend(color)
        for tri in mesh.loop_triangles:triangles.extend([start+v for v in tri.vertices])
    result=dict(target=key,title=t['title'],offsets=offsets,joints=joints,colors=colors,triangles=triangles,rest=rest,parents=t['parents'],names=names)
    (OUT/(key+'.json')).write_text(json.dumps(result,separators=(',',':')))
    print('EXPORTED',key,len(joints),len(triangles)//3)
