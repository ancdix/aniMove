"""Raw generated loop beside the contact-corrected robot, with explicit guidance masks."""
import sys,json,subprocess
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_robot_blender import build_rig,material,primitive,relocate,linear_keys
p=Path(sys.argv[sys.argv.index('--')+1]);r=json.loads((p/'retarget.json').read_text());m=np.load(p/'motion.npz');run=json.loads(Path(r['raw_run']).read_text())
assert not (p/'rise_land_loop.blend').exists()
scene=bpy.data.scenes.new('ANYTOP_Rise_Land_Loop');bpy.context.window.scene=scene;scene.frame_start=1;scene.frame_end=120;scene.render.fps=20
cols={}
for k in ['ROBOT_RIG','IK_TARGETS','DEBUG_CONTACTS','CAMERA_LIGHTS','STAGE','SOURCE']:
 c=bpy.data.collections.new('LOOP_'+k);scene.collection.children.link(c);cols[k]=c
colors=dict(silver=(.52,.62,.69),dark=(.035,.055,.075),amber=(.97,.50,.10),blue=(.025,.48,.8),green=(.13,.72,.28),floor=(.035,.05,.075),white=(.88,.92,.97),source=(.30,.78,.78),A=(.95,.32,.11),B=(.20,.72,1),C=(.92,.72,.12),D=(.67,.35,.95))
mats={k:material('LOOP '+k,v) for k,v in colors.items()}
rig,validation=build_rig('RISE_LAND_ROBOT','clean',1.65,m,r,cols,mats);rig['ik_fk']=1.;rig.update_tag()
for k in 'ABCD':
 foot=bpy.data.objects[rig.name+'_'+k+'_foot'];foot.data.materials.clear();foot.data.materials.append(mats[k])
xyz=m['source_xyz']+[-1.65,0,0];endpoints={r['joint_names'].index(l['endpoint']):k for k,l in r['config']['limbs'].items()}
for j,name in enumerate(r['joint_names']):
 radius=.035 if j in endpoints else .017;obj=primitive('LOOP_SOURCE_JOINT_'+str(j),'sphere',(0,0,0),(radius,)*3,mats[endpoints.get(j,'source')],cols['SOURCE']);obj['source_index']=j
 for f,pos in enumerate(xyz[:,j]):obj.location=pos;obj.keyframe_insert('location',frame=f+1)
 linear_keys(obj);parent=r['parents'][j]
 if parent<0:continue
 link=primitive('LOOP_SOURCE_LINK_'+str(j),'cylinder',(0,0,0),(.01,.01,1),mats['source'],cols['SOURCE']);link.modifiers.clear();link.rotation_mode='QUATERNION';last=None
 for f in range(120):
  a,b=xyz[f,parent],xyz[f,j];d=Vector(b-a);q=d.to_track_quat('Z','Y')
  if last is not None and q.dot(last)<0:q.negate()
  last=q.copy();link.rotation_quaternion=q;link.location=(a+b)/2;link.scale.z=max(d.length/2,1e-7)
  for prop in ['location','rotation_quaternion','scale']:link.keyframe_insert(prop,frame=f+1)
 linear_keys(link)
