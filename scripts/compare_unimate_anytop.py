"""Compare uncorrected Pilgrim motions at native fps in common design units."""
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from analyze_unimate_raw import ROOT,intervals

run=ROOT/'pilgrim_harvest_001';old=ROOT.parent/'pilgrim_machine/motion_harvest_001'
cond=np.load(ROOT/'pilgrim_canonical_v002/cond.npy',allow_pickle=True).item()['Pilgrim'];v=json.loads((ROOT/'pilgrim_canonical_v002/asset_validation.json').read_text());scale=v['scale'];names=list(cond['joint_names']);parents=np.asarray(cond['parents']);rest=np.asarray(cond['tpos_first_frame'])/scale
ends=[names.index(n) for n in ['LeftFingers','RightFingers','LeftToes','RightToes']]
chains=[[names.index(n) for n in ns] for ns in [['LeftUpperArm','LeftForearm','LeftHand','LeftFingers'],['RightUpperArm','RightForearm','RightHand','RightFingers'],['LeftThigh','LeftShin','LeftFoot','LeftToes'],['RightThigh','RightShin','RightFoot','RightToes']]]

def measure(x,fps):
    vel=np.gradient(x,1/fps,axis=0);acc=np.gradient(vel,1/fps,axis=0);tip=x[:,ends];tv=np.linalg.norm(vel[:,ends],axis=-1)
    mask=(np.abs(tip[:,:,1])<.06)&(tv<.30);near=np.abs(tip[:,:,1])<.06
    contact={k:intervals(mask[:,j],minimum=round(.1*fps)) for j,k in enumerate('ABCD')}
    drift=[np.linalg.norm(tip[a:b,j]-tip[a,j],axis=-1).max() for j,k in enumerate('ABCD') for a,b in contact[k]]
    spine=x[:,names.index('UpperChest')]-x[:,0];pitch=np.degrees(np.arctan2(spine[:,2],spine[:,1]));roll=np.degrees(np.arctan2(spine[:,0],spine[:,1]));across=x[:,names.index('LeftUpperArm')]-x[:,names.index('RightUpperArm')];yaw=np.degrees(np.unwrap(np.arctan2(-across[:,2],across[:,0])))
    head=x[:,names.index('HeadTip')]-x[:,names.index('Head')];headelev=np.degrees(np.arctan2(head[:,1],np.linalg.norm(head[:,[0,2]],axis=-1)))
    # Conservative sampled centerline distance: 11 samples per segment, all pairs
    # from different limbs. Radius=.04m per strut. This is a review proxy only.
    cloud=[]
    for chain in chains:
        cloud.append(np.concatenate([x[:,[a]]*(1-np.linspace(0,1,11)[None,:,None])+x[:,[b]]*np.linspace(0,1,11)[None,:,None] for a,b in zip(chain[:-1],chain[1:])],axis=1))
    dmin=np.full(len(x),np.inf)
    for a in range(4):
        for b in range(a+1,4):dmin=np.minimum(dmin,np.linalg.norm(cloud[a][:,:,None]-cloud[b][:,None,:],axis=-1).min((1,2)))
    expected=np.linalg.norm(rest[1:]-rest[parents[1:]],axis=-1);actual=np.linalg.norm(x[:,1:]-x[:,parents[1:]],axis=-1)
    return dict(root_displacement_m=float(np.linalg.norm((x[-1,0]-x[0,0])[[0,2]])),root_height_change_m=float(x[-1,0,1]-x[0,0,1]),root_height_range_m=float(np.ptp(x[:,0,1])),root_height_mean_m=float(x[:,0,1].mean()),min_joint_height_m=float(x[:,:,1].min()),joint_speed_p95_m_s=float(np.percentile(np.linalg.norm(vel,axis=-1),95)),joint_acceleration_p95_m_s2=float(np.percentile(np.linalg.norm(acc,axis=-1),95)),near_floor_tip_speed_m_s=float(tv[near].mean()) if near.any() else None,candidate_contact_drift_max_m=float(max(drift,default=0)),contact_intervals=contact,tip_relative_motion_rms_m=[float(np.sqrt(np.mean(np.sum(((x[:,i]-x[:,0])-(x[:,i]-x[:,0]).mean(0))**2,axis=-1)))) for i in ends],torso_pitch_range_deg=float(np.ptp(pitch)),torso_yaw_range_deg=float(np.ptp(yaw)),torso_roll_range_deg=float(np.ptp(roll)),head_axis_elevation_range_deg=float(np.ptp(headelev)),interlimb_sampled_distance_min_m=float(dmin.min()),interlimb_proxy_overlap_fraction=float((dmin<.08).mean()),fixed_length_error_max_m=float(abs(actual-expected).max()))

def main():
    new=json.loads((run/'run.json').read_text());oldrun=json.loads((old/'run.json').read_text());oldskel=json.loads((old/'skeleton.json').read_text());ix=[oldskel['names'].index(v['canonical_to_original'][n]) for n in names];records=[]
    for r in new['runs']:
        x=np.load(Path(r['path'])/'raw_fk.xyz.npy')/scale
        records.append(dict(model='UniMate',label=r['label'],seed=r['seed'],prompt=r['prompt'],path=r['path'],metrics=measure(x,30)))
    for r in oldrun['clips']:
        if r['object']!='Pilgrim':continue
        x=np.load(old/(r['name']+'.xyz.npy'))[:40,ix]/oldrun['normalized_units_per_design_meter']
        records.append(dict(model='AnyTop',label=r['family'],seed=r['seed'],prompt=None,path=str(old/(r['name']+'.xyz.npy')),metrics=measure(x,20)))
    summary={}
    for model in ['UniMate','AnyTop']:
        rows=[r['metrics'] for r in records if r['model']==model];summary[model]={'n':len(rows)}
        for k,val in rows[0].items():
            if isinstance(val,(float,int)) or (val is None and any(isinstance(r[k],(float,int)) for r in rows)):
                z=[r[k] for r in rows if r[k] is not None];summary[model][k]={'median':float(np.median(z)),'min':float(min(z)),'max':float(max(z))}
    prompt_summary={}
    for label in new['prompts']:
        rows=[r['metrics'] for r in records if r['model']=='UniMate' and r['label']==label];prompt_summary[label]={'prompt':new['prompts'][label]}
        for k in ['root_displacement_m','root_height_change_m','root_height_mean_m','torso_yaw_range_deg','min_joint_height_m','joint_acceleration_p95_m_s2']:
            z=[r[k] for r in rows];prompt_summary[label][k]=[float(min(z)),float(np.median(z)),float(max(z))]
    out=dict(units='design meters; Y up; common declared canonical ground at zero; no per-clip regrounding',time='First 2 seconds at native rates: UniMate 60 frames/30fps, AnyTop40frames/20fps. Last sample times1.967s/1.95s.',contact_thresholds='No filtering; abs tip height < .06m, 3D speed < .30m/s, >=0.1s (3 UniMate / 2 AnyTop frames); near-floor tip speed also reported without speed cutoff. Candidate drift is selection-biased, not contact accuracy.',collision_proxy='Minimum sampled distance between different limb centerlines, 11samples/segment, .04m radius each. Approximate and omits torso/mesh; not collision-free certification.',limitations=['AnyTop is unguided; no symmetric text-adherence test','UniMate fixed lengths come from FK representation, not learned physics','Correction required is not measured: no cleanup allowed in this phase','Different model families, datasets and frame rates; descriptive comparison only'],summary=summary,prompt_summary=prompt_summary,records=records)
    (run/'raw_comparison.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(summary=summary,prompts=prompt_summary),indent=2))
if __name__=='__main__':main()
