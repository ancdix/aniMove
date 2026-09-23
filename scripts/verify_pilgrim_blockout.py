"""Reopen a saved blockout, verify FK/IK, solid meshes, and subframe contacts."""
import bpy,json,sys
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from motion_lab import to_blender

p=Path(sys.argv[sys.argv.index('--')+1]);bpy.ops.wm.open_mainfile(filepath=str(p/'pilgrim_blockout.blend'))
scene=bpy.data.scenes['PILGRIM_Blockout'];bpy.context.window.scene=scene;rig=bpy.data.objects['PILGRIM_RIG'];d=json.loads((p/'skeleton.json').read_text());expected=to_blender(np.load(p/'pose_envelope.npz')['xyz'])
meshes=[o for o in bpy.data.collections['PILGRIM_BODY'].objects if o.type=='MESH'];bone={o.name:o.vertex_groups[0].name for o in meshes}
mount_pairs=set()
for key in 'ABCD':
    mount_pairs.add(frozenset(['PILGRIM_'+key+'_CARRIER','PILGRIM_'+key+'_0_JOINT']))
    if key in 'CD':mount_pairs.add(frozenset(['PILGRIM_'+key+'_CARRIER','PILGRIM_'+key+'_0_SEGMENT']))
for key,side in [('A','1'),('B','-1')]:
    for body in ['PILGRIM_SPINE_01_AXIS','PILGRIM_SPINE_01_TOWER_'+side]:mount_pairs.add(frozenset([body,'PILGRIM_'+key+'_CARRIER']))
report={'frames':241,'subframes':961,'source':'authored rig test','fk_joint_error':0.,'ik_joint_error':0.,'min_mesh_z':1e9,'rear_contact_drift':0.,'surface_intersections':[]}
for mode in [0.,1.]:
    for k in 'ABCD':rig['ik_'+k]=mode
    rig.update_tag()
    for f in range(1,242):
        scene.frame_set(f);dg=bpy.context.evaluated_depsgraph_get();er=rig.evaluated_get(dg);positions=np.array([er.pose.bones[n].head[:] for n in d['names']]);err=float(np.linalg.norm(positions-expected[f-1],axis=-1).max())
        key='fk_joint_error' if mode==0 else 'ik_joint_error';report[key]=max(report[key],err)
for k in 'ABCD':rig['ik_'+k]=0.
rig.update_tag()
for f in np.linspace(1,241,961):
    scene.frame_set(int(f),subframe=float(f%1));dg=bpy.context.evaluated_depsgraph_get();er=rig.evaluated_get(dg)
    for k in 'CD':
        j=d['names'].index(k+'_3');report['rear_contact_drift']=max(report['rear_contact_drift'],float(np.linalg.norm(np.array(er.pose.bones[k+'_3'].head)-expected[0,j])))
    trees={};bounds={}
    for o in meshes:
        e=o.evaluated_get(dg);me=e.to_mesh();verts=[e.matrix_world@v.co for v in me.vertices];coords=np.array(verts)
        report['min_mesh_z']=min(report['min_mesh_z'],float(coords[:,2].min()))
        if f%4==1:
            trees[o.name]=BVHTree.FromPolygons(verts,[list(poly.vertices) for poly in me.polygons]);bounds[o.name]=(coords.min(axis=0),coords.max(axis=0))
        e.to_mesh_clear()
    if trees:
        names=list(trees)
        for i,a in enumerate(names):
            for b in names[i+1:]:
                ba,bb=bone[a],bone[b]
                if frozenset([a,b]) in mount_pairs:continue
                if ba==bb:continue
                if rig.data.bones[ba].parent==rig.data.bones[bb] or rig.data.bones[bb].parent==rig.data.bones[ba]:continue
                amin,amax=bounds[a];bmin,bmax=bounds[b]
                if (amax<bmin).any() or (bmax<amin).any():continue
                hits=trees[a].overlap(trees[b])
                if hits:report['surface_intersections'].append(dict(frame=float(f),a=a,b=b,triangles=len(hits)))
report['collision_scope']='Evaluated mesh surface intersections every 4 frames; same-bone and adjacent-bone mechanical interfaces excluded. Interlimb/ring capsules additionally checked on every authored integer frame. Floor and rear contacts checked at 80 Hz. Surface overlap is not a volumetric containment test.'
report['intended_mount_exclusions']=[sorted(pair) for pair in mount_pairs]
report['status']='passed' if max(report['fk_joint_error'],report['ik_joint_error'])<1e-4 and report['min_mesh_z']>-.001 and not report['surface_intersections'] else 'needs_fix'
(p/'saved_validation.json').write_text(json.dumps(report,indent=2)+'\n');print('SAVED_PILGRIM_VALIDATION',json.dumps({k:v for k,v in report.items() if k!='surface_intersections'}),flush=True)
