"""Build a plain, rigid Pilgrim blockout with authored pose-envelope animation."""
import json, math, sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_robot_blender import primitive,material,relocate,linear_keys,bone_matrix,empty
from motion_lab import to_blender


def build(d, xyz, poles, collection, controls, prefix='PILGRIM'):
    rest=to_blender(np.array(d['rest']));names=d['names'];parents=d['parents'];ix={n:i for i,n in enumerate(names)}
    mat={k:material(prefix+' '+k,v) for k,v in dict(ivory=(.78,.74,.62),dark=(.075,.085,.085),gold=(.52,.35,.12),sensor=(.9,.64,.22)).items()}
    arm=bpy.data.armatures.new(prefix+'_Skeleton');rig=bpy.data.objects.new(prefix+'_RIG',arm);collection.objects.link(rig)
    bpy.context.view_layer.objects.active=rig;rig.select_set(True);arm.display_type='STICK'
    bpy.ops.object.mode_set(mode='EDIT')
    tails=[]
    for j,n in enumerate(names):
        children=[i for i,p in enumerate(parents) if p==j]
        tail=rest[children[0]] if children else rest[j]+([0,-.14,0] if n.endswith('_3') else [0,0,.12])
        tails.append(tail);b=arm.edit_bones.new(n);b.head=rest[j];b.tail=tail
        if parents[j]>=0:b.parent=arm.edit_bones[names[parents[j]]]
    for key in 'ABCD':
        j=ix[key+'_0'];b=arm.edit_bones.new('CARRIER_'+key);b.head=rest[parents[j]];b.tail=rest[j];b.parent=arm.edit_bones[names[parents[j]]]
    bpy.ops.object.mode_set(mode='OBJECT')
    for pb in rig.pose.bones:pb.rotation_mode='QUATERNION'
    # All matrices are in armature space. Parent-before-child update preserves attachments.
    prev={}
    for f,frame in enumerate(xyz):
        bpy.context.scene.frame_set(f+1)
        for j,n in enumerate(names):
            children=[i for i,p in enumerate(parents) if p==j]
            tail=frame[children[0]] if children else frame[j]+(tails[j]-rest[j])
            pole=(0,-1,0)
            if len(n)==3 and n[0] in 'ABCD':pole=poles[f,'ABCD'.index(n[0])]-frame[ix[n[0]+'_0']]
            pb=rig.pose.bones[n];pb.matrix=bone_matrix(frame[j],tail,pole)
            if not children:
                terminal=arm.bones[n].matrix_local.copy();terminal.translation=Vector(frame[j]);pb.matrix=terminal
            bpy.context.view_layer.update()
            if n in prev and pb.rotation_quaternion.dot(prev[n])<0:pb.rotation_quaternion.negate()
            prev[n]=pb.rotation_quaternion.copy()
            pb.keyframe_insert('location',frame=f+1);pb.keyframe_insert('rotation_quaternion',frame=f+1)
        for key in 'ABCD':
            j=ix[key+'_0'];pb=rig.pose.bones['CARRIER_'+key];pb.matrix=bone_matrix(frame[parents[j]],frame[j]);bpy.context.view_layer.update()
            if pb.name in prev and pb.rotation_quaternion.dot(prev[pb.name])<0:pb.rotation_quaternion.negate()
            prev[pb.name]=pb.rotation_quaternion.copy();pb.keyframe_insert('location',frame=f+1);pb.keyframe_insert('rotation_quaternion',frame=f+1)
    rig.animation_data.action.name='PILGRIM_Authored_Pose_Envelope_v001';rig.animation_data.action.use_fake_user=True;linear_keys(rig)
    # Basic solids deliberately stand in for armor, mechanisms, and hand assemblies.
    def cube(n,c,s,bone,color='ivory',rotation=None):
        obj=primitive(prefix+'_'+n,'cube',c,s,mat[color],collection,rig,bone,rotation);obj.modifiers.remove(obj.modifiers[-1]);return obj
    def sphere(n,c,r,bone,color='gold'):
        return primitive(prefix+'_'+n,'sphere',c,(r,)*3,mat[color],collection,rig,bone)
    def link(n,a,b,width,depth,bone,color='ivory'):
        v=Vector(b-a);return cube(n,(a+b)/2,(width,depth,max(.01,v.length*.42)),bone,color,v.to_track_quat('Z','Y'))
    cube('CORE',rest[0],(.22,.17,.13),'ROOT','dark')
    for n in ['ROOT','SPINE_01','SPINE_02','SPINE_03','NECK','HEAD']:
        j=ix[n];a,b=rest[j],tails[j];link(n+'_AXIS',a,b,.085,.07,n,'dark')
        if n!='ROOT':
            for sign in [-1,1]:link(n+'_TOWER_'+str(sign),a+[sign*.125,0,0],b+[sign*.125,0,0],.055,.13,n)
    sphere('SENSOR_ORB',rest[ix['HEAD']]+[0,-.025,.10],.115,'HEAD','sensor')
    def torus(n,center,radius,minor,bone,rotation=(0,0,0)):
        bpy.ops.mesh.primitive_torus_add(major_segments=48,minor_segments=8,major_radius=radius,minor_radius=minor,location=center,rotation=rotation)
        obj=bpy.context.object;obj.name=prefix+'_'+n;relocate(obj,collection)
        bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        obj.data.materials.append(mat['gold']);g=obj.vertex_groups.new(name=bone);g.add(list(range(len(obj.data.vertices))),1,'REPLACE');mod=obj.modifiers.new('Rigid','ARMATURE');mod.object=rig;return obj
    # Ring plane follows the spine-to-neck axis; mesh is built in its rest orientation.
    ring_center=rest[ix['SPINE_03']]+(rest[ix['NECK']]-rest[ix['SPINE_03']])/np.linalg.norm(rest[ix['NECK']]-rest[ix['SPINE_03']])*d['ring'].get('axial_offset',0.)
    torus('WAIST_RING',ring_center,d['ring']['radius'],d['ring']['tube_radius'],d['ring'].get('carrier','SPINE_03'))
    torus('HALO',rest[ix['HEAD']]+[0,.09,.16],.26,.012,'HEAD',(math.pi/2,0,0))
    for key in 'ABCD':
        attach=ix[key+'_0'];parent=parents[attach]
        link(key+'_CARRIER',rest[parent],rest[attach],.055,.055,'CARRIER_'+key,'dark')
        for k in range(3):
            n=key+'_'+str(k);j=ix[n];a,b=rest[j],rest[ix[key+'_'+str(k+1)]]
            sphere(n+'_JOINT',a,.078,n,'dark')
            inset=d.get('geometry',{}).get('upper_shell_proximal_inset_fraction',0.) if key in 'AB' and k==0 else 0.
            link(n+'_SEGMENT',a+inset*(b-a),b,.067 if k<2 else .045,.063,n)
        n=key+'_3';p=rest[ix[n]]
        cube(key+'_PALM',p+[0,-.015,-.017],(.10,.14,.043),n)
        # Three grouped toe/finger blocks only: no individual digit rig yet.
        for q in [-1,0,1]:cube(key+'_DIGIT_'+str(q),p+[q*.065,-.20,-.035],(.027,.08,.025),n,'dark')
    # Editable world targets and poles; distal rotation is held by FK/world orientation.
    for li,key in enumerate('ABCD'):
        rig['ik_'+key]=0.0;rig.id_properties_ui('ik_'+key).update(min=0,max=1)
        target=empty(prefix+'_IK_'+key,controls,'CUBE',.12);pole=empty(prefix+'_POLE_'+key,controls,'SPHERE',.08)
        js=[ix[key+'_'+str(i)] for i in range(4)]
        target['note']='Wrist IK target. Distal and palm orientation remain in the baked FK pose in this P0 prototype.'
        for f in range(len(xyz)):
            target.location=xyz[f,js[2]];pole.location=poles[f,li]
            target.keyframe_insert('location',frame=f+1);pole.keyframe_insert('location',frame=f+1)
        linear_keys(target);linear_keys(pole)
        pb=rig.pose.bones[key+'_1'];ik=pb.constraints.new('IK');ik.name='Prototype wrist IK';ik.target=target;ik.pole_target=pole;ik.chain_count=2;ik.use_stretch=False;ik.iterations=1000
        curve=ik.driver_add('influence');v=curve.driver.variables.new();v.name='blend';v.targets[0].id=rig;v.targets[0].data_path='["ik_'+key+'"]';curve.driver.expression='blend'
        # Defaults are baked FK; IK is exposed as experimental until its poles are verified.
    # Match IK bend planes to the baked pose instead of exposing an uncalibrated pole.
    constraints=[rig.pose.bones[k+'_1'].constraints['Prototype wrist IK'] for k in 'ABCD']
    for key in 'ABCD':rig['ik_'+key]=1.
    rig.update_tag();max_error=0.
    for f in range(len(xyz)):
        bpy.context.scene.frame_set(f+1);bpy.context.view_layer.update()
        for key,ik in zip('ABCD',constraints):
            hip,desired,tip=[Vector(xyz[f,ix[key+'_'+str(j)]]) for j in range(3)];axis=(tip-hip).normalized()
            def radial(p):
                v=p-hip;return (v-axis*v.dot(axis)).normalized()
            def angle(a,b):return math.atan2(axis.dot(a.cross(b)),a.dot(b))
            wanted=radial(desired)
            for _ in range(8):
                current=radial(rig.pose.bones[key+'_1'].head);err=angle(current,wanted)
                if abs(err)<1e-6:break
                initial=ik.pole_angle;step=-.01 if initial>3.1 else .01;ik.pole_angle=initial+step;bpy.context.view_layer.update()
                derivative=angle(current,radial(rig.pose.bones[key+'_1'].head))/step
                if abs(derivative)<.1:raise RuntimeError('Degenerate Pilgrim IK pole')
                corrected=initial+err/derivative;ik.pole_angle=math.atan2(math.sin(corrected),math.cos(corrected));bpy.context.view_layer.update()
            ik.keyframe_insert('pole_angle',frame=f+1)
            max_error=max(max_error,(rig.pose.bones[key+'_1'].head-desired).length,(rig.pose.bones[key+'_1'].tail-tip).length)
    for key in 'ABCD':rig['ik_'+key]=0.
    rig.update_tag();linear_keys(rig);rig['ik_joint_error_at_baked_frames']=max_error
    rig['animation_origin']='AUTHORED pose-envelope verification; not AnyTop motion.'
    rig['rig_stage']='P0: fixed-length baked FK with wrist IK matched at keyed frames. Full distal/palm controls, live snapping and head-target controls remain P2.'
    return rig


