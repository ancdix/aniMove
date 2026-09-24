"""Describe unguided phrases before assigning behavioral names or choreography."""
import argparse,json,csv
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d
from motion_lab import runs

def contacts(xyz,indices,fps=20,height=.10,speed=.30):
    tips=xyz[:,indices];vel=np.linalg.norm(np.gradient(gaussian_filter1d(tips,1,axis=0),1/fps,axis=0),axis=-1)
    mask=(abs(tips[:,:,1]-.06)<height)&(vel<speed)
    for j in range(4):
        for a,b in runs(mask[:,j]):
            if b-a<4:mask[a:b,j]=False
    return mask,vel

def describe(x,d):
    ix={n:i for i,n in enumerate(d['names'])};root=x[:,0];body=x[:,ix['SPINE_03']]-root
    across=(x[:,ix['A_0']]-x[:,ix['B_0']])+(x[:,ix['C_0']]-x[:,ix['D_0']]);yaw=np.unwrap(np.arctan2(-across[:,2],across[:,0]));pitch=np.arctan2(body[:,2],body[:,1]);roll=np.arctan2(body[:,0],body[:,1]);co,vel=contacts(x,d['contact_joints']);strict,_=contacts(x,d['contact_joints'],height=.06,speed=.20);loose,_=contacts(x,d['contact_joints'],height=.14,speed=.45)
    signatures=[]
    for li,k in enumerate('ABCD'):signatures.append(k+' '+''.join('█' if block.mean()>=.5 else '─' for block in np.array_split(co[:,li],30)))
    v=np.diff(x,axis=0)*20;a=np.diff(x,n=2,axis=0)*400;j=np.diff(x,n=3,axis=0)*8000
    head=x[:,ix['HEAD']]-root;span=lambda a:float(np.ptp(a));tip=x[:,d['contact_joints']];tipmotion=tip-tip[:1];asym=float(np.sqrt(np.mean((np.linalg.norm(tipmotion[:,0],axis=-1)-np.linalg.norm(tipmotion[:,1],axis=-1))**2)))
    degrees=lambda a:np.degrees(a)
    return dict(root_height_change=float(root[-1,1]-root[0,1]),root_height_range=span(root[:,1]),root_height_min=float(root[:,1].min()),torso_pitch_range_degrees=span(degrees(pitch)),torso_pitch_extremes_degrees=[float(degrees(pitch).min()),float(degrees(pitch).max())],torso_yaw_range_degrees=span(degrees(yaw)),torso_roll_range_degrees=span(degrees(roll)),head_displacement=float(np.linalg.norm(x[-1,ix['HEAD']]-x[0,ix['HEAD']])),relative_head_motion=float(np.linalg.norm(head-head[:1],axis=-1).max()),support_transitions=int(np.count_nonzero(np.diff(co.astype(int),axis=0))),support_state_changes=int(np.any(np.diff(co.astype(int),axis=0)!=0,axis=1).sum()),contacts={k:[[int(a),int(b)] for a,b in runs(co[:,li])] for li,k in enumerate('ABCD')},contact_fractions=co.mean(0).tolist(),contact_threshold_agreement=float((strict==loose).mean()),support_count_histogram={str(i):int((co.sum(1)==i).sum()) for i in range(5)},contact_signature=signatures,overall_displacement=float(np.linalg.norm((root[-1]-root[0])[[0,2]])),root_path_length=float(np.linalg.norm(np.diff(root[:,[0,2]],axis=0),axis=-1).sum()),min_joint_height=float(x[:,:,1].min()),tip_height_min=tip[:,:,1].min(0).tolist(),joint_speed_p95=float(np.percentile(np.linalg.norm(v,axis=-1),95)),joint_acceleration_p95=float(np.percentile(np.linalg.norm(a,axis=-1),95)),joint_jerk_p95=float(np.percentile(np.linalg.norm(j,axis=-1),95)),asymmetry=asym,pose_span=float(np.linalg.norm(x-x[:1],axis=-1).max()),loop_endpoint_rms=float(np.sqrt(np.mean(np.linalg.norm(x[-1]-x[0],axis=-1)**2))))

def main(p):
 run=json.loads((p/'run.json').read_text());d=json.loads((p/'skeleton.json').read_text());scale=run['normalized_units_per_design_meter'];results=[]
 for entry in run['clips']:
  if entry['object']!='Pilgrim':continue
  raw=np.load(p/(entry['name']+'.xyz.npy'))/scale+[0,.06,0];fit=np.load(p/(entry['name']+'.fitted.xyz.npy'))/scale+[0,.06,0];r=describe(raw,d);f=describe(fit,d)
  # Screening is a review aid: it does not equate more movement with better art.
  motion=min(1,r['pose_span']/.25);quality=entry['fit_rms_design_units']+.1*max(0,-r['min_joint_height'])+.02*r['joint_acceleration_p95']+.15*max(0,.3-r['root_height_min'])
  results.append(dict(name=entry['name'],family=entry['family'],seed=entry['seed'],fit_rms=entry['fit_rms_design_units'],fit_max=entry['fit_max_design_units'],raw=r,fitted=f,review_cost=float(quality-.015*motion)))
 results.sort(key=lambda r:r['review_cost']);report=dict(status='analyzed',clips=len(results),guidance='None',contact_note='Heuristic candidates from RAW positions near the declared floor and low 3D speed; no inferred load or physical balance. Strict/loose threshold agreement reports uncertainty. Fitted measurements are separate.',thresholds=dict(height_tolerance=.10,speed=.30,minimum_frames=4,strict=[.06,.20],loose=[.14,.45]),results=results)
 (p/'analysis.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
 with open(p/'catalog.csv','w') as handle:
  fields=['name','family','fit_rms','fit_max','review_cost','root_height_change','torso_pitch_range_degrees','torso_yaw_range_degrees','head_displacement','support_transitions','overall_displacement','pose_span','joint_acceleration_p95','asymmetry'];writer=csv.DictWriter(handle,fieldnames=fields);writer.writeheader()
  for r in results:writer.writerow({k:r.get(k,r['raw'].get(k)) for k in fields})
 print(json.dumps([dict(name=r['name'],fit=round(r['fit_rms'],3),motion=round(r['raw']['pose_span'],3),pitch=round(r['raw']['torso_pitch_range_degrees'],1),yaw=round(r['raw']['torso_yaw_range_degrees'],1),support=r['raw']['contact_fractions'],cost=round(r['review_cost'],3)) for r in results[:20]],indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('directory',type=Path);main(a.parse_args().directory)
