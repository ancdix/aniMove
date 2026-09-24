"""Build the editable settling loop, a separate visual FK bake, and raw comparison."""
import json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_pilgrim_blockout import build
from build_robot_blender import primitive,material,relocate,linear_keys
from motion_lab import to_blender
from pilgrim_controls import install,bake_fk

p=Path(sys.argv[sys.argv.index('--')+1]);d=json.loads((p/'skeleton.json').read_text());r=json.loads((p/'loop.json').read_text());m=np.load(p/'motion.npz');out=p/'pilgrim_devotional.blend';assert not out.exists()
scene=bpy.data.scenes.new('PILGRIM_Devotional_Loop');bpy.context.window.scene=scene;scene.frame_start=1;scene.frame_end=120;scene.render.fps=20
cols={}
for n in ['BODY','CONTROLS','RAW','STAGE','CONTACTS']:
    c=bpy.data.collections.new('PILGRIM_SETTLE_'+n);scene.collection.children.link(c);cols[n]=c
xyz,poles=to_blender(m['clean']),to_blender(m['poles']);rig=build(d,xyz,poles,cols['BODY'],cols['CONTROLS'],'PILGRIM_LOOP')
rig.animation_data.action.name='PILGRIM_Devotional_Controls_v001';control_action=rig.animation_data.action
controls=install(rig,d,xyz,cols['CONTROLS']);rig['animation_origin']='Direct Pilgrim AnyTop seed 5100, with explicit contact, clearance and periodic-boundary corrections. See loop.json.'
before=[];after=[]
for f in range(121):
    scene.frame_set(f+1);e=rig.evaluated_get(bpy.context.evaluated_depsgraph_get());actual=np.array([e.pose.bones[n].head[:] for n in d['names']]);after.append(actual)
errors=np.linalg.norm(np.array(after)-xyz,axis=-1)
report=dict(control_joint_max_error=float(errors.max()),control_joint_rms_error=float(np.sqrt(np.mean(errors**2))),source=r['source'],contact_schedule='A/B free; C/D planted',control_action=control_action.name)
print('CONTROL_BUILD',json.dumps(report),flush=True)
if errors.max()>1e-4:raise RuntimeError('Control rig does not reproduce corrected joints: '+str(errors.max()))
action=bake_fk(rig,'PILGRIM_Devotional_Final_FK_v001',.25);report['baked_action']=action.name;report['bake_hz']=80
rig['baked_action']=action.name;rig['control_action']=control_action.name
raw=to_blender(m['raw']);raw[:,:,0]-=3.1
teal=material('Settling raw',(.10,.56,.58));accent=material('Settling raw contact',(.85,.56,.19));green=material('Settling planted',(.17,.62,.35));white=material('Settling label',(.92,.92,.86))
for j,n in enumerate(d['names']):
    o=primitive('SETTLE_RAW_'+n,'sphere',(0,0,0),(.037,)*3,accent if j in d['contact_joints'] else teal,cols['RAW'])
    for f,pos in enumerate(raw[:,j]):o.location=pos;o.keyframe_insert('location',frame=f+1)
    linear_keys(o);pa=d['parents'][j]
    if pa<0:continue
    link=primitive('SETTLE_RAW_LINK_'+n,'cylinder',(0,0,0),(.012,.012,1),teal,cols['RAW']);link.modifiers.clear();link.rotation_mode='QUATERNION';last=None
    for f in range(120):
        a,b=raw[f,pa],raw[f,j];v=Vector(b-a);q=v.to_track_quat('Z','Y')
        if last is not None and q.dot(last)<0:q.negate()
        last=q.copy();link.location=(a+b)/2;link.rotation_quaternion=q;link.scale.z=v.length/2
        for prop in ['location','rotation_quaternion','scale']:link.keyframe_insert(prop,frame=f+1)
    linear_keys(link)
