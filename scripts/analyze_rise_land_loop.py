"""Assess raw loop quality and landing-like cues before any IK or smoothing."""
import argparse,json
from pathlib import Path
import numpy as np


def raw_metrics(xyz,features,mask):
    body=float(np.median(np.linalg.norm(xyz[:10,17]-xyz[:10,0],axis=-1)))
    core=(xyz[:,0]+xyz[:,17])/2;direction=xyz[:,17]-xyz[:,0]
    pitch=np.degrees(np.arctan2(direction[:,1],np.linalg.norm(direction[:,[0,2]],axis=-1)))
    monitored=xyz[:,[0,17,29,23,14,8]]
    step=np.linalg.norm(np.diff(monitored,axis=0),axis=-1)
    fixed=mask.all(axis=(1,2));boundaries=np.flatnonzero(fixed[1:]!=fixed[:-1])
    torso=np.linalg.norm(direction,axis=-1)
    metrics=dict(body_length=body,max_step_body_lengths=float(step.max()/body),boundary_max_step_body_lengths=float(step[boundaries].max()/body),max_step_frame=int(np.unravel_index(np.argmax(step),step.shape)[0]+2),pitch_range=[float(pitch.min()),float(pitch.max())],torso_length_range_relative=[float(torso.min()/body),float(torso.max()/body)],raw_loop_position_error=float(np.linalg.norm(xyz[-1]-xyz[0],axis=-1).max()),raw_loop_velocity_error=float(np.linalg.norm((xyz[1]-xyz[0])-(xyz[-1]-xyz[-2]),axis=-1).max()*20))
    probes={}
    for joint,bend,upper,key in [(29,26,25,'front_left'),(23,20,19,'front_right')]:
        h=(xyz[:,joint,1]-xyz[:10,joint,1].mean())/body
        v=np.gradient(h)*20
        touch=None;early_touch=None
        for f in range(65,110):
            if f+2>=110:break
            if h[f]<=.035 and np.all(h[f:f+3]<=.06) and np.max(h[max(59,f-12):f])>.12:
                if f<83:
                    if early_touch is None:early_touch=f
                    continue
                touch=f;break
        a=xyz[:,upper]-xyz[:,bend];b=xyz[:,joint]-xyz[:,bend]
        flex=180-np.degrees(np.arccos(np.clip(np.sum(a*b,axis=-1)/(np.linalg.norm(a,axis=-1)*np.linalg.norm(b,axis=-1)),-1,1)))
        p=dict(height_reference='Each source foot at its initial rest height; not a calibrated physical floor.',minimum_landing_height_body_lengths=float(h[83:110].min()),maximum_landing_height_body_lengths=float(h[83:110].max()),touchdown_frame=None if touch is None else touch+1,early_contact_before_landing_probe_frame=None if early_touch is None else early_touch+1)
        if touch is not None:
            stop=min(110,touch+11)
            p.update(touchdown_in_generated_region=not bool(fixed[touch]),post_touch_generated_frames=int(sum(~fixed[touch:stop])),pre_touch_down_speed_body_lengths_per_second=float(max(0,-np.mean(v[max(60,touch-5):max(61,touch-2)]))),near_touch_down_speed_body_lengths_per_second=float(max(0,-np.mean(v[max(60,touch-2):touch+1]))),core_drop_after_touch_body_lengths=float((core[touch,1]-core[touch:stop,1].min())/body),front_limb_flexion_change_degrees=float(flex[touch:stop].max()-flex[touch]),model_contact_feature_at_touch=float(features[touch,joint,12]))
            low=touch+int(np.argmin(core[touch:stop,1]));p['core_rebound_after_minimum_body_lengths']=float((core[low:stop,1].max()-core[low,1])/body)
            p['all_post_touch_samples_generated']=bool(np.all(~fixed[touch:stop]))
        probes[key]=p
    metrics['landing_probes']=probes
    metrics['qualitative_gate_pass']=bool(metrics['max_step_body_lengths']<.5 and metrics['torso_length_range_relative'][0]>.65 and metrics['torso_length_range_relative'][1]<1.4)
    return metrics


def main():
    parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path);a=parser.parse_args();run=json.loads((a.directory/'run.json').read_text());results=[]
    for c in run['clips']:
        name=c['name'];xyz=np.load(a.directory/(name+'.xyz.npy'));features=np.load(a.directory/(name+'.npy'));mask=np.load(a.directory/(c['kind']+'_mask.npy'))
        m=raw_metrics(xyz,features,mask);results.append(dict(name=name,kind=c['kind'],seed=c['seed'],metrics=m));print(name,json.dumps(m),flush=True)
    paired=[]
    for c in results:
        if c['kind']=='waypoints':
            base=next(b for b in results if b['kind']=='endpoints' and b['seed']==c['seed'])
            paired.append(dict(seed=c['seed'],endpoints_max_step=base['metrics']['max_step_body_lengths'],waypoints_max_step=c['metrics']['max_step_body_lengths'],endpoints_boundary_step=base['metrics']['boundary_max_step_body_lengths'],waypoints_boundary_step=c['metrics']['boundary_max_step_body_lengths']))
    accepted=[c for c in results if c['kind'] in ('waypoints','body_guided') and c['metrics']['qualitative_gate_pass']]
    selected=min(accepted,key=lambda c:c['metrics']['max_step_body_lengths'])['name'] if accepted else None
    report=dict(selected=selected,clips=results,paired=paired,note='Landing statistics are kinematic observations, not validation of forces, physical balance, learned physics, or response to novel impacts. Contact search excludes the fixed ending window.')
    (a.directory/'raw_analysis.json').write_text(json.dumps(report,indent=2)+'\n');print('SELECTED',selected)

if __name__=='__main__':main()
