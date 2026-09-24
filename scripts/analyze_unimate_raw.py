"""Decode and measure raw stock UniMate samples; never alter generated motion."""
import argparse,json,sys
from pathlib import Path
import numpy as np

ROOT=Path('/media/ipsedesktop/ShareDrive1/ModelData/aniMove/unimate')
sys.path.insert(0,str(ROOT/'UniMate'))
from unimate.utils.motion_utils import recover_unimate_joint_pos_from_rot,recover_unimate_anim_from_rot
from Animation import offsets_from_positions,rotations_global

def decode(features,cond):
    # Generated rotations are T-pose-relative. The stock data loader derives
    # world-axis T-pose offsets, not the exported rig's bone-local offsets.
    offsets=offsets_from_positions(np.asarray(cond['tpos_first_frame']),np.asarray(cond['parents']))
    return recover_unimate_joint_pos_from_rot(features,np.asarray(cond['parents']),offsets)

def intervals(mask,minimum=3):
    edges=np.flatnonzero(np.diff(np.r_[False,mask,False].astype(int)))
    return [[int(a),int(b)] for a,b in edges.reshape(-1,2) if b-a>=minimum]

def measure(x,cond,fps=30):
    names=list(cond['clean_joint_names']);parents=np.asarray(cond['parents']);rest=np.asarray(cond['tpos_first_frame'])
    head=next((i for i,n in enumerate(names) if n.lower()=='head'),None)
    neck=next((i for i,n in enumerate(names) if n.lower()=='neck'),None)
    tips={n:i for i,n in enumerate(names) if n.lower() in ['left foot','right foot','left hand','right hand']}
    if cond.get('object_type')=='Pilgrim':
        raw_names=list(cond['joint_names'])
        tips={label:raw_names.index(name) for label,name in [('A','LeftFingers'),('B','RightFingers'),('C','LeftToes'),('D','RightToes')]}
    vel=np.gradient(x,1/fps,axis=0);acc=np.gradient(vel,1/fps,axis=0)
    r=dict(frames=len(x),fps=fps,joints=len(names),finite=bool(np.isfinite(x).all()),units='canonical units; target rest leaf-to-leaf diameter 2',root_displacement=float(np.linalg.norm((x[-1,0]-x[0,0])[[0,2]])),root_height_change=float(x[-1,0,1]-x[0,0,1]),root_height_range=float(np.ptp(x[:,0,1])),min_joint_height=float(x[:,:,1].min()),below_ground_fraction=float((x[:,:,1]<-.02).mean()),joint_speed_p95=float(np.percentile(np.linalg.norm(vel,axis=-1),95)),joint_acceleration_p95=float(np.percentile(np.linalg.norm(acc,axis=-1),95)),effectors={})
    if head is not None:
        h=x[:,head]-x[:,0];r.update(head_height_change=float(x[-1,head,1]-x[0,head,1]),head_relative_height_mean=float(h[:,1].mean()),head_relative_height_change=float(h[-1,1]-h[0,1]))
    if neck is not None:
        v=x[:,neck]-x[:,0];pitch=np.degrees(np.arctan2(v[:,1],np.linalg.norm(v[:,[0,2]],axis=-1)))
        r['torso_elevation_range_degrees']=float(np.ptp(pitch));r['torso_elevation_mean_degrees']=float(pitch.mean())
    for name,i in tips.items():
        rel=x[:,i]-x[:,0];speed=np.linalg.norm(vel[:,i],axis=-1);co=(abs(x[:,i,1])<.03)&(speed<.15)
        runs=intervals(co)
        r['effectors'][name]=dict(height_range=float(np.ptp(x[:,i,1])),relative_motion_rms=float(np.sqrt(np.mean(np.sum((rel-rel.mean(0))**2,axis=-1)))),contact_candidates=runs,candidate_drift=[float(np.linalg.norm(x[a:b,i]-x[a,i],axis=-1).max()) for a,b in runs])
    expected=np.linalg.norm(rest[1:]-rest[parents[1:]],axis=-1)
    actual=np.linalg.norm(x[:,1:]-x[:,parents[1:]],axis=-1)
    r['max_fixed_length_error']=float(abs(actual-expected).max())
    return r

def main():
    a=argparse.ArgumentParser();a.add_argument('run',type=Path);a.add_argument('--cond',type=Path,default=ROOT/'known/features/cond.npy');args=a.parse_args()
    manifest=json.loads((args.run/'run.json').read_text());conditions=np.load(args.cond,allow_pickle=True).item();records=[]
    for run in manifest['runs']:
        folder=Path(run['path']);files=list((folder/'samples/motions').glob('*.npy'));assert len(files)==1,folder
        feature=np.load(files[0]);cond=conditions[manifest['object']]
        assert feature.shape==(manifest.get('frames',60),len(cond['parents']),12) and np.isfinite(feature).all()
        x=decode(feature,cond)
        np.save(folder/'raw_fk.xyz.npy',x)
        offsets=offsets_from_positions(np.asarray(cond['tpos_first_frame']),np.asarray(cond['parents']))
        anim=recover_unimate_anim_from_rot(feature,np.asarray(cond['parents']),offsets)
        q=rotations_global(anim).qs;vel=np.gradient(x,1/30,axis=0)
        np.savez_compressed(folder/'raw_kinematics.npz',positions=x,global_quaternions_wxyz=q,velocity=vel,acceleration=np.gradient(vel,1/30,axis=0),parents=cond['parents'],names=cond['joint_names'],fps=30)
        records.append(dict(label=run['label'],prompt=run['prompt'],seed=run['seed'],path=str(files[0]),fk=str(folder/'raw_fk.xyz.npy'),metrics=measure(x,cond)))
    result=dict(status='measured_requires_visual_review',postprocessing='none; stock feature-to-FK decoding only',contact_note='Unfiltered joint height/speed candidates: abs Y < .03 canonical units, speed < .15 units/s, at least 3 frames; no load or physical balance claim.',records=records)
    (args.run/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
