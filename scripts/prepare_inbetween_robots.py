"""Screen and transfer edits, retaining raw and explicitly contact-corrected arrays."""
import argparse,copy,json
from pathlib import Path
import numpy as np
from motion_lab import normalize,to_blender,smooth,two_bone
from retarget_motion import solve
from collision import audit,clean_bend_planes


def build(xyz,config,reference,extreme):
    names=reference['joint_names'];idx=lambda k:names.index(config[k]);scale=reference['source_to_robot_scale']
    x=(to_blender(xyz)-reference['origin_blender_units'])*scale;x[...,2]+=config['robot']['foot_radius']
    source_xyz=x.copy()
    if extreme:x=smooth(x,passes=3)
    raw_core=(x[:,idx('root')]+x[:,idx('chest')])/2
    rotations=[]
    for backward in x[:,idx('root')]-x[:,idx('chest')]:
        y=normalize(backward);a=normalize(np.cross(y,[0,0,1]));z=normalize(np.cross(a,y));rotations.append(np.column_stack((a,y,z)))
    rotations=np.array(rotations);headings=np.array([normalize(v) for v in x[:,idx('nose')]-x[:,idx('head')]])
    feet=x[:,[names.index(l['endpoint']) for l in config['limbs'].values()]];bends=x[:,[names.index(l['bend']) for l in config['limbs'].values()]]
    targets=feet.copy();core=raw_core.copy();contacts=np.zeros((len(x),4),bool)
    if extreme:
        # Authored contact schedule: four supports initially, rear supports throughout.
        radius=config['robot']['foot_radius'];anchor=feet[:20].mean(axis=0);anchor[:,2]=radius
        targets[:,2:]=anchor[None,2:];contacts[:,2:]=True
        weight=np.clip((42-np.arange(len(x)))/12,0,1);weight=weight*weight*(3-2*weight)
        targets[:,:2]=weight[:,None,None]*anchor[None,:2]+(1-weight[:,None,None])*feet[:,:2]
        targets[...,2]=np.maximum(targets[...,2],radius);contacts[:30,:2]=True
        # Geometry proxy only: steer body center over the two rear supports near the end.
        w=np.clip((np.arange(len(x))-30)/60,0,1);w=w*w*(3-2*w)
        support=anchor[2:,:2].mean(axis=0)
        core[:,:2]=(1-w[:,None])*core[:,:2]+w[:,None]*support
    if extreme:targets[:,:2]+=(core-raw_core)[:,None]
    direct=solve(core,rotations,targets,bends,contacts,config,extreme)
    if extreme:
        targets[:,:2]+=direct['root_correction'][:,None]
        direct=solve(direct['core'],rotations,targets,bends,contacts,config,False)
    clean=clean_bend_planes(direct,targets,rotations,headings,config)
    check=audit(clean['joints'],clean['core'],rotations,headings)
    errors=np.linalg.norm(clean['joints'][:,:,2]-targets,axis=-1)
    pitch=np.degrees(np.arctan2(-rotations[:,2,1],np.linalg.norm(rotations[:,:2,1],axis=-1)))
    result=dict(source_xyz=source_xyz,rotation=rotations,head_direction=headings,contacts=contacts,raw_targets=feet,clean_targets=targets,raw_core=raw_core)
    for mode,s in [('retarget',direct),('clean',clean)]:result.update({mode+'_'+k:v for k,v in s.items()})
    speeds=np.linalg.norm(np.diff(x[:,[0,17,29,23,14,8]],axis=0),axis=-1)*20
    metrics=dict(max_target_error=float(errors.max()),max_foot_correction=float(np.linalg.norm(targets-feet,axis=-1).max()),max_core_correction=float(np.linalg.norm(clean['core']-raw_core,axis=-1).max()),final_pitch_degrees=float(pitch[-1]),middle_pitch_range=[float(pitch[30:90].min()),float(pitch[30:90].max())],seam_max_step=float(max(speeds[29].max(),speeds[89].max())/20),max_frame_step=float(speeds.max()/20),min_front_foot_height_final=float(clean['joints'][90:,:2,2,2].min()),end_body_center_support_error=float(np.linalg.norm(clean['core'][90:,:2]-targets[90:,2:, :2].mean(axis=1),axis=-1).max()),collision={k:v for k,v in check.items() if k!='violations'})
    return result,metrics


def main():
    a=argparse.ArgumentParser();a.add_argument('directory',type=Path);a.add_argument('--robot-prefix',default='');a.add_argument('--only',nargs='*');cli=a.parse_args();out=cli.directory
    run=json.loads((out/'run.json').read_text());ref=json.loads((out.parent/'anytop_transfer_v1/retarget.json').read_text());config=ref['config'];report=[]
    clips=[dict(name='original',kind='natural',seed=100)]+run['clips']
    for c in clips:
        if cli.only and c['name'] not in cli.only:continue
        source=Path(run['source_features']).with_suffix('.xyz.npy') if c['name']=='original' else out/(c['name']+'.xyz.npy')
        arrays,metrics=build(np.load(source),config,ref,c['kind']=='rear_up')
        dest=out/(cli.robot_prefix+c['name']);dest.mkdir(exist_ok=False);np.savez_compressed(dest/'motion.npz',**arrays)
        record=dict(source=dict(id=c['name'],source=str(source)),config=config,fps=20,frames=120,units=ref['units'],joint_names=run['joint_names'],parents=run['parents'],metrics=metrics,kind=c['kind'])
        (dest/'retarget.json').write_text(json.dumps(record,indent=2)+'\n');report.append(dict(name=c['name'],kind=c['kind'],metrics=metrics));print('ROBOT',c['name'],json.dumps(metrics),flush=True)
    candidates=[c for c in report if c['kind']=='rear_up' and c['metrics']['max_target_error']<1e-5 and c['metrics']['collision']['intersection_count']==0]
    selected=min(candidates,key=lambda c:c['metrics']['seam_max_step'])['name'] if candidates else None
    (out/(cli.robot_prefix+'robot_analysis.json')).write_text(json.dumps(dict(selected_extreme=selected,clips=report),indent=2)+'\n');print('SELECTED',selected)

if __name__=='__main__':main()
