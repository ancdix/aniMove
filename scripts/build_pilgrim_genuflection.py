"""Build a directed genuflection study, editable rig, FK bake, and raw comparison."""
import json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_pilgrim_blockout import build
from build_robot_blender import primitive,material,relocate,linear_keys
from motion_lab import to_blender
from pilgrim_controls import install,bake_fk

p=Path(sys.argv[sys.argv.index('--')+1]);d=json.loads((p/'skeleton.json').read_text());r=json.loads((p/'loop.json').read_text());m=np.load(p/'motion.npz');out=p/'pilgrim_genuflection.blend';assert not out.exists()
scene=bpy.data.scenes.new('PILGRIM_Genuflection_Loop');bpy.context.window.scene=scene;scene.frame_start=1;scene.frame_end=240;scene.render.fps=20
cols={}
for n in ['BODY','CONTROLS','RAW','STAGE','CONTACTS']:
    c=bpy.data.collections.new('PILGRIM_GENU_CTRL_'+n);scene.collection.children.link(c);cols[n]=c
xyz,poles=to_blender(m['clean']),to_blender(m['poles']);rig=build(d,xyz,poles,cols['BODY'],cols['CONTROLS'],'PILGRIM_GENU')
rig.animation_data.action.name='PILGRIM_Genuflection_Controls_v001';control_action=rig.animation_data.action
controls=install(rig,d,xyz,cols['CONTROLS'],prefix='PILGRIM_GENU_CTRL',contacts=m['contacts'],anchors=to_blender(m['anchors']));rig['animation_origin']=r['contribution']
before=[];after=[]
for f in range(241):
    scene.frame_set(f+1);e=rig.evaluated_get(bpy.context.evaluated_depsgraph_get());actual=np.array([e.pose.bones[n].head[:] for n in d['names']]);after.append(actual)
errors=np.linalg.norm(np.array(after)-xyz,axis=-1)
report=dict(control_joint_max_error=float(errors.max()),control_joint_rms_error=float(np.sqrt(np.mean(errors**2))),source=r['pilot'],contact_schedule='A then B plant; B then A release; C/D planted throughout',control_action=control_action.name)
print('CONTROL_BUILD',json.dumps(report),flush=True)
if errors.max()>1e-4:raise RuntimeError('Control rig does not reproduce corrected joints: '+str(errors.max()))
action=bake_fk(rig,'PILGRIM_Genuflection_Final_FK_v001',.25);report['baked_action']=action.name;report['bake_hz']=80
rig['baked_action']=action.name;rig['control_action']=control_action.name
raw=to_blender(m['raw']);raw[:,:,0]-=3.1
teal=material('Settling raw',(.10,.56,.58));accent=material('Settling raw contact',(.85,.56,.19));green=material('Settling planted',(.17,.62,.35));white=material('Settling label',(.92,.92,.86))
for j,n in enumerate(d['names']):
    o=primitive('GENU_RAW_'+n,'sphere',(0,0,0),(.037,)*3,accent if j in d['contact_joints'] else teal,cols['RAW'])
    for f,pos in enumerate(raw[:,j]):o.location=pos;o.keyframe_insert('location',frame=f+1)
    linear_keys(o);pa=d['parents'][j]
    if pa<0:continue
    link=primitive('GENU_RAW_LINK_'+n,'cylinder',(0,0,0),(.012,.012,1),teal,cols['RAW']);link.modifiers.clear();link.rotation_mode='QUATERNION';last=None
    for f in range(240):
        a,b=raw[f,pa],raw[f,j];v=Vector(b-a);q=v.to_track_quat('Z','Y')
        if last is not None and q.dot(last)<0:q.negate()
        last=q.copy();link.location=(a+b)/2;link.rotation_quaternion=q;link.scale.z=v.length/2
        for prop in ['location','rotation_quaternion','scale']:link.keyframe_insert(prop,frame=f+1)
    linear_keys(link)
for key in 'ABCD':
    a=to_blender(m['anchors'])['ABCD'.index(key)].copy();a[2]=.003
    marker=primitive('PLANTED_'+key,'cylinder',a,(.19,.19,.003),green,cols['CONTACTS']);marker.modifiers.clear()
