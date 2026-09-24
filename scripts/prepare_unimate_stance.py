"""Versioned rest-stance ablation; same topology, lengths, names and scale."""
import copy,json,sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
BASE=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate');sys.path.insert(0,str(BASE/'UniMate'))
from Animation import offsets_from_positions
from Quaternions import Quaternions
from unimate.utils.motion_utils import compute_unimate_motion_feats,recover_unimate_joint_pos_from_rot,recover_unimate_joint_pos_from_ric,compute_rots_from_tpos
out=BASE/'pilgrim_stance_001';out.mkdir(exist_ok=False)
original=np.load(BASE/'pilgrim_labels_001/conditions/front_hind/cond.npy',allow_pickle=True).item();c=original['Pilgrim'];names=list(c['joint_names']);parents=np.asarray(c['parents']);scale=float(c['scale_factor']);rest=np.asarray(c['tpos_first_frame'])/scale;offsets=offsets_from_positions(rest,parents)
quad=rest.copy();root=np.array([0.,.90,0.]);tilt=Rotation.from_euler('x',70,degrees=True).as_matrix();quad[0]=root
# A rigid root/core rotation preserves all branching angles and attachment offsets.
for j in range(1,len(names)):quad[j]=root+tilt@(rest[j]-rest[0])
# Raise the head/neck relative to the tilted torso, using joint rotation only.
neck=names.index('Neck');counter=Rotation.from_euler('x',-50,degrees=True).as_matrix()
for name in ['Head','HeadTip']:
    j=names.index(name);quad[j]=quad[neck]+counter@(quad[j]-quad[neck])
chains=[]
for side,sign in [('Left',1),('Right',-1)]:
    for kind,segments,target in [('front',['UpperArm','Forearm','Hand','Fingers'],[sign*.72,0.,.95]),('hind',['Thigh','Shin','Foot','Toes'],[sign*.58,0.,-.65])]:
        ids=[names.index(side+s) for s in segments];a,b,w,t=ids;lengths=[np.linalg.norm(rest[v]-rest[u]) for u,v in zip(ids[:-1],ids[1:])];tip=np.array(target);last=np.array([0.,-.93,.367]);last=last/np.linalg.norm(last)*lengths[2];wrist=tip-last;delta=wrist-quad[a];distance=np.linalg.norm(delta);axis=delta/distance;L1,L2=lengths[:2];assert abs(L1-L2)<distance<L1+L2
        along=(L1*L1-L2*L2+distance*distance)/(2*distance);radius=np.sqrt(L1*L1-along*along);bend=np.array([sign*.30,0.,1.]);bend-=axis*np.dot(bend,axis);bend/=np.linalg.norm(bend)
        quad[b]=quad[a]+axis*along+radius*bend;quad[w]=wrist;quad[t]=tip;chains.append(ids)
old_len=np.linalg.norm(rest[1:]-rest[parents[1:]],axis=1);new_len=np.linalg.norm(quad[1:]-quad[parents[1:]],axis=1);length_error=float(abs(old_len-new_len).max());assert length_error<1e-10
# At branching joints, dot products verify this is attainable by rigid rotations.
branch_error=0.
for p in range(len(names)):
    kids=np.where(parents==p)[0]
    if len(kids)>1:
        a=rest[kids]-rest[p];b=quad[kids]-quad[p];branch_error=max(branch_error,float(abs(a@a.T-b@b.T).max()))
