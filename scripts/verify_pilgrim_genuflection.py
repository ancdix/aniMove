"""Independent saved-file validation of the loop, bake, contacts and live controls."""
import bpy,json,sys,math
from pathlib import Path
import numpy as np
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from motion_lab import to_blender
from pilgrim_controls import snap_ik_to_fk,snap_fk_to_ik,set_contact

p=Path(sys.argv[sys.argv.index('--')+1]);bpy.ops.wm.open_mainfile(filepath=str(p/'pilgrim_genuflection_master.blend'));scene=bpy.data.scenes['PILGRIM_Genuflection_Loop'];bpy.context.window.scene=scene;rig=bpy.data.objects[scene['rig']]
d=json.loads((p/'skeleton.json').read_text());motion=np.load(p/'motion.npz');expected=to_blender(motion['clean']);anchors=to_blender(motion['anchors']);names=d['names'];ix={n:i for i,n in enumerate(names)};prefix=rig.name[:-4];ctrl=rig['control_prefix'];control_action=bpy.data.actions[scene['control_action']];baked_action=bpy.data.actions[scene['baked_action']]
meshes=[o for o in bpy.data.collections['PILGRIM_GENU_CTRL_BODY'].objects if o.type=='MESH'];bones={o.name:o.vertex_groups[0].name for o in meshes}
mounts=set()
for key in 'ABCD':
    mounts.add(frozenset([prefix+'_'+key+'_CARRIER',prefix+'_'+key+'_0_JOINT']))
    if key in 'CD':mounts.add(frozenset([prefix+'_'+key+'_CARRIER',prefix+'_'+key+'_0_SEGMENT']))
for key,side in [('A','1'),('B','-1')]:
    for body in [prefix+'_SPINE_01_AXIS',prefix+'_SPINE_01_TOWER_'+side]:mounts.add(frozenset([body,prefix+'_'+key+'_CARRIER']))
def at(frame):scene.frame_set(math.floor(frame),subframe=frame%1);bpy.context.view_layer.update()
def xyz():
    e=rig.evaluated_get(bpy.context.evaluated_depsgraph_get());return np.array([(rig.matrix_world@e.pose.bones[n].head)[:] for n in names])
def head_q():return (rig.matrix_world@rig.evaluated_get(bpy.context.evaluated_depsgraph_get()).pose.bones['HEAD'].matrix).to_quaternion()
report=dict(control_integer_joint_error=0.,bake_vs_controls_max_error=0.,min_mesh_z=1e9,rear_contact_drift=0.,planted_hand_drift=0.,surface_intersections=[],tested_subframes=961)
controls=[]
for f in np.linspace(1,241,961):
    at(float(f));a=xyz();controls.append(a)
    if f%1==0:report['control_integer_joint_error']=max(report['control_integer_joint_error'],float(np.linalg.norm(a-expected[int(f)-1],axis=-1).max()))
    report['rear_contact_drift']=max(report['rear_contact_drift'],float(np.linalg.norm(a[[ix['C_3'],ix['D_3']]]-expected[0,[ix['C_3'],ix['D_3']]],axis=-1).max()))
    for li,key in enumerate('AB'):
        if float(rig['contact_'+key])>=.999999:report['planted_hand_drift']=max(report['planted_hand_drift'],float(np.linalg.norm(a[ix[key+'_3']]-anchors[li])))
    dg=bpy.context.evaluated_depsgraph_get();trees={};bounds={}
    for o in meshes:
        eo=o.evaluated_get(dg);mesh=eo.to_mesh();verts=[eo.matrix_world@v.co for v in mesh.vertices];co=np.array(verts);report['min_mesh_z']=min(report['min_mesh_z'],float(co[:,2].min()))
        if f%2==1:
            trees[o.name]=BVHTree.FromPolygons(verts,[list(poly.vertices) for poly in mesh.polygons]);bounds[o.name]=(co.min(0),co.max(0))
        eo.to_mesh_clear()
    keys=list(trees)
    for i,a in enumerate(keys):
        for b in keys[i+1:]:
            ba,bb=bones[a],bones[b]
            if ba==bb or frozenset([a,b]) in mounts:continue
            if rig.data.bones[ba].parent==rig.data.bones[bb] or rig.data.bones[bb].parent==rig.data.bones[ba]:continue
            amin,amax=bounds[a];bmin,bmax=bounds[b]
            if (amax<bmin).any() or (bmax<amin).any():continue
            if trees[a].overlap(trees[b]):report['surface_intersections'].append(dict(frame=float(f),a=a,b=b))
at(1);start=xyz();q1=head_q();at(241);end=xyz();q2=head_q();report['seam_position_error']=float(np.linalg.norm(end-start,axis=-1).max());report['seam_head_angle_radians']=float(q1.rotation_difference(q2).angle)
h=.05
at(1+h);right=xyz();at(241-h);left=xyz();report['seam_velocity_mismatch_units_per_second']=float(np.linalg.norm(((right-start)-(end-left))*20/h,axis=-1).max())
rig.animation_data.action=baked_action;rig['use_controls']=0.;rig.update_tag()
for f,reference in zip(np.linspace(1,241,961),controls):
    at(float(f));report['bake_vs_controls_max_error']=max(report['bake_vs_controls_max_error'],float(np.linalg.norm(xyz()-reference,axis=-1).max()))
