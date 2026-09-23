"""Reopen the experiment; verify source correspondence, IK and dense collision checks."""
import json,sys
from pathlib import Path
import bpy
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from collision import audit
from motion_lab import slip_speed
p=Path(sys.argv[sys.argv.index('--')+1]);bpy.ops.wm.open_mainfile(filepath=str(p/'inbetween_experiments.blend'))
report=json.loads((p/'saved_animation_validation.json').read_text()) if '--extreme-only' in sys.argv else dict(status='passed',scenes={})
report['status']='passed'
for name in ['ANYTOP_Inbetween_Variations','ANYTOP_Extreme_Four_to_Two']:
    if '--extreme-only' in sys.argv and name!='ANYTOP_Extreme_Four_to_Two':continue
    scene=bpy.data.scenes[name];bpy.context.window.scene=scene;report['scenes'][name]={}
    assert (scene.frame_start,scene.frame_end,scene.render.fps)==(1,120,20)
    for rig in [o for o in scene.objects if o.type=='ARMATURE']:
        m=np.load(rig['experiment_motion_npz']);r=json.loads(Path(rig['experiment_record']).read_text());checks={}
        for blend in [0.,1.]:
            rig['ik_fk']=blend;rig.update_tag();errors=[];target_errors=[];observed=[]
            for f in range(120):
                scene.frame_set(f+1);bpy.context.view_layer.update();pose=[]
                for k in 'ABCD':
                    a=rig.pose.bones['LIMB_'+k+'_0'];b=rig.pose.bones['LIMB_'+k+'_1'];pose.append([list(a.head),list(b.head),list(b.tail)])
                observed.append(pose)
            observed=np.array(observed);error=float(np.linalg.norm(observed-m['clean_joints'],axis=-1).max());assert error<1e-4,(rig.name,error)
            target_error=float(np.linalg.norm(observed[:,:,2]-m['clean_targets'],axis=-1).max());assert target_error<1e-4
            checks['FK' if blend==0 else 'IK']=dict(max_joint_error=error,max_target_error=target_error,stance_slip=slip_speed(observed[:,:,2],m['contacts'],20))
        rig['ik_fk']=1. if r['kind']=='rear_up' else 0.;rig.update_tag();poses=[];cores=[];rotations=[];headings=[];minz=float('inf');rear_positions=[]
        for f in np.arange(1,120.001,.25):
            scene.frame_set(int(f),subframe=float(f-int(f)));bpy.context.view_layer.update();graph=bpy.context.evaluated_depsgraph_get();ev=rig.evaluated_get(graph)
            pose=[[list(ev.pose.bones['LIMB_'+k+'_0'].head),list(ev.pose.bones['LIMB_'+k+'_1'].head),list(ev.pose.bones['LIMB_'+k+'_1'].tail)] for k in 'ABCD'];poses.append(pose);rear_positions.append(np.array(pose)[2:,2])
            transform=ev.pose.bones['ROOT'].matrix@ev.data.bones['ROOT'].matrix_local.inverted();cores.append(list(transform.translation));rotations.append(np.array(transform.to_3x3()))
            h=ev.pose.bones['HEAD'];headings.append(list((h.tail-h.head).normalized()))
            if r['kind']=='rear_up':
                for obj in scene.objects:
                    if obj.type=='MESH' and any(mod.type=='ARMATURE' and mod.object==rig for mod in obj.modifiers):
                        mesh=obj.evaluated_get(graph);minz=min(minz,min((mesh.matrix_world@v.co).z for v in mesh.data.vertices))
        collision=audit(np.array(poses),np.array(cores),np.array(rotations),np.array(headings));checks.update(dense_samples=len(poses),collision=collision)
        if collision['margin_violation_count']:
            report['status']='needs_review'
        if r['kind']=='rear_up':
            checks['dense_playback_mode']='IK';checks['minimum_mesh_z']=minz;checks['dense_rear_foot_drift']=float(np.linalg.norm(np.array(rear_positions)-rear_positions[0],axis=-1).max())
            checks['final_body_center_support_proxy_error']=r['metrics']['end_body_center_support_error'];checks['physical_balance']='Not evaluated; no dynamics or actual mass model.'
            checks['raw_source_max_error']=0.
            for f in range(120):
                scene.frame_set(f+1)
                for obj in scene.objects:
                    if 'source_index' in obj:
                        error=np.linalg.norm(np.array(obj.location)-[scene['source_offset_x'],0,0]-m['source_xyz'][f,obj['source_index']]);checks['raw_source_max_error']=max(checks['raw_source_max_error'],float(error))
            assert checks['raw_source_max_error']<1e-5
            if minz < -1e-4:report['status']='needs_review'
        report['scenes'][name][rig.name]=checks
        print('VERIFIED_RIG',rig.name,json.dumps(checks),flush=True)
(p/'saved_animation_validation.json').write_text(json.dumps(report,indent=2)+'\n');print('FINAL_STATUS',report['status'])
