"""Motion Lab: local Blender prompt interface, asynchronous GPU jobs and raw playback."""
bl_info={'name':'UniMate Motion Lab','author':'aniMove','version':(1,0,0),'blender':(5,0,0),'category':'Animation'}
import bpy,json,math,os,signal,subprocess,time,uuid
from pathlib import Path
import numpy as np
from mathutils import Matrix,Vector,Quaternion
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001')
REPO=Path('/home/ipsedesktop/Documents/GitHub/aniMove')
SCENE='UNIMATE_Motion_Lab'
TARGETS={t['id']:t for t in json.loads((BASE/'targets.json').read_text())}
_TARGET_ITEMS=[(k,t['title']+' · '+str(t['joints'])+' joints',t['source']) for k,t in TARGETS.items()]
_HISTORY_ITEMS=[]
JOB=None
_LOG=None
_LAST_TARGET='Mammal'
COLORS={'body':(.40,.55,.60,1),'head':(.62,.76,.79,1),'tail':(.38,.48,.54,1),'left_front':(.15,.7,.77,1),'right_front':(.94,.45,.24,1),'left_hind':(.4,.7,.32,1),'right_hind':(.65,.39,.84,1),'left_middle':(.32,.6,.85,1),'right_middle':(.85,.64,.22,1),'left_wing':(.15,.7,.77,1),'right_wing':(.94,.45,.24,1),'left_leg':(.4,.7,.32,1),'right_leg':(.65,.39,.84,1),'A':(.15,.7,.77,1),'B':(.94,.45,.24,1),'C':(.4,.7,.32,1),'D':(.65,.39,.84,1)}

def convert(v):return Vector((float(v[0]),float(-v[2]),float(v[1])))
def mat(group):
    name='ML_'+group;m=bpy.data.materials.get(name)
    if m is None:m=bpy.data.materials.new(name);m.diffuse_color=COLORS.get(group,COLORS['body'])
    return m

def move_object(obj,collection):
    for c in list(obj.users_collection):c.objects.unlink(obj)
    collection.objects.link(obj)

def bind(obj,rig,bone):
    obj.vertex_groups.new(name=bone).add(list(range(len(obj.data.vertices))),1,'REPLACE');mod=obj.modifiers.new('Rigid joint attachment','ARMATURE');mod.object=rig;obj.parent=rig

