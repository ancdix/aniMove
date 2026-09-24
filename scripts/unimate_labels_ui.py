"""Blender sidebar for matched three-way joint-label comparisons."""
import bpy,json,textwrap,itertools
from mathutils import Vector
SCENE='PILGRIM_UniMate_LABELS'
VARIANTS=['arms_legs','front_hind','neutral_limbs']
_ITEMS=[]
def select_case(identifier):
    s=bpy.data.scenes[SCENE];case=json.loads(s['cases'])[identifier];rig_names=json.loads(s['rigs']);points=[]
    for variant in VARIANTS:
        rig=s.objects[rig_names[variant]];action=bpy.data.actions['UNI_'+variant+'_'+case['prompt_id']+'_s'+str(case['seed'])];rig.animation_data.action=action
        if action.slots:rig.animation_data.action_slot=action.slots[0]
        lo=action['bounds_min'];hi=action['bounds_max']
        for x,y,z in itertools.product(*zip(lo,hi)):points.append(Vector((x,-z,y))+rig.location)
    low=Vector(tuple(min(p[i] for p in points) for i in range(3)));high=Vector(tuple(max(p[i] for p in points) for i in range(3)));low.z=min(low.z,-.2);high.z+=.7;center=(low+high)/2;cam=s.camera;cam.location=center+Vector((0,-20,7));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();inverse=cam.rotation_euler.to_quaternion().inverted();corners=[inverse@(Vector(v)-center) for v in itertools.product(*zip(low,high))];aspect=s.render.resolution_x/s.render.resolution_y;cam.data.ortho_scale=max(max(p.x for p in corners)-min(p.x for p in corners),(max(p.y for p in corners)-min(p.y for p in corners))*aspect)*1.12
    for variant in VARIANTS:
        title=s.objects['LABEL_TITLE_'+variant];title.location=(s.objects[rig_names[variant]].location.x,center.y,high.z-.3);title.rotation_euler=cam.rotation_euler
    s['active_case']=identifier;s['active_prompt']=case['prompt'];s.frame_set(1)

def _update(self,context):
    if self.unimate_label_case:select_case(self.unimate_label_case)
class UNIMATE_OT_label_step(bpy.types.Operator):
    bl_idname='unimate.label_step';bl_label='Next matched label case'
    delta:bpy.props.IntProperty(default=1)
    def execute(self,context):
        s=context.scene;names=list(json.loads(s['cases']));s.unimate_label_case=names[(names.index(s['active_case'])+self.delta)%len(names)];return {'FINISHED'}
class UNIMATE_PT_label_review(bpy.types.Panel):
    bl_label='Matched joint labels';bl_idname='UNIMATE_PT_label_review';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='UniMate'
    @classmethod
    def poll(cls,context):return context.scene.name==SCENE
    def draw(self,context):
        s=context.scene;l=self.layout;l.prop(s,'unimate_label_case',text='Case');r=l.row(align=True);r.operator('unimate.label_step',text='Previous').delta=-1;r.operator('unimate.label_step',text='Next').delta=1
        for line in textwrap.wrap(s.get('active_prompt',''),34):l.label(text=line)
        l.separator();l.label(text='Left: arms + legs');l.label(text='Center: front + hind legs');l.label(text='Right: generic Bone');l.label(text='Same skeleton / prompt / noise');l.label(text='Display offsets only; raw motion');l.label(text='30 fps; wrap is a hard reset')
for cls in [UNIMATE_OT_label_step,UNIMATE_PT_label_review]:
    old=getattr(bpy.types,cls.__name__,None)
    if old:bpy.utils.unregister_class(old)
    bpy.utils.register_class(cls)
s=bpy.data.scenes.get(SCENE)
if s:
    cases=json.loads(s['cases']);_ITEMS=[(key,key,value['prompt']) for key,value in cases.items()];bpy.types.Scene.unimate_label_case=bpy.props.EnumProperty(items=_ITEMS,update=_update);s.unimate_label_case=s.get('active_case',_ITEMS[0][0])
