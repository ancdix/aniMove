"""Build a single collision-clean walking robot with a tracking inspection camera."""
import json
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_robot_blender import build_rig, material, primitive, relocate, linear_keys


def main():
    directory=Path(sys.argv[sys.argv.index('--')+1])
    destination=directory/'robot_walk.blend'
    assert not destination.exists() or '--replace' in sys.argv
    record=json.loads((directory/'retarget.json').read_text())
    motion=np.load(directory/'motion.npz')
    scene=bpy.data.scenes.new('WALK_Collision_Checked')
    bpy.context.window.scene=scene
    scene.frame_start,scene.frame_end=1,record['frames']
    scene.render.fps,scene.render.fps_base=record['fps'],1
    collections={}
    for name in ['ROBOT_RIG','IK_TARGETS','DEBUG_CONTACTS','CAMERA_LIGHTS','STAGE']:
        coll=bpy.data.collections.new(name);scene.collection.children.link(coll);collections[name]=coll
    colors=dict(silver=(.43,.54,.65),dark=(.028,.045,.065),amber=(.95,.38,.06),blue=(.025,.47,.72),green=(.08,.67,.25),floor=(.075,.10,.14),line=(.17,.22,.28),white=(.75,.88,.95))
    mats={name:material(name,color,.6 if name in ['silver','dark'] else .15) for name,color in colors.items()}
    rig,validation=build_rig('CLEAN_'+record['source']['id'],'clean',0,motion,record,collections,mats)
    for key,limb in record['config']['limbs'].items():
        hip=np.array(limb['hip'])
        center=hip.copy();center[0]=np.sign(hip[0])*.30
        primitive('Hip_mount_'+key,'cylinder',center,(.047,.047,.05),mats['silver'],collections['ROBOT_RIG'],rig,'CORE',Vector((1,0,0)).to_track_quat('Z','Y'))
    primitive('Walk_floor','cube',(0,-2,-.045),(3.5,6,.045),mats['floor'],collections['STAGE'])
    for y in np.arange(-8,4,.4):
        primitive('Travel_grid','cube',(0,float(y),.0004),(3.4,.007,.0003),mats['line'],collections['STAGE'])
    for x in [-1.3,1.3]:
        primitive('Lane_guide','cube',(x,-2,.0005),(.008,5.8,.0003),mats['line'],collections['STAGE'])
    bpy.ops.object.camera_add(location=(3.7,-4.5,3.05))
    camera=bpy.context.object;relocate(camera,collections['CAMERA_LIGHTS'])
    camera.rotation_euler=(Vector((0,0,.62))-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO';camera.data.ortho_scale=4.7;scene.camera=camera
    initial=camera.location.copy()
    for frame in [1,record['frames']]:
        camera.location=initial+Vector((0,float(motion['clean_core'][frame-1,1]),0))
        camera.keyframe_insert('location',frame=frame)
    linear_keys(camera)
    def label(body,x,y,size,color):
        mat=material('Label '+body,color)
        mat.node_tree.nodes.clear()
        emission=mat.node_tree.nodes.new('ShaderNodeEmission');emission.inputs['Color'].default_value=(*color,1)
        output=mat.node_tree.nodes.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(emission.outputs[0],output.inputs['Surface'])
        data=bpy.data.curves.new(body,'FONT');data.body=body;data.size=size
        obj=bpy.data.objects.new(body,data);collections['CAMERA_LIGHTS'].objects.link(obj)
        obj.parent=camera;obj.location=(x,y,-4);obj.data.materials.append(mat);obj.visible_shadow=False
    label('TETRAPOD / WALK',-2.14,1.08,.16,(.78,.90,.97))
    label('Collision-aware IK   /   planted stance feet',-2.14,.88,.082,(.18,.65,.82))
    label('Four-beat steps + AnyTop torso/head detail',-2.14,-1.05,.079,(.72,.82,.90))
    label('8 seconds   |   30 fps   |   3.03 units forward',-2.14,-1.18,.067,(.57,.68,.78))
    for name,pos,energy,size in [('Key',(1,-2,6),1300,5),('Fill',(-4,-2,3),900,4),('Rim',(1,3,5),1700,4)]:
        data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size
        obj=bpy.data.objects.new(name,data);collections['CAMERA_LIGHTS'].objects.link(obj)
        obj.location=pos;obj.rotation_euler=(Vector((0,-1,.5))-obj.location).to_track_quat('-Z','Y').to_euler()
    scene.world=bpy.data.worlds.new('Walking lab world');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.06,.085,.13,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.4
    scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage=1280,720,100
    scene.render.image_settings.file_format='PNG';scene.render.filepath=str(directory/'walking.png')
    scene.frame_set(60)
    for obj in bpy.context.selected_objects:obj.select_set(False)
    rig.select_set(True);bpy.context.view_layer.objects.active=rig
    scene['experiment_manifest']=str(directory/'retarget.json')
    scene['instructions']='Space to play. Four-beat procedural foot placements with bounded AnyTop body detail. ik_fk=0 baked action; ik_fk=1 editable IK. Collision checks validate saved motion, not arbitrary later edits. The forward-travelling clip resets its position on replay.'
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active;space.region_3d.view_perspective='CAMERA';space.shading.color_type='MATERIAL'
                space.overlay.show_extras=False;space.overlay.show_bones=False;space.overlay.show_relationship_lines=False;space.overlay.show_cursor=False
    info=bpy.data.texts.new('README_WALK');info.write(scene['instructions']+'\n\n'+json.dumps(record,indent=2))
    (directory/'blender_validation.json').write_text(json.dumps(dict(status='passed',rig=validation),indent=2)+'\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(destination))
    bpy.ops.render.render(write_still=True)
    print('WALK_BUILT',json.dumps(validation))


if __name__=='__main__':main()
