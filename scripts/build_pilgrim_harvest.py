"""Build a discovered motion phrase with editable controls, FK bake, and raw comparison."""
import json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_pilgrim_blockout import build
from build_robot_blender import primitive,material,relocate,linear_keys
from motion_lab import to_blender
from pilgrim_controls import install,bake_fk

p=Path(sys.argv[sys.argv.index('--')+1]);d=json.loads((p/'skeleton.json').read_text());r=json.loads((p/'motion.json').read_text());title=r['title'];prefix='HARVEST_'+title.upper();frames=r['frames'];cyclic=r['cyclic'];count=frames+int(cyclic);m=np.load(p/'motion.npz');out=p/'harvest_comparison.blend';assert not out.exists()
scene=bpy.data.scenes.new('PILGRIM_'+title+'_Compare');bpy.context.window.scene=scene;scene.frame_start=1;scene.frame_end=frames;scene.render.fps=r['fps']
cols={}
for n in ['BODY','CONTROLS','RAW','STAGE','CONTACTS']:
    c=bpy.data.collections.new(prefix+'_'+n);scene.collection.children.link(c);cols[n]=c
xyz,poles=to_blender(m['clean']),to_blender(m['poles']);rig=build(d,xyz,poles,cols['BODY'],cols['CONTROLS'],prefix)
rig.animation_data.action.name=prefix+'_Controls_v001';control_action=rig.animation_data.action
controls=install(rig,d,xyz,cols['CONTROLS'],prefix=prefix+'_CTRL',contacts=m['contacts'],preserve_distal=True,anchor_paths=to_blender(m['anchor_paths']),cyclic=cyclic);rig['animation_origin']=r['authorship']
before=[];after=[]
for f in range(count):
    scene.frame_set(f+1);e=rig.evaluated_get(bpy.context.evaluated_depsgraph_get());actual=np.array([e.pose.bones[n].head[:] for n in d['names']]);after.append(actual)
errors=np.linalg.norm(np.array(after)-xyz,axis=-1)
report=dict(control_joint_max_error=float(errors.max()),control_joint_rms_error=float(np.sqrt(np.mean(errors**2))),source=r['source'],contact_schedule='Candidates inferred from original raw height and speed',control_action=control_action.name)
print('CONTROL_BUILD',json.dumps(report),flush=True)
if errors.max()>1e-4:raise RuntimeError('Control rig does not reproduce corrected joints: '+str(errors.max()))
action=bake_fk(rig,prefix+'_Final_FK_v001',r['fps']/80,cyclic=cyclic);report['baked_action']=action.name;report['bake_hz']=80
rig['baked_action']=action.name;rig['control_action']=control_action.name
raw=to_blender(m['raw']);raw[:,:,0]-=3.1
teal=material('Settling raw',(.10,.56,.58));accent=material('Settling raw contact',(.85,.56,.19));green=material('Settling planted',(.17,.62,.35));white=material('Settling label',(.92,.92,.86))
for j,n in enumerate(d['names']):
    o=primitive(prefix+'_RAW_'+n,'sphere',(0,0,0),(.037,)*3,accent if j in d['contact_joints'] else teal,cols['RAW'])
    for f,pos in enumerate(raw[:,j]):o.location=pos;o.keyframe_insert('location',frame=f+1)
    linear_keys(o);pa=d['parents'][j]
    if pa<0:continue
    link=primitive(prefix+'_RAW_LINK_'+n,'cylinder',(0,0,0),(.012,.012,1),teal,cols['RAW']);link.modifiers.clear();link.rotation_mode='QUATERNION';last=None
    for f in range(frames):
        a,b=raw[f,pa],raw[f,j];v=Vector(b-a);q=v.to_track_quat('Z','Y')
        if last is not None and q.dot(last)<0:q.negate()
        last=q.copy();link.location=(a+b)/2;link.rotation_quaternion=q;link.scale.z=v.length/2
        for prop in ['location','rotation_quaternion','scale']:link.keyframe_insert(prop,frame=f+1)
    linear_keys(link)