floor=material('Settling stage',(.115,.13,.145));primitive('Settling floor','cube',(0,0,-.045),(100,100,.045),floor,cols['STAGE'])
bpy.ops.object.camera_add(location=(2.4,-9,4));cam=bpy.context.object;relocate(cam,cols['STAGE']);cam.rotation_euler=(Vector((-1.45,0,1.45))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=8.;scene.camera=cam
def label(body,x,y,size):
    data=bpy.data.curves.new(body,'FONT');data.body=body;data.size=size;obj=bpy.data.objects.new(body,data);cols['STAGE'].objects.link(obj);obj.parent=cam;obj.location=(x,y,-6);data.materials.append(white)
label('PILGRIM / FIRST GENUFLECTION',-3.65,2.20,.22)
label('Authored choreography + AnyTop transition variation / 12-second blockout study',-3.65,1.92,.115)
label('RAW GUIDED ANYTOP',-3.35,-2.05,.16);label('DIRECTED GENUFLECTION',.20,-2.05,.16)
label('Original guided output before mechanical cleanup',-3.35,-2.27,.095);label('Authored contacts + bounded generated transitions',.20,-2.27,.095)
label('Authored storyboard, contacts and mechanical cleanup; AnyTop transition variation',-3.65,-2.50,.10)
scene.world=bpy.data.worlds.new('Settling world');scene.world.color=(.115,.13,.145);scene.render.engine='BLENDER_WORKBENCH';sh=scene.display.shading;sh.light='STUDIO';sh.studio_light='paint.sl';sh.color_type='MATERIAL';sh.show_shadows=False;sh.show_cavity=True;sh.cavity_type='BOTH';sh.background_type='WORLD'
scene.render.resolution_x=1400;scene.render.resolution_y=940;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene['asset_directory']=str(p);scene['instructions']='First Genuflection: 12 seconds at 20 fps. Authored storyboard/contact schedule with bounded AnyTop-generated transition variation. Raw inpaints at left. Frames 1-240; closing key 241. Controls in PILGRIM_GENU_CTRL; enable Extras overlays. Baked FK Action requires use_controls=0. See loop.json for substantial corrections.'
scene['rig']=rig.name;scene['control_action']=control_action.name;scene['baked_action']=action.name;scene['closing_key']=241
for name,f in r['events'].items():scene.timeline_markers.new(name.replace('_',' '),frame=f)
for o in bpy.context.selected_objects:o.select_set(False)
rig.select_set(True);bpy.context.view_layer.objects.active=rig;scene.frame_set(1)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            s=area.spaces.active;s.region_3d.view_perspective='CAMERA';s.shading.color_type='MATERIAL';s.overlay.show_extras=False;s.overlay.show_bones=False
bpy.data.texts.new('README_PILGRIM_GENUFLECTION').write(scene['instructions']+'\n\n'+json.dumps(r,indent=2))
bpy.data.texts.new('PILGRIM_GENU_CONTROL_UTILITIES.py').write('import sys\nsys.path.insert(0, '+repr(str(Path(__file__).parent))+')\n'+(Path(__file__).parent/'pilgrim_controls.py').read_text())
(p/'build_validation.json').write_text(json.dumps(report,indent=2)+'\n');bpy.ops.wm.save_as_mainfile(filepath=str(out))
scene.render.filepath=str(p/'genuflection_comparison.png');bpy.ops.render.render(write_still=True)
print('GENUFLECTION_BUILT',str(out),flush=True)

# Separate solo scene shares the same editable rig and Actions.
comparison=scene
scene=bpy.data.scenes.new('PILGRIM_First_Genuflection');bpy.context.window.scene=scene;scene.frame_start=1;scene.frame_end=240;scene.render.fps=20
for c in [cols['BODY'],cols['CONTROLS']]:scene.collection.children.link(c)
stage=bpy.data.collections.new('PILGRIM_GENU_STAGE');scene.collection.children.link(stage)
primitive('Genuflection floor','cube',(0,0,-.045),(100,100,.045),floor,stage)
bpy.ops.object.camera_add(location=(4,-7,3.3));cam=bpy.context.object;relocate(cam,stage);cam.rotation_euler=(Vector((0,-.25,1.45))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=4.15;scene.camera=cam
scene.world=comparison.world;scene.render.engine='BLENDER_WORKBENCH';sh=scene.display.shading;sh.light='STUDIO';sh.studio_light='paint.sl';sh.color_type='MATERIAL';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.background_type='WORLD'
scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
for k in ['rig','control_action','baked_action','closing_key','asset_directory','instructions']:scene[k]=comparison[k]
for name,f in r['events'].items():scene.timeline_markers.new(name.replace('_',' '),frame=f)
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(p/'pilgrim_genuflection_master.blend'))
for name,f in [('upright',1),('bow',57),('first_hand',79),('four_contacts',121),('turn',161),('recovery',197)]:
 scene.frame_set(f);scene.render.filepath=str(p/('pose_'+name+'.png'));bpy.ops.render.render(write_still=True)
