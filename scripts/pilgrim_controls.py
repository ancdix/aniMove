"""Editable world contacts, distal controls, head controls, and visual FK baking."""
import math
import bpy
import numpy as np
from mathutils import Matrix,Vector
from build_robot_blender import empty,linear_keys


def influence(constraint,rig,expression,properties):
    try:constraint.driver_remove('influence')
    except TypeError:pass
    fc=constraint.driver_add('influence');driver=fc.driver
    for key,prop in properties.items():
        v=driver.variables.new();v.name=key;v.targets[0].id=rig;v.targets[0].data_path='["'+prop+'"]'
    driver.expression=expression


def periodic_curves(obj,period=120):
    """Periodic cubic handles including matching derivatives at the closing key."""
    if not obj.animation_data or not obj.animation_data.action:return
    for layer in obj.animation_data.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    keys=list(curve.keyframe_points)
                    if len(keys)<3:continue
                    times=np.array([k.co.x for k in keys]);values=np.array([k.co.y for k in keys])
                    if abs(times[-1]-times[0]-period)>1e-4:continue
                    if curve.data_path.endswith('pole_angle'):values=np.unwrap(values)
                    if abs(values[-1]-values[0])>1e-3:raise RuntimeError('Nonclosing animation channel: '+curve.data_path+' '+str(values[[0,-1]]))
                    values[-1]=values[0]
                    for i,k in enumerate(keys):
                        im=len(keys)-2 if i in (0,len(keys)-1) else i-1
                        ip=1 if i in (0,len(keys)-1) else i+1
                        tm=times[im]-(period if i==0 else 0);tp=times[ip]+(period if i==len(keys)-1 else 0)
                        slope=(values[ip]-values[im])/(tp-tm)
                        hleft=(times[i]-tm)/3;hright=(tp-times[i])/3
                        k.co.y=values[i];k.interpolation='BEZIER';k.handle_left_type='FREE';k.handle_right_type='FREE'
                        k.handle_left=(times[i]-hleft,values[i]-slope*hleft);k.handle_right=(times[i]+hright,values[i]+slope*hright)
                    if not any(m.type=='CYCLES' for m in curve.modifiers):curve.modifiers.new('CYCLES')
                    curve.update()


