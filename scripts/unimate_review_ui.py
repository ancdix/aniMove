"""Run inside Blender; adds a reversible raw-clip selector to the sidebar."""
import bpy,json,textwrap
_ITEMS=[]

def _update(self,context):
    if self.unimate_raw_clip:
        ns={};exec(bpy.data.texts['UNIMATE_REVIEW_UTILITIES.py'].as_string(),ns);ns['select_clip'](self.unimate_raw_clip)

class UNIMATE_OT_step(bpy.types.Operator):
    bl_idname='unimate.step_clip';bl_label='Next raw clip'
    delta:bpy.props.IntProperty(default=1)
    def execute(self,context):
        s=context.scene;names=json.loads(s['action_names']);current=s.get('active_clip',names[0]);s.unimate_raw_clip=names[(names.index(current)+self.delta)%len(names)];return {'FINISHED'}

class UNIMATE_PT_raw_review(bpy.types.Panel):
    bl_label='UniMate — raw review';bl_idname='UNIMATE_PT_raw_review';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='UniMate'
    @classmethod
    def poll(cls,context):return context.scene.name=='PILGRIM_UniMate_RAW'
    def draw(self,context):
        s=context.scene;layout=self.layout;layout.prop(s,'unimate_raw_clip',text='Clip');row=layout.row(align=True);row.operator('unimate.step_clip',text='Previous').delta=-1;row.operator('unimate.step_clip',text='Next').delta=1
        for line in textwrap.wrap(s.get('active_prompt',''),34):layout.label(text=line)
        layout.separator();layout.label(text='Raw • 30 fps • CFG 3');layout.label(text='No IK / contact correction');layout.label(text='Playback wrap is a hard reset')

for cls in [UNIMATE_OT_step,UNIMATE_PT_raw_review]:
    existing=getattr(bpy.types,cls.__name__,None)
    if existing:bpy.utils.unregister_class(existing)
    bpy.utils.register_class(cls)
s=bpy.data.scenes.get('PILGRIM_UniMate_RAW')
if s:
    _ITEMS=[(name,name,bpy.data.actions[name].get('prompt','')) for name in json.loads(s['action_names'])]
    bpy.types.Scene.unimate_raw_clip=bpy.props.EnumProperty(items=_ITEMS,update=_update)
    s.unimate_raw_clip=s.get('active_clip',_ITEMS[0][0])
