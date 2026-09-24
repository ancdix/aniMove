"""Two rest-specific FK rigs, exact raw Actions and a reference-pose selector."""
import bpy,json,math
from pathlib import Path
import numpy as np
from mathutils import Matrix,Vector,Quaternion
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate');out=BASE/'pilgrim_stance_001';m=json.loads((out/'run.json').read_text());validation=json.loads((out/'asset_validation.json').read_text());scale=validation['scale'];basis=Matrix.Rotation(math.pi/2,4,'X');qb=basis.to_quaternion()
def convert(v):return Vector((float(v[0]),float(-v[2]),float(v[1])))
bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.name='PILGRIM_UniMate_STANCE';s.render.fps=30;s.frame_start=1;s.frame_end=60;rigs={};records=[]
colors={'A':(.16,.72,.8,1),'B':(.85,.35,.2,1),'C':(.38,.69,.31,1),'D':(.62,.35,.85,1),'core':(.78,.69,.48,1)};mats={}
for k,color in colors.items():mat=bpy.data.materials.new('Stance_'+k);mat.diffuse_color=color;mats[k]=mat
for index,variant in enumerate(m['variants']):
    c=np.load(out/'conditions'/variant/'cond.npy',allow_pickle=True).item()['Pilgrim'];names=list(c['joint_names']);parents=c['parents'];rest=np.asarray(c['tpos_first_frame'])/scale;arm=bpy.data.armatures.new('Stance_'+variant);rig=bpy.data.objects.new('STANCE_RIG_'+variant,arm);s.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
    for j,n in enumerate(names):
        b=arm.edit_bones.new(n);b.head=convert(rest[j]);kids=[i for i,p in enumerate(parents) if p==j];direction=convert(rest[kids[0]]-rest[j]) if kids else convert(rest[j]-rest[parents[j]]).normalized()*.12;b.tail=b.head+direction
        if parents[j]>=0:b.parent=arm.edit_bones[names[parents[j]]]
    bpy.ops.object.mode_set(mode='OBJECT');rig.animation_data_create();rests=[arm.bones[n].matrix_local.copy() for n in names]
    for pb in rig.pose.bones:pb.rotation_mode='QUATERNION'
    reference=bpy.data.actions.new('STN_REFERENCE_'+variant);reference.use_fake_user=True;rig.animation_data.action=reference
    for pb in rig.pose.bones:pb.location=(0,0,0);pb.rotation_quaternion=(1,0,0,0);pb.keyframe_insert('location',frame=1);pb.keyframe_insert('rotation_quaternion',frame=1)
    reference['bounds_min']=rest.min(0).tolist();reference['bounds_max']=rest.max(0).tolist();reference['authorship']='Authored static input reference, not generated animation.'
    for entry in [r for r in m['runs'] if r['variant']==variant]:
        data=np.load(Path(entry['path'])/'raw_kinematics.npz');x=data['positions']/scale;q=data['global_quaternions_wxyz'];action=bpy.data.actions.new('UNI_'+entry['label']+'_s'+str(entry['seed']));action.use_fake_user=True;rig.animation_data.action=action;action['prompt']=entry['prompt'];action['seed']=entry['seed'];action['feature_sha256']=entry['feature_sha256'];action['raw_path']=entry['path'];action['cond_path']=entry['cond_path'];action['reference_stance']=variant;action['postprocessing']='No edits: own-rest FK, axes/scale conversion only.';action['bounds_min']=x.min((0,1)).tolist();action['bounds_max']=x.max((0,1)).tolist();prev=[None]*len(names);error=0.;shift=0.
        for f in range(60):
            desired=[Matrix.LocRotScale(convert(x[f,j]),qb@Quaternion(tuple(q[f,j]))@qb.inverted()@rests[j].to_quaternion(),Vector((1,1,1))) for j in range(len(names))]
            for j,n in enumerate(names):
                local=rests[j].inverted()@desired[j] if parents[j]<0 else rests[j].inverted()@rests[parents[j]]@desired[parents[j]].inverted()@desired[j];loc,rot,_=local.decompose();pb=rig.pose.bones[n]
                if prev[j] is not None and rot.dot(prev[j])<0:rot.negate()
                prev[j]=rot.copy();pb.location=loc;pb.rotation_quaternion=rot;pb.scale=(1,1,1)
                if parents[j]>=0:shift=max(shift,loc.length)
                pb.keyframe_insert('location',frame=f+1,group=n);pb.keyframe_insert('rotation_quaternion',frame=f+1,group=n)
            s.frame_set(f+1);bpy.context.view_layer.update();error=max(error,max((rig.pose.bones[n].head-convert(x[f,j])).length for j,n in enumerate(names)))
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        for kp in fc.keyframe_points:kp.interpolation='LINEAR'
        assert error<2e-4 and shift<2e-4,(error,shift);records.append(dict(action=action.name,variant=variant,max_joint_error_design_m=error,max_nonroot_translation_m=shift))
    rig.animation_data.action=reference
    if reference.slots:rig.animation_data.action_slot=reference.slots[0]
    s.frame_set(1);bpy.context.view_layer.update()
    for j in range(1,len(names)):
        p=parents[j];start=convert(rest[p]);end=convert(rest[j]);old=validation['canonical_to_original'][names[j]];family=old.split('_')[0];family=family if family in mats else 'core';bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=.04 if family=='core' else .033,depth=(end-start).length,location=(start+end)/2);o=bpy.context.object;o.name='STANCE_'+variant+'_LINK_'+names[j];o.rotation_mode='QUATERNION';o.rotation_quaternion=(end-start).to_track_quat('Z','Y');o.data.materials.append(mats[family]);bpy.ops.object.transform_apply(location=False,rotation=True,scale=True);o.vertex_groups.new(name=names[p]).add(list(range(len(o.data.vertices))),1,'REPLACE');mod=o.modifiers.new('Own-reference raw FK','ARMATURE');mod.object=rig;o.parent=rig;o['source_parent_joint']=names[p];o['source_child_joint']=names[j]
    rig.location=(7*(index-.5),0,0);rigs[variant]=rig.name;rig.hide_render=True
    font=bpy.data.curves.new('StanceTitle_'+variant,'FONT');font.body=['UPRIGHT REFERENCE','QUADRUPEDAL REFERENCE'][index];font.align_x='CENTER';font.size=.24;o=bpy.data.objects.new('STANCE_TITLE_'+variant,font);s.collection.objects.link(o);font.materials.append(mats['core'])