def install(rig,d,xyz,collection,prefix='PILGRIM_SETTLE',contacts=None,anchors=None,preserve_distal=False,anchor_paths=None,cyclic=True):
    scene=bpy.context.scene;names=d['names'];ix={n:i for i,n in enumerate(names)};frames=len(xyz)
    matrices=[]
    for f in range(frames):
        scene.frame_set(f+1);bpy.context.view_layer.update();matrices.append({n:(rig.matrix_world@rig.pose.bones[n].matrix).copy() for n in names})
    def prop(name,value,description):
        rig[name]=value;rig.id_properties_ui(name).update(min=0,max=1,description=description)
    prop('use_controls',1.,'1 editable controls; 0 baked FK only')
    prop('head_world_lock',0.,'Keep head orientation at the initial world orientation')
    prop('head_look_at',0.,'Blend toward CTRL_LOOK_TARGET; 0 preserves generated head motion')
    objects={}
    def control(suffix,kind='CUBE',size=.12):
        o=empty(prefix+'_'+suffix,collection,kind,size);o.rotation_mode='QUATERNION';objects[suffix]=o;return o
    root=control('CTRL_ROOT','PLAIN_AXES',.35);chest=control('CTRL_CHEST','CIRCLE',.25);head=control('CTRL_HEAD','CIRCLE',.16)
    chest.parent=root;head.parent=chest;chest.lock_location=(True,)*3;head.lock_location=(True,)*3
    for o in [root,chest,head]:o.lock_scale=(True,)*3
    for f,m in enumerate(matrices):
        root.matrix_basis=m['ROOT'];chest.matrix_basis=m['ROOT'].inverted()@m['SPINE_02'];head.matrix_basis=m['SPINE_02'].inverted()@m['HEAD']
        for o in [root,chest,head]:
            o.keyframe_insert('location',frame=f+1);o.keyframe_insert('rotation_quaternion',frame=f+1)
    for bone,obj,kind in [('ROOT',root,'COPY_TRANSFORMS'),('SPINE_02',chest,'COPY_ROTATION'),('HEAD',head,'COPY_ROTATION')]:
        c=rig.pose.bones[bone].constraints.new(kind);c.name='Editable '+bone;c.target=obj;c.owner_space='WORLD';c.target_space='WORLD';influence(c,rig,'u',dict(u='use_controls'))
    lock=control('HEAD_WORLD_ORIENTATION','PLAIN_AXES',.13);lock.matrix_world=matrices[0]['HEAD']
    c=rig.pose.bones['HEAD'].constraints.new('COPY_ROTATION');c.name='World orientation lock';c.target=lock;c.owner_space='WORLD';c.target_space='WORLD';influence(c,rig,'u*w',dict(u='use_controls',w='head_world_lock'))
    look=control('CTRL_LOOK_TARGET','SPHERE',.16);look.location=matrices[0]['HEAD'].translation+Vector((0,-4,0))
    aim=control('HEAD_AIM_FRAME','PLAIN_AXES',.1);aim.parent=head;aim.matrix_basis=Matrix.Identity(4)
    c=aim.constraints.new('TRACK_TO');c.target=look;c.track_axis='TRACK_NEGATIVE_Z';c.up_axis='UP_Y'
    scene.frame_set(1);bpy.context.view_layer.update();orient=control('HEAD_LOOK_ORIENTATION','PLAIN_AXES',.08);orient.parent=aim
    orient.matrix_basis=aim.matrix_world.inverted()@matrices[0]['HEAD'];orient.location=(0,0,0)
    c=rig.pose.bones['HEAD'].constraints.new('COPY_ROTATION');c.name='Look at target';c.target=orient;c.owner_space='WORLD';c.target_space='WORLD';influence(c,rig,'u*w',dict(u='use_controls',w='head_look_at'))
    for li,key in enumerate('ABCD'):
        prop('contact_'+key,1. if key in 'CD' else 0.,'World-anchor blend for '+key+'; 0 free control, 1 planted anchor')
        palm=control('CTRL_PALM_'+key,'CUBE',.14);palm.parent=root;palm.lock_scale=(True,)*3
        anchor=control('CONTACT_ANCHOR_'+key,'CIRCLE',.18);anchor.location=xyz[0,ix[key+'_3']]
        if anchors is not None:anchor.location=anchors[li]
        if anchor_paths is not None:
            for f in range(frames):
                anchor.location=anchor_paths[f,li];anchor.keyframe_insert('location',frame=f+1)
        if contacts is not None:
            for f,w in enumerate(contacts[:,li]):
                rig['contact_'+key]=float(w);rig.keyframe_insert('["contact_'+key+'"]',frame=f+1)
        solved=control('SOLVED_PALM_'+key,'PLAIN_AXES',.06)
        c=solved.constraints.new('COPY_TRANSFORMS');c.target=palm;c.owner_space='WORLD';c.target_space='WORLD'
        c=solved.constraints.new('COPY_TRANSFORMS');c.target=anchor;c.owner_space='WORLD';c.target_space='WORLD';influence(c,rig,'w',dict(w='contact_'+key))
        distal=control('CTRL_DISTAL_'+key,'ARROWS',.14);distal.parent=solved;distal.rotation_quaternion=rig.data.bones[key+'_2'].matrix_local.to_quaternion();distal.lock_location=(True,)*3;distal.lock_scale=(True,)*3
        # Existing targets belong to build()'s prefix, which is stored in the rig name.
        wrist=bpy.data.objects[rig.name[:-4]+'_IK_'+key];wrist.animation_data_clear();wrist.parent=distal;wrist.matrix_parent_inverse=Matrix.Identity(4);wrist.location=(0,-rig.data.bones[key+'_2'].length,0);wrist.rotation_euler=(0,0,0)
        orient_pad=control('PALM_ORIENTATION_'+key,'PLAIN_AXES',.05);orient_pad.parent=solved;orient_pad.rotation_quaternion=rig.data.bones[key+'_3'].matrix_local.to_quaternion()
        last_distal=None
        for f,m in enumerate(matrices):
            tip=np.array(xyz[f,ix[key+'_3']]).copy()
            if contacts is not None and anchor_paths is not None and contacts[f,li]<1-1e-8:
                # Numerical clean positions already include the contact blend.
                w=float(contacts[f,li]);tip=(tip-w*anchor_paths[f,li])/(1-w)
            world=Matrix.Translation(Vector(tip));palm.matrix_basis=m['ROOT'].inverted()@world
            palm.keyframe_insert('location',frame=f+1);palm.keyframe_insert('rotation_quaternion',frame=f+1)
            if preserve_distal:
                q=m[key+'_2'].to_quaternion()
                if last_distal is not None and q.dot(last_distal)<0:q.negate()
                distal.rotation_quaternion=q;last_distal=q.copy()
                distal.keyframe_insert('rotation_quaternion',frame=f+1)
        for bone,obj in [(key+'_2',distal),(key+'_3',orient_pad)]:
            c=rig.pose.bones[bone].constraints.new('COPY_ROTATION');c.name='Distal and palm orientation';c.target=obj;c.owner_space='WORLD';c.target_space='WORLD';influence(c,rig,'u*w',dict(u='use_controls',w='ik_'+key))
        ik=rig.pose.bones[key+'_1'].constraints['Prototype wrist IK'];ik.name='Three-segment contact IK';influence(ik,rig,'u*w',dict(u='use_controls',w='ik_'+key));rig['ik_'+key]=1.
    for o in list(objects.values())+[rig]:
        if cyclic:periodic_curves(o,frames-1)
        else:linear_keys(o)
    # Existing poles remain world-space and are independently editable.
    for key in 'ABCD':
        if cyclic:periodic_curves(bpy.data.objects[rig.name[:-4]+'_POLE_'+key],frames-1)
    rig.update_tag();scene.frame_set(1);bpy.context.view_layer.update()
    rig['control_prefix']=prefix;rig['rig_stage']='Editable root/chest/head, look target and world lock; independent palm/distal controls, wrist IK, world contact anchors. Baked FK action supplied separately.'
    return objects