def build_target(scene,target):
    key=target['id'];collection=bpy.data.collections.new('ML_TARGET_'+key);scene.collection.children.link(collection);arm=bpy.data.armatures.new('ML_'+key);rig=bpy.data.objects.new('ML_RIG_'+key,arm);collection.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT');rest=np.asarray(target['rest']);parents=target['parents'];names=target['names']
    for j,n in enumerate(names):
        b=arm.edit_bones.new(n);b.head=convert(rest[j]);kids=[i for i,p in enumerate(parents) if p==j];d=convert(rest[kids[0]]-rest[j]) if kids else convert(rest[j]-rest[parents[j]]).normalized()*.065;b.tail=b.head+d
        if parents[j]>=0:b.parent=arm.edit_bones[names[parents[j]]]
    bpy.ops.object.mode_set(mode='OBJECT');rig.animation_data_create();rig.hide_render=True
    for pb in rig.pose.bones:pb.rotation_mode='QUATERNION'
    for j,p in enumerate(parents):
        if p<0:continue
        a,b=convert(rest[p]),convert(rest[j]);length=(b-a).length;group=target['groups'][j];radius=.045 if group=='body' else .025
        if key=='Insect':radius=.023 if group=='body' else .014
        if key=='Bird' and ('Feather' in names[j] or 'Toe' in names[j]):radius=.012
        if 'Toe' in names[j] or 'Tail' in names[j]:radius*=.7
        bpy.ops.mesh.primitive_cone_add(vertices=10,radius1=radius*1.12,radius2=radius*.72,depth=length,location=(a+b)/2);obj=bpy.context.object;obj.name='ML_LINK_'+key+'_'+names[j];move_object(obj,collection);obj.rotation_mode='QUATERNION';obj.rotation_quaternion=(b-a).to_track_quat('Z','Y');obj.data.materials.append(mat(group));bpy.ops.object.transform_apply(location=False,rotation=True,scale=True);bind(obj,rig,names[p]);obj['joint_parent']=p;obj['joint_child']=j
    # Rigid, readable body volumes. They do not enter model conditioning.
    body_specs=[]
    if key=='Mammal':body_specs=[('Chest',(.29,.36,.26)),('Hips',(.28,.28,.26)),('Head',(.20,.25,.20)),('Muzzle',(.13,.20,.10))]
    elif key=='Bird':body_specs=[('Chest',(.23,.33,.28)),('Hips',(.21,.23,.20)),('Head',(.14,.16,.16))]
    elif key=='Insect':body_specs=[('Thorax',(.20,.29,.17)),('Abdomen',(.25,.39,.20)),('Head',(.16,.18,.14))]
    for name,size in body_specs:
        j=names.index(name);bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=1,location=convert(rest[j]));obj=bpy.context.object;obj.name='ML_BODY_'+key+'_'+name;move_object(obj,collection);obj.scale=size;obj.data.materials.append(mat('head' if name in ['Head','Muzzle'] else 'body'));bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);bind(obj,rig,name)
        for poly in obj.data.polygons:poly.use_smooth=True
    if key=='Bird':
        for side in ['Left','Right']:
            ns=[side+' Wing Shoulder',side+' Wing Elbow',side+' Wing Wrist',side+' Wing Hand',side+' Wing Tip',side+' Primary Feather',side+' Secondary Feather',side+' Inner Feather'];ids=[names.index(n) for n in ns];mesh=bpy.data.meshes.new('WingSurface');mesh.from_pydata([convert(rest[j]) for j in ids],[],[(0,1,7),(1,2,6,7),(2,3,5,6),(3,4,5)]);mesh.update();obj=bpy.data.objects.new('ML_WING_'+side,mesh);collection.objects.link(obj);mesh.materials.append(mat(side.lower()+'_wing'));obj.parent=rig
            for i,j in enumerate(ids):
                n=names[parents[j]];g=obj.vertex_groups.get(n) or obj.vertex_groups.new(name=n);g.add([i],1,'REPLACE')
            mod=obj.modifiers.new('Wing skeleton','ARMATURE');mod.object=rig
    rig.select_set(False);return rig

def ensure_scene():
    if SCENE in bpy.data.scenes:return bpy.data.scenes[SCENE]
    old=bpy.context.window.scene if bpy.context.window else None
    s=bpy.data.scenes.new(SCENE)
    if bpy.context.window:bpy.context.window.scene=s
    s.render.fps=30;s.frame_start=1;s.frame_end=60;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=1500;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=True;s.world=bpy.data.worlds.new('ML_World');s.world.color=(.045,.055,.07);s.display.shading.background_type='WORLD'
    for target in TARGETS.values():build_target(s,target)
    ground=bpy.data.collections.new('ML_STAGE');s.collection.children.link(ground)
    for axis in range(2):
        for i in range(-15,16):
            bpy.ops.mesh.primitive_cube_add(size=1,location=(i if axis==0 else 0,0 if axis==0 else i,-.013));o=bpy.context.object;o.name='ML_Grid';o.dimensions=(.006,30,.004) if axis==0 else (30,.006,.004);move_object(o,ground);o.data.materials.append(mat('tail'))
    cam=bpy.data.objects.new('ML_Camera',bpy.data.cameras.new('ML_Camera'));ground.objects.link(cam);cam.data.type='ORTHO';s.camera=cam;s['lab_version']=1;s['status']='Ready';s['active_result']='';s['active_target']='Mammal'
    # Retain the interface source in standalone saves; no external Python environment needed for playback.
    text=bpy.data.texts.get('MOTION_LAB_UI.py') or bpy.data.texts.new('MOTION_LAB_UI.py');text.clear();text.write((REPO/'motion_lab/blender_ui.py').read_text())
    if old and bpy.context.window:bpy.context.window.scene=old
    return s