assert branch_error<1e-10
ends=[names.index(n) for n in ['LeftFingers','RightFingers','LeftToes','RightToes']];assert abs(quad[ends,1]).max()<1e-10 and quad[:,1].min()>=-1e-10
ident=Quaternions.id((90,len(names)));checks=[]
for variant,points in [('upright',rest),('quadruped',quad)]:
    folder=out/'conditions'/variant;(folder/'motions').mkdir(parents=True);d=copy.deepcopy(original);e=d['Pilgrim'];points=points*scale
    if variant=='quadruped':
        e['tpos_first_frame']=points;e['offsets']=offsets_from_positions(points,parents);e['tpos_offsets']=e['offsets'].copy();e['tpos_local_rotations']=Quaternions.id(len(names)).qs;e['tpos_global_rotations']=Quaternions.id(len(names)).qs
    np.save(folder/'cond.npy',d)
    # Static rest clip is loader scaffolding only; it is never supplied as known motion.
    local=np.broadcast_to(e['tpos_local_rotations'][None],(90,len(names),4)).copy();pos=np.broadcast_to(points[None],(90,len(names),3)).copy();facing=Quaternions.id(90);tq=Quaternions(np.broadcast_to(e['tpos_local_rotations'][None],local.shape).copy());rebased=compute_rots_from_tpos(tq,Quaternions(local),parents);features=compute_unimate_motion_feats(pos,rebased,parents,facing);off=offsets_from_positions(points,parents);fk=recover_unimate_joint_pos_from_rot(features,parents,off);ric=recover_unimate_joint_pos_from_ric(features);error=max(float(abs(fk-pos[:-1]).max()),float(abs(ric-pos[:-1]).max()));assert error<1e-6
    filename='Pilgrim-Registration_Only_Not_Generated-000.npz';np.savez_compressed(folder/'motions'/filename,global_positions=pos,local_rotations=local,root_facing_quat=facing.qs,fps=30)
    checks.append(dict(variant=variant,registration_roundtrip_max_error_canonical=error,frames=90))
# Record the authored reference, with unchanged scale and explicit original mapping.
np.savez_compressed(out/'rest_poses.npz',upright_design=rest,quadruped_design=quad,parents=parents,names=names,scale=scale)
validation=json.loads((BASE/'pilgrim_canonical_v002/asset_validation.json').read_text());validation.update(source_geometry='Same Pilgrim topology/lengths and branching angles; authored reference stance only.',rest_pose='Quadrupedal reference: root height .90 design m, torso tilt70deg, neck counter50deg, four analytic two-link placements. Fixed original scale; canonicalization not rerun.',source_geometry_max_error=length_error)
(out/'asset_validation.json').write_text(json.dumps(validation,indent=2)+'\n')
report=dict(status='passed',joints=len(names),max_length_change_design_m=length_error,max_branch_gram_change_m2=branch_error,scale=scale,tip_heights_design_m=quad[ends,1].tolist(),checks=checks,unchanged=['joint identifiers','clean front/hind labels','parents','graph arrays','spectral eigenvectors','scale factor','facing annotation','checkpoint/statistics'],changed=['tpos_first_frame','reference offsets','reference orientation gauge for consistent new bind frames','loader-only registration positions/rotations'],reference_authorship='Static analytical stance, no authored gait or animation constraints. Contact targets define only the reference. Any generated contact behavior must be evaluated independently.',normalization='Preserve original scale instead of renormalizing leaf diameter after posing; segment lengths remain identical in canonical and design units.')
(out/'stance_validation.json').write_text(json.dumps(report,indent=2)+'\n')
fig,axs=plt.subplots(1,2,figsize=(12,5),subplot_kw={'projection':'3d'})
for ax,(variant,x) in zip(axs,[('Upright reference',rest),('Quadrupedal reference',quad)]):
    for j,p in enumerate(parents):
        if p>=0:ax.plot(x[[p,j],0],x[[p,j],2],x[[p,j],1],color='#b38e50',lw=3)
    ax.scatter(x[ends,0],x[ends,2],x[ends,1],c=['cyan','orange','green','purple'],s=40);ax.set_xlim(-1.1,1.1);ax.set_ylim(-1.1,2.2);ax.set_zlim(0,3.1);ax.set_xlabel('X');ax.set_ylabel('Forward Z');ax.set_zlabel('Height Y');ax.set_box_aspect((2.2,3.3,3.1));ax.view_init(elev=15,azim=-55);ax.set_title(variant)
fig.suptitle('Same 23 joints, bone lengths, names and scale · different reference stance');fig.tight_layout();fig.savefig(out/'reference_stances.png',dpi=150);print(json.dumps(report,indent=2))
