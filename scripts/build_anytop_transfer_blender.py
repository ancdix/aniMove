"""Build the exact AnyTop XYZ source beside its editable robot transfer."""
import json, sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_robot_blender import build_rig, material, primitive, relocate, linear_keys


def main():
    directory=Path(sys.argv[sys.argv.index('--')+1]);record=json.loads((directory/'retarget.json').read_text());motion=np.load(directory/'motion.npz')
    destination=directory/'anytop_transfer.blend';assert not destination.exists()
    scene=bpy.data.scenes.new('ANYTOP_Source_to_Robot');bpy.context.window.scene=scene
    scene.frame_start,scene.frame_end=1,record['frames'];scene.render.fps=record['fps']
    collections={}
    for name in ['ROBOT_RIG','IK_TARGETS','DEBUG_CONTACTS','CAMERA_LIGHTS','STAGE','ANYTOP_RAW_XYZ']:
        coll=bpy.data.collections.new('TRANSFER_'+name);scene.collection.children.link(coll);collections[name]=coll
    colors=dict(silver=(.52,.62,.69),dark=(.035,.055,.075),amber=(.95,.38,.06),blue=(.035,.51,.8),green=(.12,.65,.25),floor=(.045,.062,.09),white=(.78,.87,.94),source=(.3,.78,.78),A=(.95,.32,.11),B=(.2,.72,1),C=(.92,.72,.12),D=(.67,.35,.95))
    mats={n:material('Transfer '+n,c) for n,c in colors.items()}
    rig,validation=build_rig('ANYTOP_ROBOT_'+record['source']['id'],'clean',1.65,motion,record,collections,mats)
    for key in 'ABCD':
        foot=bpy.data.objects[rig.name+'_'+key+'_foot'];foot.data.materials.clear();foot.data.materials.append(mats[key])
    xyz=motion['source_xyz']+np.array([-1.65,0,0]);source=collections['ANYTOP_RAW_XYZ']
    endpoints={record['joint_names'].index(l['endpoint']):key for key,l in record['config']['limbs'].items()}
    for j,name in enumerate(record['joint_names']):
        mat=mats[endpoints[j]] if j in endpoints else mats['source']
        radius=.04 if j in endpoints else .018
        obj=primitive('SOURCE_JOINT_'+str(j),'sphere',(0,0,0),(radius,)*3,mat,source)
        obj['source_joint_name']=name
        for f,point in enumerate(xyz[:,j]):obj.location=point;obj.keyframe_insert('location',frame=f+1)
        linear_keys(obj)
        parent=record['parents'][j]
        if parent<0:continue
        link=primitive('SOURCE_LINK_'+str(j),'cylinder',(0,0,0),(.011,.011,1),mats['source'],source)
        link.modifiers.clear();link.rotation_mode='QUATERNION';previous=None
        for f in range(record['frames']):
            a,b=xyz[f,parent],xyz[f,j];delta=Vector(b-a)
            link.location=(a+b)/2;link.scale.z=max(delta.length/2,1e-7)
            q=delta.to_track_quat('Z','Y')
            if previous is not None and q.dot(previous)<0:q.negate()
            link.rotation_quaternion=q;previous=q.copy()
            for prop in ['location','rotation_quaternion','scale']:link.keyframe_insert(prop,frame=f+1)
        linear_keys(link)
    # Low display plinth: preserves source foot drift/height without claiming planted contact.
    floor_z=float(min(xyz[...,2].min()-.06,motion['clean_joints'][...,2].min()-.09))
    primitive('Transfer_stage','cube',(0,0,floor_z-.03),(4.5,2.5,.03),mats['floor'],collections['STAGE'])
    bpy.ops.object.camera_add(location=(3,-8,4.0));camera=bpy.context.object;relocate(camera,collections['CAMERA_LIGHTS'])
    camera.rotation_euler=(Vector((0,-.1,.55))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=7.8;scene.camera=camera
    def label(body,x,y,size,color='white'):
        data=bpy.data.curves.new(body,'FONT');data.body=body;data.size=size
        obj=bpy.data.objects.new(body,data);collections['CAMERA_LIGHTS'].objects.link(obj);obj.parent=camera;obj.location=(x,y,-6);obj.data.materials.append(mats[color])
    label('ANYTOP  /  SAME MOTION, DIFFERENT SKELETON',-3.55,1.78,.19)
    label('Hound seed 100 / sample 01   |   120 original samples at 20 fps   |   6 seconds',-3.55,1.51,.105)
    label('ORIGINAL GENERATED XYZ',-3.4,-1.35,.15,'source')
    label('ROBOT TRANSFER',.38,-1.35,.15,'blue')
    label('44 joints / unfiltered',-3.4,-1.56,.10)
    label('Same feet, body timing and head direction',.38,-1.56,.10)
    label('Colored feet correspond. Robot knees bend outward for clearance.',-3.4,-1.85,.105)
    label('Weight shift / source foot drift retained / no procedural gait or contact pinning',-3.4,-2.02,.09)
    scene.world=bpy.data.worlds.new('Transfer world');scene.world.color=(.06,.08,.12)
    scene.render.engine='BLENDER_WORKBENCH';shade=scene.display.shading
    shade.light='STUDIO';shade.studiolight_rotate_z=.4;shade.color_type='MATERIAL';shade.show_shadows=False;shade.show_cavity=True;shade.cavity_type='BOTH';shade.background_type='WORLD'
    scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage=1440,810,100
    scene.render.image_settings.file_format='PNG';scene.render.filepath=str(directory/'comparison.png')
    scene['experiment_manifest']=str(directory/'retarget.json');scene['display_floor_z']=floor_z
    scene['instructions']='Actual AnyTop XYZ left; exact endpoint/body/head transfer right. Outward IK knees adapt the robot. No contact pinning or procedural gait. Six-second weight shift; not a seamless loop. Robot ik_fk property: 0 baked, 1 editable targets.'
    info=bpy.data.texts.new('README_ANYTOP_TRANSFER');info.write(scene['instructions']+'\n\n'+json.dumps(record,indent=2))
    scene.frame_set(60)
    for obj in bpy.context.selected_objects:obj.select_set(False)
    rig.select_set(True);bpy.context.view_layer.objects.active=rig
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active;space.region_3d.view_perspective='CAMERA';space.shading.color_type='MATERIAL'
                space.overlay.show_extras=False;space.overlay.show_bones=False;space.overlay.show_relationship_lines=False;space.overlay.show_cursor=False
    (directory/'blender_validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(destination));bpy.ops.render.render(write_still=True)
    scene.render.filepath=str(directory/'frames'/'frame_');bpy.ops.render.render(animation=True)

if __name__=='__main__':main()