for key in 'CD':
    a=xyz[0,d['names'].index(key+'_3')].copy();a[2]=.003
    marker=primitive('PLANTED_'+key,'cylinder',a,(.19,.19,.003),green,cols['CONTACTS']);marker.modifiers.clear()
floor=material('Settling stage',(.115,.13,.145));primitive('Settling floor','cube',(0,0,-.045),(100,100,.045),floor,cols['STAGE'])
bpy.ops.object.camera_add(location=(2.4,-9,4));cam=bpy.context.object;relocate(cam,cols['STAGE']);cam.rotation_euler=(Vector((-1.45,0,1.45))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=8.;scene.camera=cam
def label(body,x,y,size):
    data=bpy.data.curves.new(body,'FONT');data.body=body;data.size=size;obj=bpy.data.objects.new(body,data);cols['STAGE'].objects.link(obj);obj.parent=cam;obj.location=(x,y,-6);data.materials.append(white)
label('PILGRIM / DEVOTIONAL HOLD',-3.65,2.20,.22)
label('AnyTop body and head motion / planted support feet / six-second loop',-3.65,1.92,.115)
label('ORIGINAL ANYTOP',-3.35,-2.05,.16);label('CONTACT-CLEANED LOOP',.20,-2.05,.16)
label('Raw source repeats with its original seam',-3.35,-2.27,.095);label('C/D planted - A/B free - editable controls',.20,-2.27,.095)
label('Authored cleanup: foot anchors, hand clearance, distal orientation and boundary blend',-3.65,-2.50,.10)
scene.world=bpy.data.worlds.new('Settling world');scene.world.color=(.115,.13,.145);scene.render.engine='BLENDER_WORKBENCH';sh=scene.display.shading;sh.light='STUDIO';sh.studio_light='paint.sl';sh.color_type='MATERIAL';sh.show_shadows=False;sh.show_cavity=True;sh.cavity_type='BOTH';sh.background_type='WORLD'
scene.render.resolution_x=1400;scene.render.resolution_y=940;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene['asset_directory']=str(p);scene['instructions']='Six-second loop, 20 fps, frames 1-120 with closing key 121. Right: contact-cleaned Pilgrim using editable controls. Left: original unlooped raw AnyTop XYZ. Select PILGRIM_SETTLE_CTRL_* objects; enable Extras overlays to see control shapes. Rig properties: contact_A-D, ik_A-D, head_world_lock, head_look_at, use_controls. To use baked Action: use_controls=0 and choose PILGRIM_Devotional_Final_FK_v001. Previous scenes preserved.'
scene['rig']=rig.name;scene['control_action']=control_action.name;scene['baked_action']=action.name;scene['closing_key']=121
scene.timeline_markers.new('Loop start',frame=1);scene.timeline_markers.new('Generated interior',frame=13);scene.timeline_markers.new('Boundary join',frame=109)
for o in bpy.context.selected_objects:o.select_set(False)
rig.select_set(True);bpy.context.view_layer.objects.active=rig;scene.frame_set(1)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            s=area.spaces.active;s.region_3d.view_perspective='CAMERA';s.shading.color_type='MATERIAL';s.overlay.show_extras=False;s.overlay.show_bones=False
bpy.data.texts.new('README_PILGRIM_DEVOTIONAL').write(scene['instructions']+'\n\n'+json.dumps(r,indent=2))
bpy.data.texts.new('PILGRIM_CONTROL_UTILITIES.py').write('import sys\nsys.path.insert(0, '+repr(str(Path(__file__).parent))+')\n'+(Path(__file__).parent/'pilgrim_controls.py').read_text())
(p/'build_validation.json').write_text(json.dumps(report,indent=2)+'\n');bpy.ops.wm.save_as_mainfile(filepath=str(out))
scene.render.filepath=str(p/'devotional.png');bpy.ops.render.render(write_still=True)
print('DEVOTIONAL_BUILT',str(out),flush=True)
