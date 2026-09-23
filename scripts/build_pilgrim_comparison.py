"""Direct AnyTop raw XYZ beside the same motion fitted onto the Pilgrim blockout."""
import sys,json
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_pilgrim_blockout import build
from build_robot_blender import primitive,material,relocate,linear_keys
from motion_lab import to_blender,normalize

p=Path(sys.argv[sys.argv.index('--')+1]);block=Path(sys.argv[sys.argv.index('--')+2]);name=sys.argv[sys.argv.index('--')+3]
out=p/'comparison';out.mkdir(exist_ok=False);run=json.loads((p/'run.json').read_text());entry=next(c for c in run['clips'] if c['name']==name)
d=json.loads((block/'skeleton.json').read_text());scale=run['normalized_units_per_design_meter'];raw=to_blender(np.load(p/(name+'.xyz.npy'))/scale);fitted=to_blender(np.load(p/(name+'.fitted.xyz.npy'))/scale)
# Restore the rest floor offset removed by upstream normalization. This is one static coordinate conversion.
raw[:,:,2]+=.06;fitted[:,:,2]+=.06
ix={n:i for i,n in enumerate(d['names'])};poles=[]
for frame in fitted:
    q=[]
    for key in 'ABCD':
        a,b,c=[frame[ix[key+'_'+str(j)]] for j in range(3)];v=normalize(c-a);bend=b-a-v*np.dot(b-a,v);q.append(a+normalize(bend)*.85)
    poles.append(q)
scene=bpy.data.scenes.new('PILGRIM_Direct_AnyTop');bpy.context.window.scene=scene;scene.frame_start=1;scene.frame_end=120;scene.render.fps=20
cols={}
for n in ['BODY','CONTROLS','SOURCE','STAGE']:
    c=bpy.data.collections.new('PILGRIM_DIRECT_'+n);scene.collection.children.link(c);cols[n]=c
rig=build(d,fitted,np.array(poles),cols['BODY'],cols['CONTROLS'],prefix='PILGRIM_DIRECT')
rig.animation_data.action.name='PILGRIM_Direct_AnyTop_bipeds_s5100_Fitted';rig['animation_origin']='AnyTop unconditional custom Pilgrim skeleton; fixed-length BVH reconstruction. No contact cleanup, smoothing, temporal edits or loop construction.'
# Translate the assembled character as a whole through object offsets, including world IK targets.
for obj in cols['BODY'].objects:obj.location.x+=1.8
for obj in cols['CONTROLS'].objects:
    if obj.animation_data and obj.animation_data.action:
        for layer in obj.animation_data.action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        if curve.data_path=='location' and curve.array_index==0:
                            for k in curve.keyframe_points:k.co.y+=1.8;k.handle_left.y+=1.8;k.handle_right.y+=1.8
    else:obj.location.x+=1.8
raw[:,:,0]-=1.8
cyan=material('Raw AnyTop teal',(.12,.67,.66));gold=material('AnyTop effectors',(.92,.59,.16))
for j,n in enumerate(d['names']):
    obj=primitive('PILGRIM_RAW_'+n,'sphere',(0,0,0),(.045,)*3,gold if j in d['contact_joints'] else cyan,cols['SOURCE'])
    for f,pos in enumerate(raw[:,j]):obj.location=pos;obj.keyframe_insert('location',frame=f+1)
    linear_keys(obj);parent=d['parents'][j]
    if parent<0:continue
    link=primitive('PILGRIM_RAW_LINK_'+n,'cylinder',(0,0,0),(.014,.014,1),cyan,cols['SOURCE']);link.modifiers.clear();link.rotation_mode='QUATERNION';last=None
    for f in range(120):
        a,b=raw[f,parent],raw[f,j];v=Vector(b-a);q=v.to_track_quat('Z','Y')
        if last is not None and q.dot(last)<0:q.negate()
        last=q.copy();link.location=(a+b)/2;link.rotation_quaternion=q;link.scale.z=v.length/2
        for prop in ['location','rotation_quaternion','scale']:link.keyframe_insert(prop,frame=f+1)
    linear_keys(link)
floor=material('Direct stage',(.11,.13,.145));primitive('Direct diagnostic stage','cube',(0,0,-.22),(100,100,.04),floor,cols['STAGE'])
bpy.ops.object.camera_add(location=(3,-9,4));cam=bpy.context.object;relocate(cam,cols['STAGE']);cam.rotation_euler=(Vector((0,0,1.35))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=7.5;scene.camera=cam
white=material('Direct label',(.92,.92,.86))
def label(text,x,y,size):
    data=bpy.data.curves.new(text,'FONT');data.body=text;data.size=size;ob=bpy.data.objects.new(text,data);cols['STAGE'].objects.link(ob);ob.parent=cam;ob.location=(x,y,-6);data.materials.append(white)
label('PILGRIM / DIRECT ANYTOP',-3.45,2.0,.22)
label('Custom skeleton | biped prior | seed 5100 | six seconds',-3.45,1.73,.12)
label('RAW MODEL POSITIONS',-3.2,-1.65,.16);label('FIXED-LENGTH BLOCKOUT',.5,-1.65,.16)
label('No contact cleanup or loop edits. Hound-derived calibration statistics.',-3.45,-1.98,.115)
scene.world=bpy.data.worlds.new('Direct world');scene.world.color=(.11,.13,.145);scene.render.engine='BLENDER_WORKBENCH';s=scene.display.shading;s.light='STUDIO';s.studio_light='paint.sl';s.color_type='MATERIAL';s.show_shadows=False;s.show_cavity=True;s.cavity_type='BOTH';s.background_type='WORLD'
scene.render.resolution_x=1400;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene['instructions']='Direct AnyTop generation on the 23-joint Pilgrim skeleton. Raw XYZ left; fixed-length fitted blockout right. No pose guidance, procedural gait, contact cleanup or loop construction. Hound-generated calibration statistics bias the condition; this is not proof of morphology-only adaptation.'
scene['run_manifest']=str(p/'run.json');scene['clip']=name;scene['fit_rms_design_units']=entry['fit_rms_design_units']
scene.frame_set(1)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.color_type='MATERIAL';area.spaces.active.overlay.show_extras=False;area.spaces.active.overlay.show_bones=False
bpy.data.texts.new('README_PILGRIM_DIRECT').write(scene['instructions']+'\n\n'+json.dumps(entry,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(out/'pilgrim_direct_anytop.blend'))
scene.render.filepath=str(out/'direct_anytop.png');bpy.ops.render.render(write_still=True)
print('DIRECT_COMPARISON_SAVED',str(out),flush=True)