def frame_view(scene,points):
    points=np.asarray(points).reshape(-1,3);lo=points.min(0);hi=points.max(0);lo[1]=min(lo[1],0);center=convert((lo+hi)/2);cam=scene.camera;cam.location=center+Vector((4,-6,3));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();inverse=cam.rotation_euler.to_quaternion().inverted();corners=[inverse@(convert((x,y,z))-center) for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]];aspect=scene.render.resolution_x/scene.render.resolution_y;cam.data.ortho_scale=max(max(p.x for p in corners)-min(p.x for p in corners),(max(p.y for p in corners)-min(p.y for p in corners))*aspect,2)*1.25

@bpy.app.handlers.persistent
def follow_frame(scene,*_):
    if scene.name!=SCENE or not getattr(scene,'ml_follow',False) or not scene.get('active_result') or 'follow_camera_origin' not in scene:return
    rig=scene.objects.get('ML_RIG_'+scene.get('active_target',''))
    if rig is None:return
    root=rig.pose.bones[TARGETS[scene['active_target']]['names'][0]].head
    delta=root-Vector(scene['follow_root_origin']);delta.z=0
    scene.camera.location=Vector(scene['follow_camera_origin'])+delta

def reframe_motion(scene,x):
    points=x.copy()
    if scene.ml_follow:
        points[:,:,0]-=x[:,0:1,0]-x[0,0,0];points[:,:,2]-=x[:,0:1,2]-x[0,0,2]
    frame_view(scene,points);scene['follow_camera_origin']=list(scene.camera.location);scene['follow_root_origin']=list(convert(x[0,0]));follow_frame(scene)

def follow_changed(self,context):
    job=self.get('active_result','')
    if job and self.name==SCENE:
        with np.load(BASE/'jobs'/job/'kinematics.npz') as data:reframe_motion(self,data['positions'])

def show_target(scene,key,rest=False):
    global _LAST_TARGET
    for k in TARGETS:
        c=bpy.data.collections['ML_TARGET_'+k];c.hide_viewport=k!=key;c.hide_render=k!=key
    scene['active_target']=key;rig=scene.objects['ML_RIG_'+key]
    if rest:
        if bpy.context.screen and bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
        rig.animation_data.action=None
        for pb in rig.pose.bones:pb.location=(0,0,0);pb.rotation_quaternion=(1,0,0,0);pb.scale=(1,1,1)
        scene.frame_set(1);frame_view(scene,TARGETS[key]['rest']);scene['active_result']='';scene['status']='Reference pose — enter a prompt and generate'
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active;space.region_3d.view_perspective='CAMERA';space.shading.color_type='MATERIAL';space.overlay.show_overlays=False;space.show_region_ui=True
    _LAST_TARGET=key

def target_changed(self,context):
    if self.name!=SCENE or 'ML_TARGET_'+self.ml_target not in bpy.data.collections:return
    old_default=TARGETS.get(_LAST_TARGET,{}).get('default_prompt')
    if not self.ml_prompt or self.ml_prompt==old_default:self.ml_prompt=TARGETS[self.ml_target]['default_prompt']
    show_target(self,self.ml_target,rest=True)

def history_items(self,context):return _HISTORY_ITEMS or [('NONE','No generations yet','')]
def refresh_history():
    global _HISTORY_ITEMS
    results=[]
    for f in (BASE/'jobs').glob('*/result.json'):
        try:
            r=json.loads(f.read_text());results.append((r['created'],r))
        except (OSError,ValueError,KeyError):continue
    results.sort(key=lambda v:v[0],reverse=True);_HISTORY_ITEMS=[(r['id'],f"{r['target']} · {r['seconds']:g}s · {r['request']['prompt'][:55]}",f"Seed {r['request']['seed']} · {r['id']}") for _,r in results]

