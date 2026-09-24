"""Raw FK -> native Blender Actions, with numerical pose verification (no solve)."""
import argparse,json,sys,math
from pathlib import Path
import bpy,numpy as np
from mathutils import Matrix,Vector,Quaternion
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate')
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,default=BASE/'pilgrim_harvest_001');p.add_argument('--limit',type=int);a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
run=json.loads((a.run/'run.json').read_text());validation=json.loads((BASE/'pilgrim_canonical_v002/asset_validation.json').read_text());scale=validation['scale']
cond=np.load(BASE/'pilgrim_canonical_v002/cond.npy',allow_pickle=True).item()['Pilgrim'];names=list(cond['joint_names']);parents=list(cond['parents']);rest=np.asarray(cond['tpos_first_frame'])/scale
basis=Matrix.Rotation(math.pi/2,4,'X');qb=basis.to_quaternion()
def convert(v):return Vector((float(v[0]),float(-v[2]),float(v[1])))
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.name='PILGRIM_UniMate_RAW';scene.render.fps=30;scene.frame_start=1;scene.frame_end=60
scene['RAW_WARNING']='Raw UniMate; no IK, guides, smoothing, contact correction or seamless loop. Playback wrap is a hard reset.'
arm=bpy.data.armatures.new('UniMate_23J');rig=bpy.data.objects.new('PILGRIM_UniMate_RAW_Rig',arm);scene.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for j,n in enumerate(names):
    b=arm.edit_bones.new(n);b.head=convert(rest[j]);children=[i for i,p in enumerate(parents) if p==j]
    d=convert(rest[children[0]]-rest[j]) if children else convert(rest[j]-rest[parents[j]]).normalized()*.12
    b.tail=b.head+d
    if parents[j]>=0:b.parent=arm.edit_bones[names[parents[j]]]
bpy.ops.object.mode_set(mode='OBJECT');rig.animation_data_create();rests=[b.matrix_local.copy() for b in arm.bones]
# Bone creation order and iteration order must agree explicitly.
rests=[arm.bones[n].matrix_local.copy() for n in names]
for pb in rig.pose.bones:pb.rotation_mode='QUATERNION'
records=[]
for entry in run['runs'][:a.limit]:
    data=np.load(Path(entry['path'])/'raw_kinematics.npz');x=data['positions']/scale;q=data['global_quaternions_wxyz'];frames=len(x)
    action=bpy.data.actions.new('UNI_'+entry['label']+'_s'+str(entry['seed']));action.use_fake_user=True;rig.animation_data.action=action
    action['prompt']=entry['prompt'];action['seed']=entry['seed'];action['CFG']=run['cfg'];action['raw_path']=entry['path'];action['postprocessing']='none: stock FK, coordinate/scale conversion only';action['feature_sha256']=entry.get('feature_sha256','see run.json')
    action['bounds_min']=[float(t) for t in x.min((0,1))];action['bounds_max']=[float(t) for t in x.max((0,1))]
    prev=[None]*len(names);max_error=0.;local_shift=0.
    for f in range(frames):
        desired=[]
        for j,n in enumerate(names):
            rot=qb@Quaternion(tuple(q[f,j]))@qb.inverted()@rests[j].to_quaternion()
            desired.append(Matrix.LocRotScale(convert(x[f,j]),rot,Vector((1,1,1))))
        for j,n in enumerate(names):
            local=rests[j].inverted()@desired[j] if parents[j]<0 else rests[j].inverted()@rests[parents[j]]@desired[parents[j]].inverted()@desired[j]
            pb=rig.pose.bones[n];loc,rot,_=local.decompose()
            if prev[j] is not None and rot.dot(prev[j])<0:rot.negate()
            prev[j]=rot.copy();pb.location=loc;pb.rotation_quaternion=rot;pb.scale=(1,1,1)
            if parents[j]>=0:local_shift=max(local_shift,loc.length)
            pb.keyframe_insert('location',frame=f+1,group=n);pb.keyframe_insert('rotation_quaternion',frame=f+1,group=n)
        scene.frame_set(f+1);bpy.context.view_layer.update()
        max_error=max(max_error,max((rig.pose.bones[n].head-convert(x[f,j])).length for j,n in enumerate(names)))
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for kp in fc.keyframe_points:kp.interpolation='LINEAR'
    assert max_error<2e-4,(action.name,max_error)
    records.append(dict(action=action.name,frames=frames,max_joint_error_design_m=max_error,max_nonroot_translation=local_shift));print('ACTION',action.name,max_error,flush=True)
# Rigid colored struts visualize exact bone positions. Not the final Pilgrim mesh.
colors={'A':(.16,.72,.8,1),'B':(.85,.35,.2,1),'C':(.38,.69,.31,1),'D':(.62,.35,.85,1),'core':(.78,.69,.48,1)}
mats={}
for k,color in colors.items():
    mat=bpy.data.materials.new('UniMate_'+k);mat.diffuse_color=color;mats[k]=mat
