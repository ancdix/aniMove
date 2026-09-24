"""Reopen harvested assets and check actual contacts, geometry, bake and loop seam."""
import bpy,json,sys,math
from pathlib import Path
import numpy as np
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from motion_lab import to_blender
p=Path(sys.argv[sys.argv.index('--')+1]);r=json.loads((p/'motion.json').read_text());m=np.load(p/'motion.npz');d=json.loads((p/'skeleton.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(p/'harvest_master.blend'));scene=bpy.data.scenes['PILGRIM_'+r['title']];bpy.context.window.scene=scene;rig=bpy.data.objects[scene['rig']];prefix=rig.name[:-4];names=d['names'];ix={n:i for i,n in enumerate(names)};expected=to_blender(m['clean']);anchors=to_blender(m['anchor_paths']);contacts=m['contacts'];end=len(expected);fps=r['fps'];times=np.arange(1,end+.0001,fps/80);meshes=[o for o in bpy.data.collections[prefix+'_BODY'].objects if o.type=='MESH'];bones={o.name:o.vertex_groups[0].name for o in meshes};mounts=set()
for k in 'ABCD':
 mounts.add(frozenset([prefix+'_'+k+'_CARRIER',prefix+'_'+k+'_0_JOINT']))
 if k in 'CD':mounts.add(frozenset([prefix+'_'+k+'_CARRIER',prefix+'_'+k+'_0_SEGMENT']))
for k,side in [('A','1'),('B','-1')]:
 for body in [prefix+'_SPINE_01_AXIS',prefix+'_SPINE_01_TOWER_'+side]:mounts.add(frozenset([body,prefix+'_'+k+'_CARRIER']))
def at(f):scene.frame_set(math.floor(f),subframe=f%1);bpy.context.view_layer.update()
def xyz():
 e=rig.evaluated_get(bpy.context.evaluated_depsgraph_get());return np.array([(rig.matrix_world@e.pose.bones[n].head)[:] for n in names])
report=dict(control_integer_error=0.,bake_error=0.,min_mesh_z=1e9,contact_error=0.,mesh_intersections=[],tested_poses=len(times),fps=fps,cyclic=r['cyclic']);captured=[]
for f in times:
 at(float(f));x=xyz();captured.append(x)
 if f%1==0:
  err=np.linalg.norm(x-expected[int(f)-1],axis=-1)
  if err.max()>report['control_integer_error']:report['control_integer_error']=float(err.max());report['joint_worst']=[float(f),names[int(err.argmax())]]
 for li,k in enumerate('ABCD'):
  if rig['contact_'+k]>=.999999:
   idx=min(int(f)-1,len(anchors)-1);error=float(np.linalg.norm(x[ix[k+'_3']]-anchors[idx,li]));
   if error>report['contact_error']:report['contact_error']=error;report['contact_worst']=[float(f),k]
 dg=bpy.context.evaluated_depsgraph_get();trees={};bounds={}
 for o in meshes:
  eo=o.evaluated_get(dg);me=eo.to_mesh();verts=[eo.matrix_world@v.co for v in me.vertices];co=np.array(verts);low=float(co[:,2].min());
  if low<report['min_mesh_z']:report['min_mesh_z']=low;report['ground_worst']=[float(f),o.name]
  if f%1==0:trees[o.name]=BVHTree.FromPolygons(verts,[list(poly.vertices) for poly in me.polygons]);bounds[o.name]=(co.min(0),co.max(0))
  eo.to_mesh_clear()
 keys=list(trees)
 for i,a in enumerate(keys):
  for b in keys[i+1:]:
   ba,bb=bones[a],bones[b]
   if ba==bb or frozenset([a,b]) in mounts or rig.data.bones[ba].parent==rig.data.bones[bb] or rig.data.bones[bb].parent==rig.data.bones[ba]:continue
   amin,amax=bounds[a];bmin,bmax=bounds[b]
   if (amax<bmin).any() or (bmax<amin).any():continue
   if trees[a].overlap(trees[b]):report['mesh_intersections'].append(dict(frame=float(f),a=a,b=b))
if r['cyclic']:
 at(1);start=xyz();at(end);last=xyz();h=.05;at(1+h);right=xyz();at(end-h);left=xyz();report['seam_position']=float(np.linalg.norm(last-start,axis=-1).max());report['seam_velocity']=float(np.linalg.norm(((right-start)-(last-left))*fps/h,axis=-1).max())
control=rig.animation_data.action;rig.animation_data.action=bpy.data.actions[scene['baked_action']];rig['use_controls']=0.;rig.update_tag()
for f,ref in zip(times,captured):
 at(float(f));report['bake_error']=max(report['bake_error'],float(np.linalg.norm(xyz()-ref,axis=-1).max()))
report['scope']='Ground/contact checks at 80 Hz; evaluated mesh surface intersections at every integer frame. Same/adjacent bone interfaces and ten listed carrier mounts excluded. No dynamics or continuous volumetric collision claim.';report['mount_exclusions']=[sorted(s) for s in mounts];checks=dict(joints=report['control_integer_error']<1e-4,bake=report['bake_error']<1e-4,ground=report['min_mesh_z']>-.001,contacts=report['contact_error']<1e-4,collision=not report['mesh_intersections'])
if r['cyclic']:checks.update(seam=report['seam_position']<1e-4,velocity=report['seam_velocity']<.02)
report['checks']=checks;report['status']='passed' if all(checks.values()) else 'needs_fix';(p/'saved_validation.json').write_text(json.dumps(report,indent=2)+'\n');print('HARVEST_VALIDATION',json.dumps({k:v for k,v in report.items() if k not in ['mesh_intersections','mount_exclusions']}),flush=True)
if report['mesh_intersections']:print('PAIRS',sorted(set((x['a'],x['b']) for x in report['mesh_intersections'])),flush=True)
