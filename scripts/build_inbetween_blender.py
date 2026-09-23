"""Render original + four true inbetweens and a separately corrected upright test."""
import json,sys,subprocess
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_robot_blender import build_rig,material,primitive,relocate,linear_keys

OUT=Path(sys.argv[sys.argv.index('--')+1]);EXTRA=OUT.parent/'inbetween_extra_v1'
COLORS=dict(silver=(.52,.62,.69),dark=(.035,.055,.075),amber=(.96,.41,.06),blue=(.035,.51,.8),green=(.12,.7,.25),floor=(.045,.062,.09),white=(.85,.9,.96),source=(.3,.78,.78),A=(.95,.32,.11),B=(.2,.72,1),C=(.92,.72,.12),D=(.67,.35,.95))
MATS={k:material('EDIT '+k,v) for k,v in COLORS.items()}
REPORT={}

def setup(name,camera_position,target,scale):
    scene=bpy.data.scenes.new(name);bpy.context.window.scene=scene;scene.frame_start=1;scene.frame_end=120;scene.render.fps=20
    cols={}
    for n in ['ROBOT_RIG','IK_TARGETS','DEBUG_CONTACTS','CAMERA_LIGHTS','STAGE','SOURCE']:
        c=bpy.data.collections.new(name+'_'+n);scene.collection.children.link(c);cols[n]=c
    bpy.ops.object.camera_add(location=camera_position);camera=bpy.context.object;relocate(camera,cols['CAMERA_LIGHTS'])
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=scale;scene.camera=camera
    scene.world=bpy.data.worlds.new(name+' World');scene.world.color=(.035,.05,.075)
    scene.render.engine='BLENDER_WORKBENCH';sh=scene.display.shading;sh.light='STUDIO';sh.studio_light='paint.sl';sh.color_type='MATERIAL';sh.show_shadows=False;sh.show_cavity=True;sh.cavity_type='BOTH';sh.background_type='WORLD'
    scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
    scene['experiment_manifest']=str(OUT/'run.json')
    return scene,cols

def text(scene,cols,body,x,y,size,color='white'):
    data=bpy.data.curves.new(body,'FONT');data.body=body;data.size=size
    obj=bpy.data.objects.new(body,data);cols['CAMERA_LIGHTS'].objects.link(obj);obj.parent=scene.camera;obj.location=(x,y,-6);data.materials.append(MATS[color]);return obj

def timeline(scene,cols,left,right,y,extreme=False):
    text(scene,cols,'SOURCE HELD',left,y+.14,.11,'source');text(scene,cols,'ANYTOP GENERATES',left+(right-left)*.29,y+.14,.11,'amber');text(scene,cols,'AUTHORED END' if extreme else 'SOURCE HELD',left+(right-left)*.76,y+.14,.11,'source')
    for a,b,mat in [(0,.25,'source'),(.25,.75,'amber'),(.75,1,'source')]:
        obj=primitive('Timeline segment','cube',(0,0,0),((right-left)*(b-a)/2,.025,.001),MATS[mat],cols['CAMERA_LIGHTS']);obj.modifiers.clear();obj.parent=scene.camera;obj.location=(left+(right-left)*(a+b)/2,y,-6)
    cursor=primitive('Timeline cursor','sphere',(0,0,0),(.045,)*3,MATS['white'],cols['CAMERA_LIGHTS']);cursor.parent=scene.camera
    for frame,x in [(1,left),(120,right)]:cursor.location=(x,y,-5.99);cursor.keyframe_insert('location',frame=frame)
    linear_keys(cursor)

def robot(scene,cols,path,x,y,prefix):
    r=json.loads((path/'retarget.json').read_text());m=np.load(path/'motion.npz');before=set(bpy.data.objects)
    rig,validation=build_rig(prefix,'clean',x,m,r,cols,MATS)
    created=set(bpy.data.objects)-before
    if y:
        parent=bpy.data.objects.new(prefix+'_placement',None);cols['ROBOT_RIG'].objects.link(parent);parent.location.y=y
        for obj in created:obj.parent=parent
    for k in 'ABCD':
        foot=bpy.data.objects[prefix+'_'+k+'_foot'];foot.data.materials.clear();foot.data.materials.append(MATS[k])
    rig['experiment_motion_npz']=str(path/'motion.npz');rig['experiment_record']=str(path/'retarget.json')
    REPORT[prefix]=validation
    return rig,m,r

def source_skeleton(cols,xyz,record,xoffset):
    xyz=xyz+np.array([xoffset,0,0]);endpoint={record['joint_names'].index(v['endpoint']):k for k,v in record['config']['limbs'].items()}
    for j,name in enumerate(record['joint_names']):
        radius=.035 if j in endpoint else .017
        obj=primitive('EDIT_SOURCE_JOINT_'+str(j),'sphere',(0,0,0),(radius,)*3,MATS[endpoint.get(j,'source')],cols['SOURCE']);obj['source_index']=j
        for f,pos in enumerate(xyz[:,j]):obj.location=pos;obj.keyframe_insert('location',frame=f+1)
        linear_keys(obj);parent=record['parents'][j]
        if parent<0:continue
        link=primitive('EDIT_SOURCE_LINK_'+str(j),'cylinder',(0,0,0),(.01,.01,1),MATS['source'],cols['SOURCE']);link.modifiers.clear();link.rotation_mode='QUATERNION';last=None
        for f in range(len(xyz)):
            a,b=xyz[f,parent],xyz[f,j];delta=Vector(b-a);q=delta.to_track_quat('Z','Y')
            if last is not None and q.dot(last)<0:q.negate()
            last=q.copy();link.rotation_quaternion=q;link.location=(a+b)/2;link.scale.z=max(delta.length/2,1e-7)
            for prop in ['location','rotation_quaternion','scale']:link.keyframe_insert(prop,frame=f+1)
        linear_keys(link)