floor=material('Settling stage',(.115,.13,.145));primitive('Settling floor','cube',(0,0,-.045),(100,100,.045),floor,cols['STAGE'])
bpy.ops.object.camera_add(location=(2.4,-9,4));cam=bpy.context.object;relocate(cam,cols['STAGE']);cam.rotation_euler=(Vector((-1.45,0,1.45))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=8.;scene.camera=cam
def label(body,x,y,size):
    data=bpy.data.curves.new(body,'FONT');data.body=body;data.size=size;obj=bpy.data.objects.new(body,data);cols['STAGE'].objects.link(obj);obj.parent=cam;obj.location=(x,y,-6);data.materials.append(white)
label('MOTION HARVEST / '+title.replace('_',' ').upper(),-3.65,2.20,.22)
label('Unguided source / contact and constant clearance edits'+(' / uniform half speed' if cyclic else ' / native timing'),-3.65,1.92,.115)
label('RAW ANYTOP',-3.35,-2.05,.16);label('CLEANED PHRASE',.20,-2.05,.16)
label('Original positions / aligned playback',-3.35,-2.27,.095);label('Fitted body/head retained'+(' in interior' if cyclic else ''),.20,-2.27,.095)
label('Contacts are inferred candidates; static clearance corrections are recorded. No authored action guide.',-3.65,-2.50,.10)
scene.world=bpy.data.worlds.new('Settling world');scene.world.color=(.115,.13,.145);scene.render.engine='BLENDER_WORKBENCH';sh=scene.display.shading;sh.light='STUDIO';sh.studio_light='paint.sl';sh.color_type='MATERIAL';sh.show_shadows=False;sh.show_cavity=True;sh.cavity_type='BOTH';sh.background_type='WORLD'
scene.render.resolution_x=1400;scene.render.resolution_y=940;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene['asset_directory']=str(p);scene['instructions']=r['description']+' '+r['authorship']
scene['rig']=rig.name;scene['control_action']=control_action.name;scene['baked_action']=action.name;scene['closing_key']=count
scene.timeline_markers.new('Source start',frame=1);scene.timeline_markers.new('Source end',frame=frames)
for o in bpy.context.selected_objects:o.select_set(False)
rig.select_set(True);bpy.context.view_layer.objects.active=rig;scene.frame_set(1)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            s=area.spaces.active;s.region_3d.view_perspective='CAMERA';s.shading.color_type='MATERIAL';s.overlay.show_extras=False;s.overlay.show_bones=False
bpy.data.texts.new('README_'+prefix).write(scene['instructions']+'\n\n'+json.dumps(r,indent=2))
bpy.data.texts.new(prefix+'_CONTROL_UTILITIES.py').write('import sys\nsys.path.insert(0, '+repr(str(Path(__file__).parent))+')\n'+(Path(__file__).parent/'pilgrim_controls.py').read_text())
(p/'build_validation.json').write_text(json.dumps(report,indent=2)+'\n');bpy.ops.wm.save_as_mainfile(filepath=str(out))
scene.render.filepath=str(p/'comparison.png');bpy.ops.render.render(write_still=True)
print('HARVEST_BUILT',str(out),flush=True)

# Separate solo scene shares the same editable rig and Actions.
comparison=scene
scene=bpy.data.scenes.new('PILGRIM_'+title);bpy.context.window.scene=scene;scene.frame_start=1;scene.frame_end=frames;scene.render.fps=r['fps']
for c in [cols['BODY'],cols['CONTROLS']]:scene.collection.children.link(c)
stage=bpy.data.collections.new(prefix+'_STAGE');scene.collection.children.link(stage)
primitive(prefix+' floor','cube',(0,0,-.045),(100,100,.045),floor,stage)
bpy.ops.object.camera_add(location=(4,-7,3.3));cam=bpy.context.object;relocate(cam,stage);cam.rotation_euler=(Vector((0,-.25,1.45))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=4.15;scene.camera=cam
scene.world=comparison.world;scene.render.engine='BLENDER_WORKBENCH';sh=scene.display.shading;sh.light='STUDIO';sh.studio_light='paint.sl';sh.color_type='MATERIAL';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.background_type='WORLD'
scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
for k in ['rig','control_action','baked_action','closing_key','asset_directory','instructions']:scene[k]=comparison[k]
scene.timeline_markers.new('Source start',frame=1);scene.timeline_markers.new('Source end',frame=frames)
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(p/'harvest_master.blend'))
for name,f in [('start',1),('middle',frames//2),('end',frames)]:
 scene.frame_set(f);scene.render.filepath=str(p/('pose_'+name+'.png'));bpy.ops.render.render(write_still=True)