def main():
    p=Path(sys.argv[sys.argv.index('--')+1]);d=json.loads((p/'skeleton.json').read_text());m=np.load(p/'pose_envelope.npz')
    path=p/'pilgrim_blockout.blend';assert not path.exists()
    scene=bpy.data.scenes.new('PILGRIM_Blockout');bpy.context.window.scene=scene;scene.frame_start=1;scene.frame_end=len(m['xyz']);scene.render.fps=20
    cols={}
    for name in ['BODY','CONTROLS','STAGE']:
        c=bpy.data.collections.new('PILGRIM_'+name);scene.collection.children.link(c);cols[name]=c
    xyz,poles=to_blender(m['xyz']),to_blender(m['poles']);rig=build(d,xyz,poles,cols['BODY'],cols['CONTROLS'])
    floor=material('Pilgrim stage',(.13,.145,.155));primitive('Pilgrim floor','cube',(0,0,-.04),(200,200,.04),floor,cols['STAGE'])
    bpy.ops.object.camera_add(location=(4,-7,3.6));camera=bpy.context.object;relocate(camera,cols['STAGE']);camera.rotation_euler=(Vector((0,-.1,1.5))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=4.3;scene.camera=camera
    scene.world=bpy.data.worlds.new('Pilgrim world');scene.world.color=(.13,.145,.155)
    scene.render.engine='BLENDER_WORKBENCH';s=scene.display.shading;s.light='STUDIO';s.studio_light='paint.sl';s.color_type='MATERIAL';s.show_shadows=True;s.show_cavity=True;s.cavity_type='BOTH';s.background_type='WORLD'
    scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
    scene['instructions']='Simple Pilgrim blockout. Authored pose checks at 1 upright, 41 bow, 81 one hand, 121 four contacts, 161 turn, 201 recovery. Space plays the authored rig test; no learned motion is shown in this scene. IK defaults off pending P2 controls.'
    scene['asset_directory']=str(p)
    scene['scope']='Authored pose test only. Direct AnyTop samples are in a separate comparison scene.'
    for name,f in d['pose_checks']['authored_pose_frames'].items():scene.timeline_markers.new(name,frame=f)
    report={'source':'authored pose envelope','joint_error':0.,'min_mesh_z':1e9,'evaluated_frames':0}
    for f in range(1,len(xyz)+1,2):
        scene.frame_set(f);dg=bpy.context.evaluated_depsgraph_get();er=rig.evaluated_get(dg)
        got=np.array([er.pose.bones[n].head[:] for n in d['names']]);report['joint_error']=max(report['joint_error'],float(np.linalg.norm(got-xyz[f-1],axis=-1).max()))
        for obj in cols['BODY'].objects:
            if obj.type!='MESH':continue
            e=obj.evaluated_get(dg);mesh=e.to_mesh();low=min((e.matrix_world@v.co).z for v in mesh.vertices);report['min_mesh_z']=min(report['min_mesh_z'],low);e.to_mesh_clear()
        report['evaluated_frames']+=1
    report['status']='passed' if report['joint_error']<1e-4 and report['min_mesh_z']>=-1e-4 else 'needs_fix'
    (p/'blockout_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    scene.frame_set(1)
    for obj in bpy.context.selected_objects:obj.select_set(False)
    rig.select_set(True);bpy.context.view_layer.objects.active=rig
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.color_type='MATERIAL';area.spaces.active.overlay.show_extras=False;area.spaces.active.overlay.show_bones=False
    bpy.data.texts.new('README_PILGRIM_BLOCKOUT').write(scene['instructions']+'\n\n'+json.dumps(d,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    for name,f in d['pose_checks']['authored_pose_frames'].items():
        scene.frame_set(f);scene.render.filepath=str(p/('pose_'+name.lower().replace(' ','_')+'.png'));bpy.ops.render.render(write_still=True)
    print('PILGRIM_BLOCKOUT',json.dumps(report),flush=True)


if __name__=='__main__':main()