def load_result(job_id,autoplay=True):
    if not job_id or job_id=='NONE':return
    job=BASE/'jobs'/job_id
    if job.parent!=BASE/'jobs':raise ValueError('Invalid generation ID')
    result=json.loads((job/'result.json').read_text());key=result['request']['target'];s=bpy.data.scenes[SCENE]
    if bpy.context.window:bpy.context.window.scene=s
    if bpy.context.screen and bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
    s.ml_target=key;show_target(s,key);t=TARGETS[key];rig=s.objects['ML_RIG_'+key];data=np.load(job/'kinematics.npz');x=data['positions'];q=data['global_quaternions_wxyz'];names=t['names'];parents=t['parents'];action=bpy.data.actions.get('ML_'+job_id)
    if action is None:
        action=bpy.data.actions.new('ML_'+job_id);action.use_fake_user=True;rig.animation_data.action=action;rests=[rig.data.bones[n].matrix_local.copy() for n in names];qb=Matrix.Rotation(math.pi/2,4,'X').to_quaternion();previous=[None]*len(names)
        for f in range(len(x)):
            desired=[Matrix.LocRotScale(convert(x[f,j]),qb@Quaternion(tuple(q[f,j]))@qb.inverted()@rests[j].to_quaternion(),Vector((1,1,1))) for j in range(len(names))]
            for j,n in enumerate(names):
                local=rests[j].inverted()@desired[j] if parents[j]<0 else rests[j].inverted()@rests[parents[j]]@desired[parents[j]].inverted()@desired[j];loc,rot,_=local.decompose()
                if previous[j] is not None and rot.dot(previous[j])<0:rot.negate()
                previous[j]=rot.copy();pb=rig.pose.bones[n];pb.location=loc;pb.rotation_quaternion=rot;pb.scale=(1,1,1);pb.keyframe_insert('location',frame=f+1,group=n);pb.keyframe_insert('rotation_quaternion',frame=f+1,group=n)
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        for point in fc.keyframe_points:point.interpolation='LINEAR'
        for k in ['target','seconds','frames','duration_mode','feature_sha256','postprocessing']:action[k]=result[k]
        action['result_path']=str(job/'result.json');action['prompt']=result['request']['prompt'];action['seed']=result['request']['seed']
    rig.animation_data.action=action
    if action.slots:rig.animation_data.action_slot=action.slots[0]
    # Check the actual baked rig at representative frames before exposing completion.
    error=0
    for f in sorted(set([0,len(x)//2,len(x)-1])):
        s.frame_set(f+1);bpy.context.view_layer.update();error=max(error,max((rig.pose.bones[n].head-convert(x[f,j])).length for j,n in enumerate(names)))
    if error>2e-4:raise RuntimeError(f'Blender bake mismatch: {error:g} m')
    (job/'blender_validation.json').write_text(json.dumps(dict(status='passed',max_joint_error_m=error,frames_checked=[1,len(x)//2+1,len(x)]),indent=2))
    s.frame_start=1;s.frame_end=len(x);s.frame_set(1);s['active_result']=job_id;reframe_motion(s,x);s['status']=f"Ready · {result['seconds']:g}s · seed {result['request']['seed']}";s.ml_prompt=result['request']['prompt'];s.ml_seed=result['request']['seed'];s.ml_seconds=result['seconds'];s.timeline_markers.clear()
    for frame in result['seams_zero_based']:s.timeline_markers.new('Generated continuation',frame=frame+1)
    if autoplay and bpy.context.screen and not bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_play()

def poll_job():
    global JOB,_LOG
    if JOB is None:return None
    s=bpy.data.scenes.get(SCENE)
    if s is None:return None
    process,job,started=JOB
    try:
        p=job/'status.json';state=json.loads(p.read_text()) if p.exists() else {'status':'starting'};elapsed=int(time.time()-started);s['status']=state['status'].capitalize()+f' · {elapsed}s elapsed'
        if process.poll() is None:
            for screen in bpy.data.screens:
                for area in screen.areas:area.tag_redraw()
            return .5
        if _LOG:_LOG.close();_LOG=None
        JOB=None
        if state['status']=='complete':refresh_history();s.ml_history=job.name;load_result(job.name,s.ml_autoplay)
        else:s['status']='Failed: '+state.get('error','See job log');s['last_error_log']=str(job/'error.log')
    except Exception as exc:
        s['status']='Could not load result: '+str(exc);JOB=None
    for screen in bpy.data.screens:
        for area in screen.areas:area.tag_redraw()
    return None

def start_job(scene):
    global JOB,_LOG
    if JOB is not None:raise RuntimeError('A generation is already running')
    prompt=scene.ml_prompt.strip()
    if not prompt:raise ValueError('Enter a motion prompt')
    job=BASE/'jobs'/(time.strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8]);job.mkdir(parents=True);request=dict(target=scene.ml_target,prompt=prompt,seed=scene.ml_seed,seconds=scene.ml_seconds);(job/'request.json').write_text(json.dumps(request,indent=2));_LOG=(job/'worker.log').open('w');process=subprocess.Popen([str(REPO/'.venv-unimate/bin/python'),str(REPO/'motion_lab/worker.py'),str(job/'request.json')],cwd=REPO,stdout=_LOG,stderr=subprocess.STDOUT,start_new_session=True);JOB=(process,job,time.time());scene['status']='Starting generation';bpy.app.timers.register(poll_job,first_interval=.5);return job

class ML_OT_open(bpy.types.Operator):
    bl_idname='motion_lab.open';bl_label='Open Motion Lab'
    def execute(self,context):
        s=ensure_scene();context.window.scene=s;s.sync_mode='FRAME_DROP';show_target(s,s.ml_target,rest=not bool(s.get('active_result','')));return {'FINISHED'}
class ML_OT_generate(bpy.types.Operator):
    bl_idname='motion_lab.generate';bl_label='Generate motion';bl_description='Generate new motion on the selected rig using the local GPU'
    new_seed:bpy.props.BoolProperty(default=False)
    def execute(self,context):
        try:
            if self.new_seed:context.scene.ml_seed=int.from_bytes(os.urandom(4),'little')%2147483647
            start_job(context.scene);return {'FINISHED'}
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}
class ML_OT_cancel(bpy.types.Operator):
    bl_idname='motion_lab.cancel';bl_label='Cancel generation'
    def execute(self,context):
        global JOB,_LOG
        if JOB:
            process,job,_=JOB
            try:os.killpg(process.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            (job/'status.json').write_text(json.dumps(dict(status='cancelled')));JOB=None
            if _LOG:_LOG.close();_LOG=None
        context.scene['status']='Cancelled';return {'FINISHED'}
class ML_OT_load(bpy.types.Operator):
    bl_idname='motion_lab.load';bl_label='Play selected result'
    def execute(self,context):
        try:load_result(context.scene.ml_history,context.scene.ml_autoplay);return {'FINISHED'}
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}
class ML_OT_rest(bpy.types.Operator):
    bl_idname='motion_lab.rest';bl_label='Show reference pose'
    def execute(self,context):show_target(context.scene,context.scene.ml_target,rest=True);return {'FINISHED'}
class ML_OT_refresh(bpy.types.Operator):
    bl_idname='motion_lab.refresh';bl_label='Refresh results'
    def execute(self,context):refresh_history();return {'FINISHED'}
class ML_OT_save(bpy.types.Operator):
    bl_idname='motion_lab.save';bl_label='Save current animation .blend'
    def execute(self,context):
        s=context.scene;job_id=s.get('active_result','')
        if not job_id:self.report({'ERROR'},'Load a generated animation first');return {'CANCELLED'}
        target=BASE/'jobs'/job_id/'animation.blend';bpy.data.libraries.write(str(target),{s,bpy.data.texts['MOTION_LAB_UI.py']});self.report({'INFO'},'Saved '+str(target));s['status']='Saved animation.blend in this result folder';return {'FINISHED'}
class ML_PT_panel(bpy.types.Panel):
    bl_label='UniMate Motion Lab';bl_idname='ML_PT_panel';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='Motion Lab'
    def draw(self,context):
        import textwrap
        s=context.scene;l=self.layout
        if s.name!=SCENE:
            l.operator('motion_lab.open',icon='ARMATURE_DATA');return
        l.prop(s,'ml_target',text='Target');l.operator('motion_lab.rest',icon='ARMATURE_DATA');l.separator();l.prop(s,'ml_prompt',text='Prompt');row=l.row(align=True);row.prop(s,'ml_seconds',text='Seconds');row.prop(s,'ml_seed',text='Seed')
        if s.ml_seconds>2:l.label(text='Longer clip: overlapping continuations',icon='INFO')
        row=l.row(align=True);row.enabled=JOB is None;row.operator('motion_lab.generate',text='Generate',icon='PLAY');row.operator('motion_lab.generate',text='New variation',icon='FILE_REFRESH').new_seed=True
        if JOB:l.operator('motion_lab.cancel',icon='CANCEL')
        for line in textwrap.wrap(s.get('status','Ready'),40):l.label(text=line)
        l.prop(s,'ml_autoplay',text='Play when ready');l.prop(s,'ml_follow',text='Camera follows motion');l.separator();l.label(text='Previous generations');row=l.row(align=True);row.prop(s,'ml_history',text='');row.operator('motion_lab.refresh',text='',icon='FILE_REFRESH');l.operator('motion_lab.load',icon='PLAY');l.operator('motion_lab.save',icon='FILE_BLEND');l.separator();l.label(text='Raw motion · no IK or contact cleanup');l.label(text='Timeline repeat is a hard reset')
CLASSES=[ML_OT_open,ML_OT_generate,ML_OT_cancel,ML_OT_load,ML_OT_rest,ML_OT_refresh,ML_OT_save,ML_PT_panel]
def register():
    for cls in CLASSES:
        old=getattr(bpy.types,cls.__name__,None)
        if old:bpy.utils.unregister_class(old)
        bpy.utils.register_class(cls)
    bpy.types.Scene.ml_target=bpy.props.EnumProperty(items=_TARGET_ITEMS,default='Mammal',update=target_changed)
    bpy.types.Scene.ml_prompt=bpy.props.StringProperty(name='Motion prompt',default='A dog walks forward.',maxlen=1500)
    bpy.types.Scene.ml_seconds=bpy.props.FloatProperty(default=2,min=2,max=12,precision=1,step=100)
    bpy.types.Scene.ml_seed=bpy.props.IntProperty(default=9800,min=0,max=2147483647)
    bpy.types.Scene.ml_autoplay=bpy.props.BoolProperty(default=True)
    bpy.types.Scene.ml_follow=bpy.props.BoolProperty(default=True,update=follow_changed)
    for handler in list(bpy.app.handlers.frame_change_post):
        if getattr(handler,'__module__','').startswith(('animove_motion_lab','motion_lab_review')) and getattr(handler,'__name__','')=='follow_frame':bpy.app.handlers.frame_change_post.remove(handler)
    bpy.app.handlers.frame_change_post.append(follow_frame)
    bpy.types.Scene.ml_history=bpy.props.EnumProperty(items=history_items)
    refresh_history()
    bpy.app.driver_namespace['motion_lab_ui']=globals()
def unregister():
    if follow_frame in bpy.app.handlers.frame_change_post:bpy.app.handlers.frame_change_post.remove(follow_frame)
    for cls in reversed(CLASSES):
        old=getattr(bpy.types,cls.__name__,None)
        if old:bpy.utils.unregister_class(old)
    for name in ['ml_target','ml_prompt','ml_seconds','ml_seed','ml_autoplay','ml_follow','ml_history']:
        if hasattr(bpy.types.Scene,name):delattr(bpy.types.Scene,name)
if __name__=='__main__':register()