primitive('Loop floor','cube',(0,0,-.04),(5,3,.04),mats['floor'],cols['STAGE'])
bpy.ops.object.camera_add(location=(3,-8,4.7));camera=bpy.context.object;relocate(camera,cols['CAMERA_LIGHTS']);camera.rotation_euler=(Vector((0,-.1,.65))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=8.8;scene.camera=camera

def label(body,x,y,size,color='white'):
 data=bpy.data.curves.new(body,'FONT');data.body=body;data.size=size;obj=bpy.data.objects.new(body,data);cols['CAMERA_LIGHTS'].objects.link(obj);obj.parent=camera;obj.location=(x,y,-6);data.materials.append(mats[color]);return obj
label('RISE / LOWER / SETTLE / REPEAT',-4.0,2.38,.26)
label('AnyTop with authored torso guidance / raw landing remains free / 6-second closed cycle',-4.0,2.08,.125)
label('RAW GUIDED ANYTOP',-3.8,-1.72,.17,'source');label('CORRECTED ROBOT LOOP',.35,-1.72,.17,'blue')
label('Generated limbs can snap or miss contact',-3.8,-1.94,.11);label('Smoothing + reach correction + planted feet',.35,-1.94,.11)
left,right=-3.8,3.8
label('Pose windows / generated gaps',left,-2.17,.105)
windows=run['masks']['body_guided']
for start,stop in [(0,120)]+windows:
 mat='amber' if (start,stop)==(0,120) else 'source'
 obj=primitive('Guidance timeline','cube',(0,0,0),((right-left)*(stop-start)/240,.018,.001),mats[mat],cols['CAMERA_LIGHTS']);obj.modifiers.clear();obj.parent=camera;obj.location=(left+(right-left)*(start+stop)/240,-2.29,-6 if mat=='amber' else -5.99)
# This separate band makes the continuous torso constraint visible rather than hiding it.
obj=primitive('Torso guide band','cube',(0,0,0),((right-left)*83/240,.014,.001),mats['blue'],cols['CAMERA_LIGHTS']);obj.modifiers.clear();obj.parent=camera;obj.location=(left+(right-left)*83/240,-2.38,-6)
label('Torso guided to 4.15 s',left,-2.57,.10,'blue');label('Free landing probe: 4.15-5.5 s',.45,-2.57,.10,'amber')
cursor=primitive('Loop time cursor','sphere',(0,0,0),(.042,)*3,mats['white'],cols['CAMERA_LIGHTS']);cursor.parent=camera
for frame,x in [(1,left),(120,right)]:cursor.location=(x,-2.29,-5.98);cursor.keyframe_insert('location',frame=frame)
linear_keys(cursor)
scene.world=bpy.data.worlds.new('Loop world');scene.world.color=(.035,.05,.075)
scene.render.engine='BLENDER_WORKBENCH';sh=scene.display.shading;sh.light='STUDIO';sh.studio_light='paint.sl';sh.color_type='MATERIAL';sh.show_shadows=False;sh.show_cavity=True;sh.cavity_type='BOTH';sh.background_type='WORLD'
scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage=1600,1000,100;scene.render.image_settings.file_format='PNG'
scene['experiment_manifest']=r['raw_run'];scene['robot_directory']=str(p);scene['source_offset_x']=-1.65;scene['instructions']='120-frame closed loop, IK enabled. Raw AnyTop left; corrected robot right. Torso/root guidance and pose windows are authored. Landing probe uses uncorrected generated frames 84-110. No simulated physics or verified balance. Raw failures are retained; cleanup includes measured free-foot reach projection.'
scene.frame_set(54)
for obj in bpy.context.selected_objects:obj.select_set(False)
rig.select_set(True);bpy.context.view_layer.objects.active=rig
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   s=area.spaces.active;s.region_3d.view_perspective='CAMERA';s.shading.color_type='MATERIAL';s.overlay.show_extras=False;s.overlay.show_bones=False;s.overlay.show_relationship_lines=False;s.overlay.show_cursor=False
bpy.data.texts.new('README_RISE_LAND_LOOP').write(scene['instructions']+'\n\n'+json.dumps(r,indent=2))
(p/'blender_build_validation.json').write_text(json.dumps(validation,indent=2)+'\n');bpy.ops.wm.save_as_mainfile(filepath=str(p/'rise_land_loop.blend'))
scene.render.filepath=str(p/'loop.png');bpy.ops.render.render(write_still=True)
scene.render.filepath=str(p/'frames/frame_');bpy.ops.render.render(animation=True)
subprocess.run(['/usr/bin/ffmpeg','-v','error','-n','-framerate','20','-i',str(p/'frames/frame_%04d.png'),'-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(p/'cycle.mp4')],check=True)
subprocess.run(['/usr/bin/ffmpeg','-v','error','-n','-stream_loop','1','-i',str(p/'cycle.mp4'),'-c','copy','-movflags','+faststart',str(p/'loop_two_cycles.mp4')],check=True)
print('LOOP_BUILT',json.dumps(validation))