mat=bpy.data.materials.new('StanceGrid');mat.diffuse_color=(.13,.17,.2,1)
for axis in range(2):
    for t in range(-16,17):
        bpy.ops.mesh.primitive_cube_add(size=1,location=(t if axis==0 else 0,0 if axis==0 else t,-.007));o=bpy.context.object;o.name='StanceGrid';o.dimensions=(.012,32,.007) if axis==0 else (32,.012,.007);o.data.materials.append(mat)
camdata=bpy.data.cameras.new('StanceCamera');cam=bpy.data.objects.new('StanceCamera',camdata);s.collection.objects.link(cam);s.camera=cam;camdata.type='ORTHO';s.render.resolution_x=1600;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('StanceWorld');s.world.color=(.025,.035,.05)
s['rigs']=json.dumps(rigs);s['cases']=json.dumps({f'{pid}_{seed}':dict(prompt_id=pid,seed=seed,prompt=prompt) for pid,prompt in m['prompts'].items() for seed in m['seeds']});s['active_case']='REFERENCE';s['source_manifest']=str(out/'run.json');s['raw_notice']='Only display X offsets differ from raw world motion. Input references are authored; all generated frames are free.'
t=bpy.data.texts.new('UNIMATE_STANCE_UI.py');t.write((Path(__file__).parent/'unimate_stance_ui.py').read_text());ns={'__name__':'stance_review'};exec(t.as_string(),ns);bpy.app.driver_namespace['unimate_stance_ui']=ns
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.color_type='MATERIAL';area.spaces.active.overlay.show_overlays=False;area.spaces.active.show_region_ui=True
readme=bpy.data.texts.new('README_UNIMATE_STANCE');readme.write('Reference stance ablation: same 23 joints, bone lengths, topology, names, prompts, noise and scale. Reference mode displays authored inputs. Other cases display generated raw 60-frame clips. No first-frame clamp, IK, cleanup or seamless loop. Two independent rigs use their own reference offsets. Constant X display offsets only. Run UNIMATE_STANCE_UI.py after reopening to restore selector. Source: '+str(out))
bpy.ops.wm.save_as_mainfile(filepath=str(out/'stance_review.blend'));s.render.filepath=str(out/'blender_reference_preview.png');bpy.ops.render.render(write_still=True);(out/'blender_validation.json').write_text(json.dumps(dict(status='passed',raw_actions=18,reference_actions=2,rigs=rigs,records=records),indent=2)+'\n');print('BUILD PASSED',max(r['max_joint_error_design_m'] for r in records))
