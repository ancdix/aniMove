"""Pilgrim v1 geometry and authored pose-envelope checks; no learned animation here."""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from motion_lab import two_bone, normalize


def definition():
    nodes = [
        ('ROOT', None, [0, 1.38, 0], 'Pelvis', 0),
        ('SPINE_01', 'ROOT', [0, 1.62, 0], 'Spine', 2),
        ('SPINE_02', 'SPINE_01', [0, 1.88, 0], 'Spine1', 15),
        ('SPINE_03', 'SPINE_02', [0, 2.14, 0], 'Spine2', 17),
        ('NECK', 'SPINE_03', [0, 2.43, 0], 'Neck', 30),
        ('HEAD', 'NECK', [0, 2.76, 0], 'Head', 31),
        ('SENSOR', 'HEAD', [0, 2.96, .10], 'HeadEnd', 32),
    ]
    for key, sign, upper, src in [('A', 1, True, [25,26,27,29]), ('B', -1, True, [19,20,21,23]),
                                  ('C', 1, False, [9,10,12,14]), ('D', -1, False, [3,4,6,8])]:
        pts = [[.43,1.86,.01],[.69,1.20,.06],[.67,.48,.09],[.73,.25,.18]] if upper else [[.27,1.35,-.02],[.43,.79,.28],[.44,.24,-.04],[.44,.06,.03]]
        side = 'Left' if sign > 0 else 'Right'
        model = [side+'Arm',side+'ForeArm',side+'Hand',side+'HandFoot'] if upper else [side+'UpLeg',side+'Leg',side+'Ankle',side+'Foot']
        for j, p in enumerate(pts):
            p[0] *= sign
            nodes.append((key+'_'+str(j), ('SPINE_02' if upper else 'ROOT') if j==0 else key+'_'+str(j-1), p, model[j], src[j]))
    # DFS order is shared by arrays, BVH, conditions, and Blender.
    ordered=[]
    def visit(name):
        n=next(n for n in nodes if n[0]==name);ordered.append(n)
        for child in nodes:
            if child[1]==name:visit(child[0])
    visit('ROOT')
    names=[n[0] for n in ordered];parents=[names.index(n[1]) if n[1] else -1 for n in ordered]
    rest=np.array([n[2] for n in ordered]);offsets=rest.copy()
    for j,p in enumerate(parents):
        if p>=0:offsets[j]-=rest[p]
    return dict(schema=1,name='Pilgrim',units='design meters',up='Y',forward='+Z',fps=20,
                names=names,model_names=[n[3] for n in ordered],parents=parents,rest=rest.tolist(),offsets=offsets.tolist(),
                source_hound_indices=[n[4] for n in ordered],face_joints=[names.index(k) for k in ['D_0','C_0','B_0','A_0']],
                contact_joints=[names.index(k+'_3') for k in 'ABCD'],ring=dict(joint='SPINE_03',radius=.64,tube_radius=.055),
                notes='Three segments per limb. Distal orientation determines wrist; two-link IK solves shoulder-to-wrist. All pose-envelope animation is authored. Model names deliberately carry semantics; Blender labels are neutral.')


def pose(d, lower=0, pitch=0, yaw=0, a=0, b=0):
    rest=np.array(d['rest']);out=rest.copy();ix={n:i for i,n in enumerate(d['names'])}
    root=rest[0]+[0,-lower,-.06*lower]
    # Distributed bend: incrementally orient spine links, then stabilize head direction.
    R=Rotation.from_euler('yx',[yaw,pitch],degrees=True).as_matrix()
    for j in range(len(rest)):
        out[j]=root+R@(rest[j]-rest[0])
    for n,factor in [('SPINE_01',.35),('SPINE_02',.65),('SPINE_03',.9),('NECK',1),('HEAD',.65),('SENSOR',0)]:
        j=ix[n];p=d['parents'][j]
        rr=Rotation.from_euler('yx',[yaw*factor,pitch*factor],degrees=True).as_matrix()
        out[j]=out[p]+rr@(rest[j]-rest[p])
    poles=[];reach=[]
    for key,w in zip('ABCD',[a,b,1,1]):
        js=[ix[key+'_'+str(i)] for i in range(4)];sign=1 if key in 'AC' else -1
        attach=d['parents'][js[0]];out[js[0]]=out[attach]+R@(rest[js[0]]-rest[attach])
        lengths=np.linalg.norm(np.diff(rest[js],axis=0),axis=1)
        distal=normalize(rest[js[3]]-rest[js[2]])*lengths[2]
        if key in 'AB':
            free=out[js[0]]+R@(rest[js[2]]-rest[js[0]])+distal
            free[1]=max(free[1],.38)
            free[0]=sign*max(abs(free[0]),.88)
            free[2]=max(free[2],.5)
            anchor=np.array([sign*.84,.06,.95])
            tip=free*(1-w)+anchor*w
        else:tip=rest[js[3]].copy()
        wrist=tip-distal
        pole=np.array([sign*(1.0 if key in 'AB' else .22),.05,.2 if key in 'AB' else 1.0])
        elbow,actual,bend,err,_=two_bone(out[js[0]],wrist,pole,lengths[0],lengths[1],(2,165))
        out[js[1]]=elbow;out[js[2]]=actual;out[js[3]]=actual+distal
        poles.append(out[js[0]]+bend*.85);reach.append(err)
    return out,np.array(poles),np.array(reach)


