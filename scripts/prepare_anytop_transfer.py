"""Transfer an unfiltered AnyTop sample; preserve source timing and foot paths."""
import argparse, copy, hashlib, json
from pathlib import Path
import numpy as np
from motion_lab import normalize, to_blender
from retarget_motion import solve
from collision import clean_bend_planes, audit


def main():
    p=argparse.ArgumentParser();p.add_argument('analysis',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    analysis=json.loads(a.analysis.read_text())
    report=next(c for c in analysis['clips'] if c['id']=='Hound_seed0100_rep01')
    metadata_path=Path(report['source']);metadata=json.loads(metadata_path.read_text())
    xyz_path=metadata_path.with_suffix('.xyz.npy')
    original=np.load(xyz_path)
    xyz=to_blender(original).astype(float)
    config=copy.deepcopy(analysis['config'])
    for limb in config['limbs'].values():limb['hip'][0]=np.sign(limb['hip'][0])*.35
    names=metadata['joint_names']; idx=lambda key:names.index(config[key])
    scale=config['robot']['body_length']/report['body_length']
    origin=xyz[0,idx('root')].copy();origin[2]=report['estimated_ground']
    xyz=(xyz-origin)*scale;xyz[...,2]+=config['robot']['foot_radius']
    core=(xyz[:,idx('root')]+xyz[:,idx('chest')])/2
    rotations=[]
    for backward in xyz[:,idx('root')]-xyz[:,idx('chest')]:
        y=normalize(backward);x=normalize(np.cross(y,[0,0,1]));z=normalize(np.cross(x,y));rotations.append(np.column_stack((x,y,z)))
    rotations=np.array(rotations)
    feet=xyz[:,[names.index(l['endpoint']) for l in config['limbs'].values()]]
    bends=xyz[:,[names.index(l['bend']) for l in config['limbs'].values()]]
    headings=np.array([normalize(v) for v in xyz[:,idx('nose')]-xyz[:,idx('head')]])
    contacts=np.zeros((len(xyz),4),dtype=bool) # no artificial stance pinning
    direct=solve(core,rotations,feet,bends,contacts,config,False)
    clean=clean_bend_planes(direct,feet,rotations,headings,config)
    audits={label:audit(s['joints'],s['core'],rotations,headings) for label,s in [('direct',direct),('clean',clean)]}
    error=np.linalg.norm(clean['joints'][:,:,2]-feet,axis=-1)
    assert error.max()<1e-8,'Source endpoints were changed'
    assert audits['clean']['intersection_count']==0, 'Unresolved robot collision'
    arrays=dict(source_xyz=xyz,rotation=rotations,head_direction=headings,contacts=contacts,raw_targets=feet,clean_targets=feet)
    for label,s in [('retarget',direct),('clean',clean)]:arrays.update({label+'_'+k:v for k,v in s.items()})
    record=dict(schema=1,source=report,config=config,fps=metadata['fps'],frames=metadata['frames'],units='robot design units; body length 0.9',source_to_robot_scale=scale,origin_blender_units=origin.tolist(),source_xyz_path=str(xyz_path),source_xyz_sha256=hashlib.sha256(xyz_path.read_bytes()).hexdigest(),joint_names=names,parents=metadata['parents'],filtering='None; every source sample retained at original 20 fps',corrections='Static robot hip width 0.70; fixed-length IK and outward bend-plane collision cleanup. No foot pinning, foot offsets, root correction, temporal resampling or procedural gait.',metrics=dict(max_endpoint_error=float(error.max()),max_core_change=float(np.linalg.norm(clean['core']-core,axis=-1).max()),max_elbow_change=float(np.linalg.norm(clean['joints'][:,:,1]-direct['joints'][:,:,1],axis=-1).max()),endpoint_ranges=np.ptp(feet,axis=0).tolist()),collision=audits,interpretation='Genuine AnyTop standing weight shift, not walking. Source foot drift and variable source bone lengths are deliberately preserved.')
    a.output.mkdir(parents=True,exist_ok=False);np.savez_compressed(a.output/'motion.npz',**arrays);(a.output/'retarget.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(dict(metrics=record['metrics'],collisions={k:{x:v for x,v in val.items() if x!='violations'} for k,val in audits.items()}),indent=2))

if __name__=='__main__':main()
