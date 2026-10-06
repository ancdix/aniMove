"""Check view switching, unchanged motion, rigid mesh bindings and saved overlays."""
import bpy,json
from pathlib import Path
from mathutils import Vector
REPO=Path('/home/ipsedesktop/Documents/GitHub/aniMove')
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate/motion_lab_v001')
ns={'__name__':'motion_lab_review'};exec((REPO/'motion_lab/blender_ui.py').read_text(),ns);ns['register']()
s=bpy.data.scenes[ns['SCENE']];bpy.context.window.scene=s
jobs=json.loads((BASE/'official_v2_target_jobs.json').read_text());records=[]
for key in ['Pilgrim','PilgrimQuad']:
    job=next(j for j in jobs if json.loads((BASE/'jobs'/j/'request.json').read_text())['target']==key)
    ns['load_result'](job,False);rig=s.objects['ML_RIG_'+key];action=rig.animation_data.action
    frames=[1,s.frame_end//2,s.frame_end];before={}
    for f in frames:
        s.frame_set(f);bpy.context.view_layer.update();before[f]=[b.head.copy() for b in rig.pose.bones]
    for mode in ['MODEL','BOTH','SKELETON','MODEL']:
        s.ml_pilgrim_view=mode;assert rig.animation_data.action==action
        collection=bpy.data.collections['ML_MODEL_'+key]
        assert collection.hide_viewport==(mode=='SKELETON') and collection.hide_render==(mode=='SKELETON')
        assert all(o.hide_viewport==(mode=='MODEL') for o in bpy.data.collections['ML_TARGET_'+key].objects if o.name.startswith('ML_LINK_'))
    error=0;motion_error=0
    for f in frames:
        s.frame_set(f);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
        motion_error=max(motion_error,max((b.head-p).length for b,p in zip(rig.pose.bones,before[f])))
        for obj in collection.objects:
            bone=obj['model_bone'];transform=rig.matrix_world@rig.pose.bones[bone].matrix@rig.data.bones[bone].matrix_local.inverted()
            evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh()
            error=max(error,max((evaluated.matrix_world@a.co-transform@b.co).length for a,b in zip(mesh.vertices,obj.data.vertices)))
            evaluated.to_mesh_clear()
    assert error<2e-5 and motion_error<1e-7,(key,error,motion_error)
    assert len(collection.objects)==64 and not any(b.constraints for b in rig.pose.bones)
    records.append(dict(target=key,parts=len(collection.objects),mesh_attachment_error_m=error,motion_change_m=motion_error,frames=frames))
    s.frame_set(20);s.render.resolution_percentage=65;s.render.filepath=str(BASE/(key+'_model_motion.png'));bpy.ops.render.render(write_still=True)
    ns['show_target'](s,key,rest=True);s.render.filepath=str(BASE/(key+'_model_reference.png'));bpy.ops.render.render(write_still=True)
ns['load_result'](next(j for j in jobs if json.loads((BASE/'jobs'/j/'request.json').read_text())['target']=='Pilgrim'),False)
s.ml_pilgrim_view='MODEL';s.render.resolution_percentage=100
text=bpy.data.texts['MOTION_LAB_UI.py'];text.clear();text.write((REPO/'motion_lab/blender_ui.py').read_text())
bpy.data.libraries.write(str(BASE/'motion_lab_overlay_preview.blend'),{s,text,bpy.data.texts['MOTION_LAB_PILGRIM_MODEL.json']}|{a for a in bpy.data.actions if a.name.startswith('ML_')})
report=dict(status='passed',records=records,modes=['Skeleton','Model','Both'],source='Existing blockout_v004 geometry, rigid binding only; no motion cleanup')
(BASE/'pilgrim_overlay_validation.json').write_text(json.dumps(report,indent=2)+'\n');print('OVERLAY_VALIDATED',json.dumps(report))
