"""Add a clean asset-view scene without modifying the verified rig or Actions."""
import bpy,sys,json,hashlib
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_robot_blender import material,primitive,relocate
p=Path(sys.argv[sys.argv.index('--')+1]);assert json.loads((p/'saved_validation.json').read_text())['status']=='passed';out=p/'pilgrim_devotional_master.blend';assert not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(p/'pilgrim_devotional.blend'));comparison=bpy.data.scenes['PILGRIM_Devotional_Loop']
rig=bpy.data.objects[comparison['rig']]
def signature():
    entries=[]
    for name in [comparison['control_action'],comparison['baked_action']]:
        action=bpy.data.actions[name]
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:entries.append((name,fc.data_path,fc.array_index,[(list(k.co),list(k.handle_left),list(k.handle_right)) for k in fc.keyframe_points]))
    return hashlib.sha256(json.dumps(entries).encode()).hexdigest()
before=signature();scene=bpy.data.scenes.new('PILGRIM_Devotional_Hold');bpy.context.window.scene=scene;scene.frame_start=1;scene.frame_end=120;scene.render.fps=20
for name in ['PILGRIM_SETTLE_BODY','PILGRIM_SETTLE_CONTROLS']:scene.collection.children.link(bpy.data.collections[name])
stage=bpy.data.collections.new('PILGRIM_HOLD_STAGE');scene.collection.children.link(stage);floor=material('Pilgrim hold stage',(.12,.135,.15));primitive('Pilgrim hold floor','cube',(0,0,-.045),(100,100,.045),floor,stage)
bpy.ops.object.camera_add(location=(4,-7,3.3));cam=bpy.context.object;relocate(cam,stage);cam.rotation_euler=(Vector((0,0,1.45))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=3.9;scene.camera=cam
scene.world=bpy.data.worlds.new('Pilgrim hold world');scene.world.color=(.12,.135,.15);scene.render.engine='BLENDER_WORKBENCH';sh=scene.display.shading;sh.light='STUDIO';sh.studio_light='paint.sl';sh.color_type='MATERIAL';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.background_type='WORLD'
scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene['instructions']='Devotional Hold: six-second AnyTop-derived settling loop. Contact, clearance and seam edits are documented. Same editable rig and FK bake as PILGRIM_Devotional_Loop comparison scene. Assets remain blockout geometry.'
for k in ['rig','control_action','baked_action','closing_key','asset_directory']:scene[k]=comparison[k]
scene.frame_set(1)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            s=area.spaces.active;s.region_3d.view_perspective='CAMERA';s.shading.color_type='MATERIAL';s.overlay.show_extras=False;s.overlay.show_bones=False
assert before==signature();bpy.ops.wm.save_as_mainfile(filepath=str(out))
# Reopen the packaged file to verify the stored Actions and both scene references.
bpy.ops.wm.open_mainfile(filepath=str(out));comparison=bpy.data.scenes['PILGRIM_Devotional_Loop'];assert before==signature();assert bpy.data.scenes['PILGRIM_Devotional_Hold'].objects[comparison['rig']]==bpy.data.scenes['PILGRIM_Devotional_Loop'].objects[comparison['rig']]
report=dict(status='passed',action_signature=before,unchanged_actions=[comparison['control_action'],comparison['baked_action']],shared_rig= comparison['rig'],scenes=['PILGRIM_Devotional_Hold','PILGRIM_Devotional_Loop'])
(p/'package_validation.json').write_text(json.dumps(report,indent=2)+'\n');scene=bpy.data.scenes['PILGRIM_Devotional_Hold'];bpy.context.window.scene=scene;scene.frame_set(1);scene.render.filepath=str(p/'devotional_hold.png');bpy.ops.render.render(write_still=True)
print('PACKAGED_PILGRIM',json.dumps(report),flush=True)
