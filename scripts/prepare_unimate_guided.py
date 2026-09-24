"""Author three static support poses; disclose every supplied feature channel."""
import json,shutil
from pathlib import Path
import numpy as np
from analyze_unimate_raw import decode,ROOT,offsets_from_positions
from Quaternions import Quaternions
from unimate.utils.motion_utils import compute_unimate_motion_feats
out=ROOT/'pilgrim_guided_001';out.mkdir(exist_ok=False)
shutil.copytree(ROOT/'pilgrim_stance_001/conditions/quadruped',out/'condition')
shutil.copy2(ROOT/'pilgrim_stance_001/asset_validation.json',out/'asset_validation.json')
c=np.load(out/'condition/cond.npy',allow_pickle=True).item()['Pilgrim'];names=list(c['joint_names']);parents=np.asarray(c['parents']);scale=c['scale_factor'];rest=np.asarray(c['tpos_first_frame'])/scale;off=offsets_from_positions(rest,parents)
poses=[]
for phase in [1,-1,1]:
    x=rest.copy()
    for side,sign in [('Left',1),('Right',-1)]:
        for kind,segments in [('front',['UpperArm','Forearm','Hand','Fingers']),('hind',['Thigh','Shin','Foot','Toes'])]:
            a,b,w,t=[names.index(side+v) for v in segments];tip=rest[t].copy();tip[2]+=.10*phase*sign*(1 if kind=='front' else -1);last=rest[t]-rest[w];wrist=tip-last;d=wrist-x[a];length=np.linalg.norm(d);axis=d/length;L1=np.linalg.norm(rest[b]-rest[a]);L2=np.linalg.norm(rest[w]-rest[b]);assert abs(L1-L2)<length<L1+L2
            along=(L1*L1-L2*L2+length*length)/(2*length);radius=np.sqrt(L1*L1-along*along);bend=rest[b]-rest[a];bend-=axis*np.dot(bend,axis);bend/=np.linalg.norm(bend);x[b]=x[a]+axis*along+radius*bend;x[w]=wrist;x[t]=tip
    poses.append(x)
# Only these 3 poses enter the mask; no intermediate gait is authored.
# The filler holds one pose. Its non-root velocity channels are NEVER constrained.
positions=np.repeat(poses[0][None],61,axis=0)
for f,p in zip([0,29,59],poses):positions[f]=p
positions[:,:,2]+=np.arange(61)[:,None]*(.6/59)
local=Quaternions.id((61,len(names)))
for f in range(61):
    globalq=Quaternions.id(len(names))
    for j in range(len(names)):
        kids=np.flatnonzero(parents==j)
        if len(kids)==1:
            k=kids[0];globalq[j]=Quaternions.between(off[k][None],(positions[f,k]-positions[f,j])[None])[0]
        elif len(kids)>1:
            assert np.max(abs((positions[f,kids]-positions[f,j])-off[kids]))<1e-9
        local[f,j]=globalq[j] if parents[j]<0 else -globalq[parents[j]]*globalq[j]
features=compute_unimate_motion_feats(positions*scale,local,parents,Quaternions.id(61));x=decode(features,c)/scale;assert np.max(abs(x-positions[:-1]))<1e-6
np.save(out/'authored_features.npy',features)
np.savez_compressed(out/'authored_poses.npz',poses=np.array(poses),frames=[0,29,59],parents=parents,names=names)
mask=np.zeros((60,23,12),bool);mask[[0,29,59],:,:9]=True
masks={'euler_free':np.zeros_like(mask),'poses':mask.copy(),'poses_root':mask.copy()};masks['poses_root'][:,0,:]=True
for mode,m in masks.items():np.save(out/(mode+'_mask.npy'),m)
report=dict(status='passed',authorship='Three analytic four-tip support poses with opposite diagonal fore/aft offsets of 0.10m; root moves 0.60m in the optional root-guided mode. No in-between pose or non-root velocity channel is supplied.',frames_zero_based=[0,29,59],pose_channels='RIFKE positions and 6D rotations only',optional_root_channels='All 12 root channels at every frame: height, facing, integrated forward velocity',active_feature_fraction={k:float(v.mean()) for k,v in masks.items()},roundtrip_max_error_design_m=float(np.max(abs(x-positions[:-1]))),note='Sparse root slots do not pin global XZ endpoints; those depend on integrated velocities. Root-guided mode explicitly authors travel, which cannot count as generated adherence.')
(out/'guide_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
