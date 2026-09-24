"""Blender comparison selector with explicit input-reference mode."""
import bpy,json,itertools,textwrap
from mathutils import Vector
SCENE='PILGRIM_UniMate_STANCE';_ITEMS=[]
def select_case(identifier):
    s=bpy.data.scenes[SCENE];cases=json.loads(s['cases']);rigs=json.loads(s['rigs']);points=[]
    for variant,name in rigs.items():
        rig=s.objects[name]
        action=bpy.data.actions['STN_REFERENCE_'+variant] if identifier=='REFERENCE' else bpy.data.actions['UNI_stance_'+variant+'_'+cases[identifier]['prompt_id']+'_s'+str(cases[identifier]['seed'])]
        rig.animation_data.action=action
        if action.slots:rig.animation_data.action_slot=action.slots[0]
        for x,y,z in itertools.product(*zip(action['bounds_min'],action['bounds_max'])):points.append(Vector((x,-z,y))+rig.location)
    low=Vector(tuple(min(p[i] for p in points) for i in range(3)));high=Vector(tuple(max(p[i] for p in points) for i in range(3)));low.z=min(low.z,-.2);high.z+=.7;center=(low+high)/2;cam=s.camera;cam.location=center+Vector((7,-20,8));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();inverse=cam.rotation_euler.to_quaternion().inverted();corners=[inverse@(Vector(v)-center) for v in itertools.product(*zip(low,high))];aspect=s.render.resolution_x/s.render.resolution_y;cam.data.ortho_scale=max(max(p.x for p in corners)-min(p.x for p in corners),(max(p.y for p in corners)-min(p.y for p in corners))*aspect)*1.10
    for variant,name in rigs.items():
        title=s.objects['STANCE_TITLE_'+variant];title.location=(s.objects[name].location.x,center.y,high.z-.3);title.rotation_euler=cam.rotation_euler
    s['active_case']=identifier;s['active_prompt']='AUTHORED INPUT REFERENCES — not animation frames' if identifier=='REFERENCE' else cases[identifier]['prompt'];s.frame_set(1)
def _update(self,context):
    if self.unimate_stance_case:select_case(self.unimate_stance_case)
class UNIMATE_OT_stance_step(bpy.types.Operator):
    bl_idname='unimate.stance_step';bl_label='Next stance comparison';delta:bpy.props.IntProperty(default=1)
    def execute(self,context):
        s=context.scene;keys=['REFERENCE']+list(json.loads(s['cases']));s.unimate_stance_case=keys[(keys.index(s['active_case'])+self.delta)%len(keys)];return {'FINISHED'}
class UNIMATE_PT_stance_review(bpy.types.Panel):
    bl_label='Reference stance comparison';bl_idname='UNIMATE_PT_stance_review';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='UniMate'
    @classmethod
    def poll(cls,context):return context.scene.name==SCENE
    def draw(self,context):
        s=context.scene;l=self.layout;l.prop(s,'unimate_stance_case',text='Case');r=l.row(align=True);r.operator('unimate.stance_step',text='Previous').delta=-1;r.operator('unimate.stance_step',text='Next').delta=1
        for line in textwrap.wrap(s.get('active_prompt',''),34):l.label(text=line)
        l.separator();l.label(text='Left: upright reference');l.label(text='Right: quadrupedal reference');l.label(text='Same lengths / labels / noise');l.label(text='No starting frame imposed');l.label(text='Raw; playback wrap hard-resets')
for cls in [UNIMATE_OT_stance_step,UNIMATE_PT_stance_review]:
    old=getattr(bpy.types,cls.__name__,None)
    if old:bpy.utils.unregister_class(old)
    bpy.utils.register_class(cls)
s=bpy.data.scenes.get(SCENE)
if s:
    _ITEMS=[('REFERENCE','Input reference poses','Authored static references; not generated animation')]+[(k,k,v['prompt']) for k,v in json.loads(s['cases']).items()];bpy.types.Scene.unimate_stance_case=bpy.props.EnumProperty(items=_ITEMS,update=_update);s.unimate_stance_case=s.get('active_case','REFERENCE')