rig.animation_data.action=control_action;rig['use_controls']=1.;rig.update_tag();at(61)
functional={}
def fresh():
    rig['use_controls']=1.;rig['head_world_lock']=0.;rig['head_look_at']=0.
    for k in 'ABCD':rig['ik_'+k]=1.;rig['contact_'+k]=float(k in 'CD')
    rig.update_tag();at(60);at(61)
fresh();base=xyz();root=bpy.data.objects[ctrl+'_CTRL_ROOT'];root.location+=Vector((.02,0,.015));bpy.context.view_layer.update();changed=xyz()
functional['root_moves_body']=float(np.linalg.norm(changed[ix['ROOT']]-base[ix['ROOT']]))
functional['root_edit_keeps_planted_feet']=float(np.linalg.norm(changed[[ix['C_3'],ix['D_3']]]-base[[ix['C_3'],ix['D_3']]],axis=-1).max());fresh()
base=xyz();palm=bpy.data.objects[ctrl+'_CTRL_PALM_A'];mw=palm.matrix_world.copy();mw.translation.x+=.025;palm.matrix_world=mw;bpy.context.view_layer.update();functional['free_hand_target_error']=float(np.linalg.norm(xyz()[ix['A_3']]-(base[ix['A_3']]+[.025,0,0])));fresh()
base=xyz();distal=bpy.data.objects[ctrl+'_CTRL_DISTAL_C'];saved=distal.rotation_quaternion.copy();distal.rotation_quaternion=saved@Quaternion((1,0,0),.10);bpy.context.view_layer.update();changed=xyz()
functional['distal_rotates_wrist']=float(np.linalg.norm(changed[ix['C_2']]-base[ix['C_2']]));functional['distal_edit_keeps_contact']=float(np.linalg.norm(changed[ix['C_3']]-base[ix['C_3']]));distal.rotation_quaternion=saved;fresh()
base=xyz();anchor=bpy.data.objects[ctrl+'_CONTACT_ANCHOR_C'];saved=anchor.matrix_world.copy();anchor.location.x+=.025;bpy.context.view_layer.update();functional['anchor_target_error']=float(np.linalg.norm(xyz()[ix['C_3']]-(base[ix['C_3']]+[.025,0,0])));anchor.matrix_world=saved;fresh()
base=xyz();set_contact(rig,'C',False);released=xyz();set_contact(rig,'C',True);functional['contact_release_plant_pop']=float(max(np.linalg.norm(released-base,axis=-1).max(),np.linalg.norm(xyz()-base,axis=-1).max()));fresh()
rig['head_world_lock']=1.;rig.update_tag();at(31);qa=head_q();at(81);qb=head_q();functional['head_world_lock_angle_radians']=float(qa.rotation_difference(qb).angle);fresh()
rig['head_look_at']=1.;rig.update_tag();target=bpy.data.objects[ctrl+'_CTRL_LOOK_TARGET'];saved=target.location.copy();bpy.context.view_layer.update();qa=head_q();target.location.x+=1.;bpy.context.view_layer.update();qb=head_q();functional['look_target_response_radians']=float(qa.rotation_difference(qb).angle);target.location=saved;fresh()
edited_palm=bpy.data.objects[ctrl+'_CTRL_PALM_A'];edit_matrix=edited_palm.matrix_world.copy();edit_matrix.translation+=Vector((.035,-.02,.025));edited_palm.matrix_world=edit_matrix;bpy.context.view_layer.update()
base=xyz();snap_fk_to_ik(rig,'A');fk=xyz();snap_ik_to_fk(rig,'A');ik=xyz();functional['ik_fk_snap_pop']=float(max(np.linalg.norm(fk-base,axis=-1).max(),np.linalg.norm(ik-base,axis=-1).max()));functional['snap_test']='Edited A hand by (0.035,-0.02,0.025) before IK -> FK -> IK matching';fresh()
report['controls']=functional;report['mesh_collision_scope']='Evaluated surfaces every two frames, known carrier interfaces plus same/adjacent-bone interfaces excluded; no volumetric containment or dynamics claim.';report['mount_exclusions']=[sorted(s) for s in mounts]
checks=dict(joint_match=report['control_integer_joint_error']<1e-4,baked_match=report['bake_vs_controls_max_error']<1e-4,ground=report['min_mesh_z']>-.001,contacts=max(report['rear_contact_drift'],report['planted_hand_drift'])<1e-4,seam=report['seam_position_error']<1e-4,seam_velocity=report['seam_velocity_mismatch_units_per_second']<.02,collision=not report['surface_intersections'],root_response=functional['root_moves_body']>.01,root_contacts=functional['root_edit_keeps_planted_feet']<1e-4,hand_response=functional['free_hand_target_error']<1e-4,distal_response=functional['distal_rotates_wrist']>.005,distal_contact=functional['distal_edit_keeps_contact']<1e-4,anchor_response=functional['anchor_target_error']<1e-4,contact_switch=functional['contact_release_plant_pop']<1e-4,head_lock=functional['head_world_lock_angle_radians']<.001,head_aim=functional['look_target_response_radians']>.05,snap=functional['ik_fk_snap_pop']<1e-4)
report['checks']=checks;report['status']='passed' if all(checks.values()) else 'needs_fix';(p/'saved_validation.json').write_text(json.dumps(report,indent=2)+'\n');print('GENUFLECTION_VALIDATION',json.dumps({k:v for k,v in report.items() if k not in ['surface_intersections','mount_exclusions']}),flush=True)
if report['surface_intersections']:print('COLLISION_PAIRS',sorted(set((x['a'],x['b']) for x in report['surface_intersections'])),flush=True)
