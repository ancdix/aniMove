"""Export existing rigid blockout geometry in Motion Lab's upright bind space."""
import bpy,hashlib,json
from pathlib import Path
from mathutils import Vector
ROOT=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove')
BASE=ROOT/'unimate/motion_lab_v001'
source=ROOT/'pilgrim_machine/blockout_v004/pilgrim_blockout.blend'
mapping=json.loads((ROOT/'unimate/pilgrim_canonical_v002/asset_validation.json').read_text())['canonical_to_original']
reverse={old:new for new,old in mapping.items()}
rig=bpy.data.objects['PILGRIM_RIG']
target=next(t for t in json.loads((BASE/'targets.json').read_text()) if t['id']=='Pilgrim')
rest={n:Vector((v[0],-v[2],v[1])) for n,v in zip(target['names'],target['rest'])}
shift=rest['Hips']-rig.data.bones['ROOT'].head_local
assert max((rig.data.bones[old].head_local+shift-rest[new]).length for new,old in mapping.items())<2e-5
parts=[]
for obj in bpy.data.collections['PILGRIM_BODY'].objects:
    if obj.type!='MESH':continue
    assert any(m.type=='ARMATURE' and m.object==rig for m in obj.modifiers)
    assert len(obj.vertex_groups)==1
    old=obj.vertex_groups[0].name
    # Mounts follow the supporting body joint, without adding model joints or IK.
    bone=reverse[rig.data.bones[old].parent.name if old.startswith('CARRIER_') else old]
    assert all(len(v.groups)==1 and abs(v.groups[0].weight-1)<1e-6 for v in obj.data.vertices)
    parts.append(dict(name=obj.name,bone=bone,source_bone=old,vertices=[list(obj.matrix_world@v.co+shift) for v in obj.data.vertices],faces=[list(p.vertices) for p in obj.data.polygons],smooth=[p.use_smooth for p in obj.data.polygons],material=obj.data.materials[0].name,color=list(obj.data.materials[0].diffuse_color)))
assert len(parts)>50
asset=dict(version=1,source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),reference_target='Pilgrim',source_to_lab_translation=list(shift),parts=parts)
path=BASE/'pilgrim_model.json';path.write_text(json.dumps(asset,separators=(',',':'))+'\n')
print('PILGRIM_MODEL_EXPORTED',len(parts),'parts',sum(len(p['vertices']) for p in parts),'vertices',str(path))