for j in range(1,len(names)):
    old=validation['canonical_to_original'][names[j]];family=old[0] if old[0] in 'ABCD' and '_' in old else 'core';p=parents[j]
    start=convert(rest[p]);end=convert(rest[j]);mid=(start+end)/2;length=(end-start).length
    bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=.042 if family=='core' else .034,depth=length,location=mid);o=bpy.context.object;o.name='RAW_Link_'+names[j];o.rotation_mode='QUATERNION';o.rotation_quaternion=(end-start).to_track_quat('Z','Y');o.data.materials.append(mats[family])
    # Bind each rigid link to its parent rotation; no skinning solve or constraints.
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True);group=o.vertex_groups.new(name=names[p]);group.add(list(range(len(o.data.vertices))),1,'REPLACE');mod=o.modifiers.new('Exact raw FK','ARMATURE');mod.object=rig
    o.parent=rig
# Ground grid as geometry, keeping penetrations visible.
mat=bpy.data.materials.new('Grid');mat.diffuse_color=(.13,.17,.2,1)
for axis in range(2):
    for t in range(-12,13):
        bpy.ops.mesh.primitive_cube_add(size=1,location=(t if axis==0 else 0,0 if axis==0 else t,-.007));o=bpy.context.object;o.name='Raw_Grid';o.dimensions=(.014,24,.007) if axis==0 else (24,.014,.007);o.data.materials.append(mat)
camdata=bpy.data.cameras.new('UniMate_RAW_Camera');cam=bpy.data.objects.new(camdata.name,camdata);scene.collection.objects.link(cam);scene.camera=cam;camdata.type='ORTHO'
scene['rig']=rig.name;scene['action_names']=json.dumps([r['action'] for r in records]);scene['source_manifest']=str(a.run/'run.json')
# Utilities are callable from Blender console; no dependency on inference Python.
util='''import bpy,json\nfrom mathutils import Vector\ndef select_clip(name):\n    s=bpy.data.scenes["PILGRIM_UniMate_RAW"];r=s.objects[s["rig"]];a=bpy.data.actions[name];r.animation_data.action=a\n    if a.slots:r.animation_data.action_slot=a.slots[0]\n    lo=Vector(a["bounds_min"]);hi=Vector(a["bounds_max"]);c=(lo+hi)/2;c=Vector((c.x,-c.z,c.y));span=max(hi.x-lo.x,hi.z-lo.z,hi.y-lo.y,3.0)\n    camera=s.camera;camera.location=c+Vector((1.15,-1.5,.85))*span;camera.rotation_euler=(c-camera.location).to_track_quat("-Z","Y").to_euler();camera.data.ortho_scale=span*1.5\n    s.frame_start=1;s.frame_end=int(a.frame_range[1]);s.frame_set(1);s["active_prompt"]=a["prompt"];s["active_clip"]=name\n    for w in bpy.context.window_manager.windows:\n        if w.scene==s:\n            for ar in w.screen.areas:\n                if ar.type=="VIEW_3D":ar.spaces.active.region_3d.view_perspective="CAMERA"\n    return a["prompt"]\n'''
text=bpy.data.texts.new('UNIMATE_REVIEW_UTILITIES.py');text.write(util);namespace={};exec(util,namespace)
selected=next((r['action'] for r in records if r['action']=='UNI_p07_s9400'),records[0]['action']);namespace['select_clip'](selected)
rig.select_set(True);bpy.context.view_layer.objects.active=rig;rig.show_in_front=False;rig.hide_render=True
scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=1280;scene.render.resolution_y=960;scene.render.resolution_percentage=100;scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.background_type='WORLD';scene.world=bpy.data.worlds.new('UniMate_RAW_World');scene.world.color=(.025,.035,.05)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.color_type='MATERIAL';area.spaces.active.overlay.show_overlays=False
readme=bpy.data.texts.new('README_UNIMATE_RAW');readme.write('RAW UniMate text generation: 23 joints, 30fps, 60 frames. No IK, authored guides, cleanup or loop correction. The visual struts are a review proxy. Colors A cyan, B orange, C green, D purple. Grid is at the original canonical floor.\n\nAll clips are Actions UNI_pXX_sNNNN. For automatic framing run UNIMATE_REVIEW_UTILITIES.py in the Text Editor; then select_clip("UNI_p07_s9400") from its namespace or exec it in the Python Console. Action custom properties preserve prompt, seed, CFG and raw source. Playback wrapping is not a seamless generated loop.\n')
ui=bpy.data.texts.new('UNIMATE_REVIEW_UI.py');ui.write((Path(__file__).parent/'unimate_review_ui.py').read_text())
out=a.run/('raw_review_test.blend' if a.limit else 'unimate_raw_master.blend');bpy.ops.wm.save_as_mainfile(filepath=str(out));scene.render.filepath=str(a.run/'blender_raw_preview.png');bpy.ops.render.render(write_still=True)
report=dict(status='passed',actions=len(records),scene=scene.name,blend=str(out),postprocessing='none',records=records);(a.run/('blender_test_validation.json' if a.limit else 'blender_validation.json')).write_text(json.dumps(report,indent=2)+'\n')