def render(scene,stem):
    bpy.context.window.scene=scene;scene.frame_set(105 if 'Extreme' in scene.name else 60);scene.render.filepath=str(OUT/(stem+'.png'));bpy.ops.render.render(write_still=True)
    folder=OUT/(stem+'_frames');scene.render.filepath=str(folder/'frame_');bpy.ops.render.render(animation=True)
    subprocess.run(['/usr/bin/ffmpeg','-v','error','-n','-framerate','20','-i',str(folder/'frame_%04d.png'),'-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/(stem+'.mp4'))],check=True)

scene,cols=setup('ANYTOP_Inbetween_Variations',(0,-10,9),(0,0,.5),11.7)
text(scene,cols,'ANYTOP / FOUR GENERATED MIDDLES',-5.35,3.18,.27)
text(scene,cols,'Identical boundary features. Different seeds. All robot motion comes from the resulting samples.',-5.35,2.85,.135)
placements=[('ORIGINAL',OUT/'original',-3.6,1.7),('VARIATION 1',OUT/'natural_seed3101',0,1.7),('VARIATION 2',OUT/'natural_seed3102',3.6,1.7),('VARIATION 3',OUT/'natural_seed3103',-1.8,-2),('VARIATION 4',EXTRA/'natural_seed3105',1.8,-2)]
rigs=[]
for i,(label,path,x,y) in enumerate(placements):
    rig,m,r=robot(scene,cols,path,x,y,'EDIT_VARIANT_'+str(i));rigs.append(rig)
    text(scene,cols,label,x-1.0,1.95 if i<3 else -.60,.16,'source' if i==0 else 'blue')
primitive('Variants display stage','cube',(0,0,-.20),(6,4,.04),MATS['floor'],cols['STAGE'])
timeline(scene,cols,-5.2,5.2,-2.92)
for fraction,label in [(0,'0 s'),(.25,'1.5 s'),(.75,'4.5 s'),(1,'6 s')]:text(scene,cols,label,-5.2+10.4*fraction-.06,-3.19,.12)
text(scene,cols,'Raw timing and foot drift retained / source-conditioned motion, not action prompts',-5.2,-3.42,.13)
scene['instructions']='Original and four AnyTop inbetweens. Frames 1-30 and 91-120 fixed in feature space; 31-90 synthesized. Root integration can shift suffix globally. No contact pinning or temporal smoothing on these robots.'
variants_scene=scene
scene,cols=setup('ANYTOP_Extreme_Four_to_Two',(3,-8,4.7),(0,-.1,.75),7.9)
text(scene,cols,'ANYTOP / FOUR SUPPORTS TO TWO',-3.6,2.12,.22)
text(scene,cols,'Source beginning + authored upright ending / diffusion generates the middle',-3.6,1.84,.11)
rig,m,r=robot(scene,cols,OUT/'corrected_rear_up_seed3101',1.65,0,'EDIT_EXTREME_ROBOT')
source_skeleton(cols,m['source_xyz'],r,-1.65)
primitive('Extreme display stage','cube',(0,0,-.04),(4.5,2.5,.04),MATS['floor'],cols['STAGE'])
text(scene,cols,'RAW ANYTOP OUTPUT',-3.5,-1.48,.16,'source');text(scene,cols,'CONTACT-CORRECTED ROBOT',.25,-1.48,.145,'blue')
text(scene,cols,'Boundary snap and foot drift visible',-3.5,-1.60,.105);text(scene,cols,'Rear feet pinned / body repositioned',.25,-1.60,.105)
timeline(scene,cols,-3.5,3.5,-1.91,True)
text(scene,cols,'~75-degree torso / smoothing + IK / body-center support proxy only; no physics simulation',-3.5,-2.26,.094)
scene['instructions']='Stress test, not a validated physical balance. Left raw diffusion; right 3-pass smoothing, rear-foot anchors, released front feet, body-center shift toward support and IK. Upright ending is authored. Raw transition has a boundary snap; corrections are substantial. Not a seamless loop.'
scene['source_offset_x']=-1.65;scene['robot_directory']=str(OUT/'corrected_rear_up_seed3101')
rig['ik_fk']=1.;rig.update_tag()
scene.frame_set(105)
for obj in bpy.context.selected_objects:obj.select_set(False)
rig.select_set(True);bpy.context.view_layer.objects.active=rig
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            s=area.spaces.active;s.region_3d.view_perspective='CAMERA';s.shading.color_type='MATERIAL';s.overlay.show_extras=False;s.overlay.show_bones=False;s.overlay.show_relationship_lines=False;s.overlay.show_cursor=False
bpy.data.texts.new('README_INBETWEEN_EXPERIMENT').write(variants_scene['instructions']+'\n\n'+scene['instructions'])
(OUT/'blender_build_validation.json').write_text(json.dumps(REPORT,indent=2)+'\n')
assert not (OUT/'inbetween_experiments.blend').exists()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'inbetween_experiments.blend'))
render(variants_scene,'variations');render(scene,'extreme')
print('INBETWEEN_BUILT',json.dumps(REPORT))
