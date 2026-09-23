"""Contact-aware robot loop; all changes retained separately from raw AnyTop XYZ."""
import argparse,copy,json
from pathlib import Path
import numpy as np
from motion_lab import normalize,to_blender
from retarget_motion import solve
from collision import clean_bend_planes,audit


def cyclic_smooth(values,passes):
    x=np.asarray(values,dtype=float).copy()
    for _ in range(passes):x=(np.roll(x,1,axis=0)+2*x+np.roll(x,-1,axis=0))/4
    return x


def prepare(directory,clip,output,passes=3):
    run=json.loads((directory/'run.json').read_text());names=run['joint_names'];config=json.loads((Path(__file__).resolve().parents[1]/'configs/hound_robot.json').read_text())
    for limb in config['limbs'].values():limb['hip'][0]=np.sign(limb['hip'][0])*.35
    xyz=np.load(directory/(clip+'.xyz.npy'));body=float(np.linalg.norm(xyz[:10,17]-xyz[:10,0],axis=-1).mean());scale=.9/body
    indices=[names.index(l['endpoint']) for l in config['limbs'].values()];ground=float(xyz[:10,indices,1].min())
    origin=np.array([xyz[0,0,0],-xyz[0,0,2],ground]);raw=(to_blender(xyz)-origin)*scale;raw[...,2]+=config['robot']['foot_radius']
    x=cyclic_smooth(raw,passes);core=(x[:,0]+x[:,17])/2;raw_core=core.copy()
    rotations=[]
    for d in x[:,0]-x[:,17]:
        y=normalize(d);a=normalize(np.cross(y,[0,0,1]));z=normalize(np.cross(a,y));rotations.append(np.column_stack((a,y,z)))
    rotations=np.array(rotations);head=names.index(config['head']);nose=names.index(config['nose']);headings=np.array([normalize(v) for v in x[:,nose]-x[:,head]])
    feet=x[:,indices];bends=x[:,[names.index(l['bend']) for l in config['limbs'].values()]]
    targets=feet.copy();anchors=feet[0].copy();anchors[:,2]=config['robot']['foot_radius']
    contacts=np.zeros((len(x),4),bool);contacts[:,2:]=True;targets[:,2:]=anchors[None,2:]
    f=np.arange(len(x));release=np.clip((22-f)/12,0,1);landing=np.clip((f-95)/12,0,1)
    weights=np.maximum(release,landing);weights=weights*weights*(3-2*weights)
    pitch=np.degrees(np.arctan2(-rotations[:,2,1],np.linalg.norm(rotations[:,:2,1],axis=-1)))
    upright=np.clip((pitch-15)/60,0,1);upright=upright*upright*(3-2*upright)
    support=anchors[2:,:2].mean(axis=0);core[:,:2]=(1-upright[:,None])*core[:,:2]+upright[:,None]*support
    # Keep free front targets relative to the torso when correcting its path.
    targets[:,:2]+=(core-raw_core)[:,None]
    targets[:,:2]=weights[:,None,None]*anchors[None,:2]+(1-weights[:,None,None])*targets[:,:2]
    targets[...,2]=np.maximum(targets[...,2],config['robot']['foot_radius']);contacts[:,:2]=weights[:,None]>.999
    first=solve(core,rotations,targets,bends,contacts,config,True)
    targets[:,:2]+=(1-weights[:,None,None])*first['root_correction'][:,None]
    direct=solve(first['core'],rotations,targets,bends,contacts,config,False)
    requested_targets=targets.copy()
    free=~contacts
    targets[free]=direct['joints'][:,:,2][free]
    direct=solve(first['core'],rotations,targets,bends,contacts,config,False)
    clean=clean_bend_planes(direct,targets,rotations,headings,config)
    collision=audit(clean['joints'],clean['core'],rotations,headings,clearance=.01)
    endpoint_error=float(np.linalg.norm(clean['joints'][:,:,2]-targets,axis=-1).max())
    metrics=dict(max_unreachable_free_target_adjustment=float(np.linalg.norm(targets-requested_targets,axis=-1).max()),max_target_error=endpoint_error,collision={k:v for k,v in collision.items() if k!='violations'},max_core_correction=float(np.linalg.norm(clean['core']-raw_core,axis=-1).max()),max_foot_correction=float(np.linalg.norm(targets-feet,axis=-1).max()),max_smoothing_change=float(np.linalg.norm(x-raw,axis=-1).max()),loop_joint_error=float(np.linalg.norm(clean['joints'][-1]-clean['joints'][0],axis=-1).max()),loop_core_error=float(np.linalg.norm(clean['core'][-1]-clean['core'][0])),peak_body_pitch_degrees=float(pitch.max()),max_robot_frame_step=float(np.linalg.norm(np.diff(clean['joints'],axis=0),axis=-1).max()),minimum_front_height_while_upright=float(clean['joints'][48:59,:2,2,2].min()))
    arrays=dict(source_xyz=raw,smoothed_xyz=x,raw_core=raw_core,rotation=rotations,head_direction=headings,raw_targets=feet,requested_targets=requested_targets,clean_targets=targets,contacts=contacts,front_pin_weights=weights)
    for prefix,result in [('retarget',direct),('clean',clean)]:arrays.update({prefix+'_'+k:v for k,v in result.items()})
    output.mkdir(exist_ok=False);np.savez_compressed(output/'motion.npz',**arrays)
    record=dict(source=dict(id=clip,source=str(directory/(clip+'.xyz.npy'))),config=config,fps=20,frames=120,units='robot design units; body length 0.9',joint_names=names,parents=run['parents'],source_to_robot_scale=scale,source_origin=origin.tolist(),metrics=metrics,filtering=dict(cyclic_binomial_passes=passes),corrections='Rear feet pinned throughout; front feet release over frames 11-23 and pin over 96-108; body center shifts over rear support as pitch rises; IK bends outward. Unreachable free end-effectors are projected to the reachable shell, with adjustment measured separately. These are authored corrections, not evidence of learned landing physics.',loop='Rest-to-rest; first and last windows are authored identical stationary poses.',raw_run=str(directory/'run.json'))
    (output/'retarget.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(metrics,indent=2),flush=True)
    return metrics

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('--clip',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--passes',type=int,default=3);a=p.parse_args();prepare(a.directory,a.clip,a.output,a.passes)