def snap_ik_to_fk(rig,key):
    """Match a limb's evaluated FK pose with free IK controls at the current frame."""
    p=rig['control_prefix'];scene=bpy.context.scene;rig['ik_'+key]=0.;rig.update_tag();bpy.context.view_layer.update()
    m={i:(rig.matrix_world@rig.pose.bones[key+'_'+str(i)].matrix).copy() for i in range(4)}
    rig['contact_'+key]=0.;palm=bpy.data.objects[p+'_CTRL_PALM_'+key]
    q=m[3].to_quaternion()@rig.data.bones[key+'_3'].matrix_local.to_quaternion().inverted();world=q.to_matrix().to_4x4();world.translation=m[3].translation;palm.matrix_world=world
    bpy.context.view_layer.update();solved=bpy.data.objects[p+'_SOLVED_PALM_'+key];distal=bpy.data.objects[p+'_CTRL_DISTAL_'+key]
    distal.rotation_quaternion=solved.matrix_world.to_quaternion().inverted()@m[2].to_quaternion()
    a,b,c=(m[i].translation for i in range(3));axis=(c-a).normalized();v=b-a;rad=(v-axis*v.dot(axis)).normalized()
    bpy.data.objects[rig.name[:-4]+'_POLE_'+key].location=a+rad*.85
    rig['ik_'+key]=1.;rig.update_tag();bpy.context.view_layer.update()
    # Compensate pole-roll changes using the same differential calibration as build().
    ik=rig.pose.bones[key+'_1'].constraints['Three-segment contact IK']
    def radial(point):
        v=point-a;return (v-axis*v.dot(axis)).normalized()
    def angle(x,y):return math.atan2(axis.dot(x.cross(y)),x.dot(y))
    for _ in range(8):
        current=radial(rig.matrix_world@rig.pose.bones[key+'_1'].head);err=angle(current,rad)
        if abs(err)<1e-6:break
        old=ik.pole_angle;step=-.01 if old>3.1 else .01;ik.pole_angle=old+step;bpy.context.view_layer.update()
        deriv=angle(current,radial(rig.matrix_world@rig.pose.bones[key+'_1'].head))/step
        if abs(deriv)<.1:raise RuntimeError('Cannot match a degenerate straight limb')
        ik.pole_angle=math.atan2(math.sin(old+err/deriv),math.cos(old+err/deriv));bpy.context.view_layer.update()


