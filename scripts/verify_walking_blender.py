"""Validate saved FK/IK playback, dense collision clearance and visible mesh floor."""
import json
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from collision import audit
from motion_lab import slip_speed


def main():
    directory=Path(sys.argv[sys.argv.index('--')+1])
    bpy.ops.wm.open_mainfile(filepath=str(directory/'robot_walk.blend'))
    scene=bpy.data.scenes['WALK_Collision_Checked'];bpy.context.window.scene=scene
    record=json.loads((directory/'retarget.json').read_text());motion=np.load(directory/'motion.npz')
    rig=bpy.data.objects['CLEAN_'+record['source']['id']]
    assert (scene.frame_start,scene.frame_end,scene.render.fps)==(1,record['frames'],record['fps'])
    report={'status':'passed','fps':scene.render.fps,'frames':scene.frame_end}
    for blend in [0.,1.]:
        rig['ik_fk']=blend;rig.update_tag()
        observed=[];length_errors=[]
        for frame in range(record['frames']):
            scene.frame_set(frame+1);bpy.context.view_layer.update()
            pose=[]
            for key in 'ABCD':
                upper=rig.pose.bones['LIMB_'+key+'_0'];lower=rig.pose.bones['LIMB_'+key+'_1']
                pose.append([list(upper.head),list(lower.head),list(lower.tail)])
                length_errors.extend([abs(upper.length-.7),abs(lower.length-.7)])
            observed.append(pose)
        observed=np.array(observed)
        error=float(np.linalg.norm(observed-motion['clean_joints'],axis=-1).max())
        stance=slip_speed(observed[:,:,2],motion['contacts'],record['fps'])
        assert error<1e-4,error
        assert max(length_errors)<1e-5
        assert stance<1e-4,stance
        report['FK' if blend==0 else 'IK']=dict(max_joint_error=error,max_segment_length_error=max(length_errors),stance_slip=stance)
    # Dense samples include the interpolation between keys, not just generated poses.
    rig['ik_fk']=0.;rig.update_tag()
    poses=[];cores=[];rotations=[];headings=[];minimum_mesh_z=float('inf')
    sample_frames=np.arange(1,record['frames']+.001,.25)
    for sample in sample_frames:
        integer=int(np.floor(sample));scene.frame_set(integer,subframe=float(sample-integer));bpy.context.view_layer.update()
        graph=bpy.context.evaluated_depsgraph_get();evaluated=rig.evaluated_get(graph)
        pose=[]
        for key in 'ABCD':
            upper=evaluated.pose.bones['LIMB_'+key+'_0'];lower=evaluated.pose.bones['LIMB_'+key+'_1']
            pose.append([list(upper.head),list(lower.head),list(lower.tail)])
        transform=evaluated.pose.bones['ROOT'].matrix @ evaluated.data.bones['ROOT'].matrix_local.inverted()
        cores.append(list(transform.translation));rotations.append(np.array(transform.to_3x3()));poses.append(pose)
        head=evaluated.pose.bones['HEAD'];headings.append(list((head.tail-head.head).normalized()))
        for obj in rig.users_collection[0].objects:
            if obj.type!='MESH':continue
            mesh=obj.evaluated_get(graph)
            minimum_mesh_z=min(minimum_mesh_z,min((mesh.matrix_world@v.co).z for v in mesh.data.vertices))
    collisions=audit(np.array(poses),np.array(cores),np.array(rotations),np.array(headings))
    assert collisions['margin_violation_count']==0,collisions['worst']
    assert minimum_mesh_z>-1e-4,minimum_mesh_z
    report['dense_samples']=len(sample_frames)
    report['collision_sample_rate']=record['fps']*4
    report['minimum_rendered_mesh_z']=minimum_mesh_z
    report['collision']=collisions
    report['collision']['sample_to_blender_frame']='1 + (sample_index - 1) / 4; report frame fields are one-based dense sample indices'
    # Exercise an editable target without saving the altered pose.
    rig['ik_fk']=1.;rig.update_tag();scene.frame_set(20)
    target=bpy.data.objects['IK_CLEAN_'+record['source']['id']+'_A'];target.location.x+=.03
    bpy.context.view_layer.update()
    edit_error=(rig.pose.bones['LIMB_A_1'].tail-target.location).length
    assert edit_error<1e-3,edit_error
    report['interactive_target_move_error']=edit_error
    (directory/'walk_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('WALK_VALIDATED',json.dumps(report))


if __name__=='__main__':main()