def audit(d,xyz):
    from collision import segment_distance
    parents=np.array(d['parents']);rest=np.array(d['rest']);lengths=np.linalg.norm(rest[1:]-rest[parents[1:]],axis=-1)
    got=np.linalg.norm(xyz[:,1:]-xyz[:,parents[1:]],axis=-1)
    # Sample limb centerlines against the oriented ring torus, conservative .075 radius.
    ix={n:i for i,n in enumerate(d['names'])};ring_mins=[]
    for frame in xyz:
        center=frame[ix['SPINE_03']];normal=normalize(frame[ix['NECK']]-center)
        for key in 'ABCD':
            for s in range(3):
                p,q=frame[ix[key+'_'+str(s)]],frame[ix[key+'_'+str(s+1)]]
                v=p[None]+np.linspace(0,1,51)[:,None]*(q-p)[None]-center
                h=v@normal;rad=np.sqrt(np.maximum(0,(v*v).sum(axis=-1)-h*h))
                dist=np.sqrt((rad-d['ring']['radius'])**2+h*h)-d['ring']['tube_radius']-.075
                ring_mins.append(dist.min())
    interlimb=[]
    for frame in xyz:
        for li,a in enumerate('ABCD'):
            for b in 'ABCD'[li+1:]:
                for s in range(3):
                    for t in range(3):
                        interlimb.append(segment_distance(frame[ix[a+'_'+str(s)]],frame[ix[a+'_'+str(s+1)]],frame[ix[b+'_'+str(t)]],frame[ix[b+'_'+str(t+1)]])-.19)
    return dict(max_bone_length_error=float(abs(got-lengths).max()),min_joint_height=float(xyz[...,1].min()),
                min_ring_limb_capsule_clearance=float(min(ring_mins)),ring_limb_intersection_samples=int(sum(v<0 for v in ring_mins)),
                min_interlimb_capsule_clearance=float(min(interlimb)),interlimb_intersection_samples=int(sum(v<0 for v in interlimb)),
                scope='Bone lengths, joint heights, ring vs .075 limb capsule and .095-radius interlimb capsules; palms/torso require evaluated-mesh checks. No physical balance claim.')


def main():
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    d=definition()
    keys=np.array([[0,0,0,0,0],[.2,25,0,0,0],[.45,40,0,1,0],[.55,50,0,1,1],[.55,48,12,1,1],[.25,20,-8,0,0],[0,0,0,0,0]])
    xyz=[];poles=[];errors=[];controls=[]
    for f in range(241):
        interval=min(f//40,5);t=min((f-interval*40)/40,1);t=t*t*(3-2*t)
        params=keys[interval]*(1-t)+keys[interval+1]*t
        x,b,e=pose(d,*params);xyz.append(x);poles.append(b);errors.append(e);controls.append(params)
    xyz=np.array(xyz);report=audit(d,xyz)
    report['max_reach_projection']=float(np.max(errors));report['authored_pose_frames']={n:f for n,f in zip(['Upright','Bow','One hand','Four contacts','Turn','Recover'],[1,41,81,121,161,201])}
    d['pose_checks']=report
    (a.output/'skeleton.json').write_text(json.dumps(d,indent=2)+'\n')
    np.savez_compressed(a.output/'pose_envelope.npz',xyz=xyz,poles=poles,controls=np.array(controls),reach_error=np.array(errors))
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