def snap_fk_to_ik(rig,key):
    """Match FK to the currently evaluated IK limb; no keyframes are changed."""
    bpy.context.view_layer.update();e=rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
    matrices={key+'_'+str(i):e.pose.bones[key+'_'+str(i)].matrix.copy() for i in range(4)}
    rig['ik_'+key]=0.;rig.update_tag();bpy.context.view_layer.update()
    for name,matrix in matrices.items():rig.pose.bones[name].matrix=matrix;bpy.context.view_layer.update()


def set_contact(rig,key,planted,keyframe=False):
    """Plant or release at the current solved pose without jumping to an old target."""
    p=rig['control_prefix'];bpy.context.view_layer.update();solved=bpy.data.objects[p+'_SOLVED_PALM_'+key];world=solved.matrix_world.copy()
    target=bpy.data.objects[p+('_CONTACT_ANCHOR_' if planted else '_CTRL_PALM_')+key];target.matrix_world=world
    rig['contact_'+key]=float(planted);rig.update_tag();bpy.context.view_layer.update()
    if keyframe:
        frame=bpy.context.scene.frame_current+float(bpy.context.scene.frame_subframe)
        target.keyframe_insert('location',frame=frame);target.keyframe_insert('rotation_quaternion',frame=frame);rig.keyframe_insert('["contact_'+key+'"]',frame=frame)


def bake_fk(rig,name,step=.25,cyclic=True):
    """Bake evaluated control output, retaining the separate editable Action."""
    scene=bpy.context.scene;original=rig.animation_data.action;names=[b.name for b in rig.data.bones];frames=np.arange(scene.frame_start,scene.frame_end+int(cyclic)+step/2,step);captured=[]
    for frame in frames:
        scene.frame_set(int(frame),subframe=float(frame%1));e=rig.evaluated_get(bpy.context.evaluated_depsgraph_get());captured.append([e.pose.bones[n].matrix.copy() for n in names])
    action=bpy.data.actions.new(name);action.use_fake_user=True;rig.animation_data.action=action;rig['use_controls']=0.;rig.update_tag();prev={}
    for frame,matrices in zip(frames,captured):
        scene.frame_set(int(frame),subframe=float(frame%1))
        for n,m in zip(names,matrices):
            pb=rig.pose.bones[n];pb.matrix=m;bpy.context.view_layer.update()
            if n in prev and pb.rotation_quaternion.dot(prev[n])<0:pb.rotation_quaternion.negate()
            prev[n]=pb.rotation_quaternion.copy();pb.keyframe_insert('location',frame=float(frame));pb.keyframe_insert('rotation_quaternion',frame=float(frame))
    if cyclic:periodic_curves(rig,scene.frame_end-scene.frame_start+1)
    else:linear_keys(rig)
    rig.animation_data.action=original;rig['use_controls']=1.;rig.update_tag();scene.frame_set(scene.frame_start)
    return action
