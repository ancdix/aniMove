"""Export only the existing Pilgrim motion topology and an innocuous registration clip."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector

p=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/pilgrim_registration_v001');p.mkdir(exist_ok=False)
d=json.loads(Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/pilgrim_machine/motion_harvest_001/skeleton.json').read_text())
names=['Hips','Spine','Chest','UpperChest','Neck','Head','HeadTip','LeftUpperArm','LeftForearm','LeftHand','LeftFingers','RightUpperArm','RightForearm','RightHand','RightFingers','LeftThigh','LeftShin','LeftFoot','LeftToes','RightThigh','RightShin','RightFoot','RightToes']
rest=[Vector((v[0],-v[2],v[1])) for v in d['rest']]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
arm=bpy.data.armatures.new('PilgrimMotionSkeleton');rig=bpy.data.objects.new('PilgrimMotionSkeleton',arm);bpy.context.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for i,name in enumerate(names):
    bone=arm.edit_bones.new(name);bone.head=rest[i]
    children=[j for j,pa in enumerate(d['parents']) if pa==i]
    if children:bone.tail=rest[children[0]]
    else:
        direction=(rest[i]-rest[d['parents'][i]]).normalized();bone.tail=rest[i]+direction*.08
    if d['parents'][i]>=0:bone.parent=arm.edit_bones[names[d['parents'][i]]]
    bone.use_deform=True
bpy.ops.object.mode_set(mode='OBJECT')
# Small rigid struts make a real skinned GLB while keeping this an inference proxy.
verts=[];faces=[];groups=[]
for i,name in enumerate(names):
    bone=arm.bones[name];head=bone.head_local;tail=bone.tail_local;axis=(tail-head).normalized();side=axis.cross(Vector((1,0,0)))
    if side.length<.1:side=axis.cross(Vector((0,0,1)))
    side.normalize();other=axis.cross(side).normalized();base=len(verts)
    for center in [head,tail]:
        for x,y in [(-1,-1),(-1,1),(1,1),(1,-1)]:verts.append(center+.018*(x*side+y*other))
    for face in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:faces.append(tuple(base+j for j in face))
    groups.append(list(range(base,base+8)))
mesh=bpy.data.meshes.new('MotionProxy');mesh.from_pydata(verts,[],faces);mesh.update();obj=bpy.data.objects.new('MotionProxy',mesh);bpy.context.collection.objects.link(obj);obj.parent=rig
for name,indices in zip(names,groups):obj.vertex_groups.new(name=name).add(indices,1,'REPLACE')
mod=obj.modifiers.new('Rigid motion skin','ARMATURE');mod.object=rig
scene=bpy.context.scene;scene.render.fps=30;scene.frame_start=1;scene.frame_end=90
for f in range(1,91):
    phase=2*math.pi*(f-1)/89
    for i,name in enumerate(names):
        pb=rig.pose.bones[name];pb.rotation_mode='XYZ';pb.rotation_euler=(0,0,0)
        if i in [1,2,3,4,5]:pb.rotation_euler.x=math.radians(.6)*math.sin(phase+i*.3)*(-1 if i%2 else 1)
        pb.keyframe_insert('rotation_euler',frame=f)
    rig.pose.bones[names[0]].location.x=.015*math.sin(phase);rig.pose.bones[names[0]].keyframe_insert('location',frame=f)
rig.animation_data.action.name='Registration_Only_Not_Generated'
scene.frame_set(1);bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);obj.select_set(True);bpy.context.view_layer.objects.active=rig
assert len(arm.bones)==23 and not any(pb.constraints for pb in rig.pose.bones)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'pilgrim_registration.blend'))
bpy.ops.export_scene.gltf(filepath=str(p/'Pilgrim.glb'),export_format='GLB',use_selection=True,export_animations=True,export_frame_range=True,export_force_sampling=True)
manifest=dict(source='Existing Pilgrim 23-joint skeleton, unchanged joint positions/parents; rigid strut skin is a diagnostic proxy.',names=names,original_names=d['names'],parents=d['parents'],rest_source_y_up=d['rest'],source_to_blender='(x,-z,y)',fps=30,frames=90,registration='0.6-degree alternating torso sway and 1.5cm lateral root shift only; not generated, not a target action.',helper_bones=0,face_r='RightThigh',face_l='LeftThigh')
(p/'registration.json').write_text(json.dumps(manifest,indent=2)+'\n');print('PILGRIM_EXPORT',json.dumps(manifest))
