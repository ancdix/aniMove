"""Verify saved looping IK/FK, contacts, source visualization, mesh and subframes."""
import json,sys
from pathlib import Path
import bpy
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from collision import audit
from motion_lab import slip_speed
p=Path(sys.argv[sys.argv.index('--')+1]);r=json.loads((p/'retarget.json').read_text());m=np.load(p/'motion.npz')
bpy.ops.wm.open_mainfile(filepath=str(p/'rise_land_loop.blend'));scene=bpy.data.scenes['ANYTOP_Rise_Land_Loop'];bpy.context.window.scene=scene;rig=bpy.data.objects['RISE_LAND_ROBOT']
assert rig['ik_fk']==1.;assert (scene.frame_start,scene.frame_end,scene.render.fps)==(1,120,20)
report=dict(status='passed',frames=120,fps=20,saved_playback='IK',source_max_error=0)
for blend in [0.,1.]:
 rig['ik_fk']=blend;rig.update_tag();poses=[]
 for f in range(120):
  scene.frame_set(f+1);bpy.context.view_layer.update();pose=[]
  for k in 'ABCD':
   u=rig.pose.bones['LIMB_'+k+'_0'];l=rig.pose.bones['LIMB_'+k+'_1'];pose.append([list(u.head),list(l.head),list(l.tail)])
  poses.append(pose)
  if blend==0:
   for o in scene.objects:
    if 'source_index' in o:
     e=np.linalg.norm(np.array(o.location)-[-1.65,0,0]-m['source_xyz'][f,o['source_index']]);report['source_max_error']=max(report['source_max_error'],float(e))
 poses=np.array(poses);err=float(np.linalg.norm(poses-m['clean_joints'],axis=-1).max());assert err<1e-4
 tips=poses[:,:,2];slip=slip_speed(tips,m['contacts'],20);assert slip<1e-4
 result=dict(max_joint_error=err,contact_slip=slip,loop_pose_error=float(np.linalg.norm(poses[-1]-poses[0],axis=-1).max()),loop_velocity_error=float(np.linalg.norm((poses[1]-poses[0])-(poses[-1]-poses[-2]),axis=-1).max()*20))
 assert result['loop_pose_error']<1e-4 and result['loop_velocity_error']<1e-4
 report['FK' if blend==0 else 'IK']=result
assert report['source_max_error']<1e-5
rig['ik_fk']=1.;rig.update_tag();poses=[];cores=[];rots=[];headings=[];rear=[];minz=float('inf')
for f in np.arange(1,120.001,.25):
 scene.frame_set(int(f),subframe=float(f-int(f)));bpy.context.view_layer.update();graph=bpy.context.evaluated_depsgraph_get();ev=rig.evaluated_get(graph)
 pose=[[list(ev.pose.bones['LIMB_'+k+'_0'].head),list(ev.pose.bones['LIMB_'+k+'_1'].head),list(ev.pose.bones['LIMB_'+k+'_1'].tail)] for k in 'ABCD'];poses.append(pose);rear.append(np.array(pose)[2:,2])
 mat=ev.pose.bones['ROOT'].matrix@ev.data.bones['ROOT'].matrix_local.inverted();cores.append(list(mat.translation));rots.append(np.array(mat.to_3x3()));h=ev.pose.bones['HEAD'];headings.append(list((h.tail-h.head).normalized()))
 for o in scene.objects:
  if o.type=='MESH' and any(mod.type=='ARMATURE' and mod.object==rig for mod in o.modifiers):
   mesh=o.evaluated_get(graph);minz=min(minz,min((mesh.matrix_world@v.co).z for v in mesh.data.vertices))
collision=audit(np.array(poses),np.array(cores),np.array(rots),np.array(headings),clearance=.01)
report.update(dense_samples=len(poses),sample_rate=80,collision=collision,minimum_robot_mesh_z=minz,dense_rear_foot_drift=float(np.linalg.norm(np.array(rear)-rear[0],axis=-1).max()))
# Explicitly inspect the seam in repeated playback, including near-boundary samples.
seam=[]
for phase in [119.5,119.75,120,1,1.25,1.5]:
 scene.frame_set(int(phase),subframe=float(phase-int(phase)));bpy.context.view_layer.update();seam.append([[list(rig.pose.bones['LIMB_'+k+'_1'].head),list(rig.pose.bones['LIMB_'+k+'_1'].tail)] for k in 'ABCD'])
report['seam_neighborhood_motion']=float(np.linalg.norm(np.array(seam)-seam[0],axis=-1).max())
if collision['margin_violation_count'] or minz < -1e-4 or report['dense_rear_foot_drift']>1e-4:report['status']='needs_review'
report['interpretation']='These checks verify corrected kinematics and collision clearance. They do not establish physical balance, impact forces or learned landing physics.'
(p/'saved_loop_validation.json').write_text(json.dumps(report,indent=2)+'\n');print('LOOP_VALIDATION',json.dumps(report))
