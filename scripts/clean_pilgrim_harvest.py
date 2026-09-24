"""Minimal contact edits: preserve fitted body, bend planes and distal directions."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d
from analyze_pilgrim_harvest import contacts,describe
from motion_lab import runs,normalize,two_bone
from pilgrim_skeleton import audit
from prepare_pilgrim_loop import stats,periodic_bridge

def cleanup(x,d,contact_mask):
    ix={n:i for i,n in enumerate(d['names'])};rest=np.array(d['rest']);out=x.copy();tips=x[:,d['contact_joints']].copy();weights=np.zeros(contact_mask.shape);anchor_paths=tips.copy();episodes={}
    for li,k in enumerate('ABCD'):
        episodes[k]=[]
        for a,b in runs(contact_mask[:,li]):
            anchor=np.median(tips[a:b,li],axis=0);anchor[1]=.06;episodes[k].append(dict(start=int(a),stop=int(b),anchor=anchor.tolist()))
            for f in range(a,b):
                u=min(1 if a==0 else min(1,(f-a+1)/4),1 if b==len(x) else min(1,(b-f)/4));w=u*u*(3-2*u);weights[f,li]=w;anchor_paths[f,li]=anchor
                tips[f,li]=(1-w)*tips[f,li]+w*anchor
        # Flat pad clearance; no artist-chosen horizontal hand path or bend sector.
        tips[:,li,1]=np.maximum(tips[:,li,1],.06)
    poles=[];reach=[]
    for f in range(len(x)):
        fp=[];fr=[]
        for k,li in zip('ABCD',range(4)):
            js=[ix[k+'_'+str(q)] for q in range(4)];lengths=np.linalg.norm(np.diff(rest[js],axis=0),axis=-1);distal=normalize(x[f,js[3]]-x[f,js[2]])*lengths[2]
            e,w,bend,error,_=two_bone(x[f,js[0]],tips[f,li]-distal,x[f,js[1]]-x[f,js[0]],*lengths[:2],(1,175))
            out[f,js[1]]=e;out[f,js[2]]=w;out[f,js[3]]=w+distal;fp.append(x[f,js[0]]+bend*.85);fr.append(error)
        poles.append(fp);reach.append(fr)
    return out,np.array(poles),weights,anchor_paths,episodes,float(np.max(reach))

def evaluate(p):
    report=json.loads((p/'analysis.json').read_text());run=json.loads((p/'run.json').read_text());d=json.loads((p/'skeleton.json').read_text());d['ring'].update(carrier='SPINE_02',axial_offset=-.05,limb_capsule_radius=.095);d['geometry']={'upper_shell_proximal_inset_fraction':.10};scale=run['normalized_units_per_design_meter'];results=[]
    for entry in report['results']:
        name=entry['name'];raw=np.load(p/(name+'.xyz.npy'))/scale+[0,.06,0];x=np.load(p/(name+'.fitted.xyz.npy'))/scale+[0,.06,0];co,_=contacts(raw,d['contact_joints']);clean,poles,w,a,episodes,reach=cleanup(x,d,co)
        # Preliminary proxy audit is decimated; selected assets receive full mesh checks.
        check=audit(d,clean[::3]);corr=stats(clean-x);total=stats(clean-raw);body=np.arange(7);support=float((co.sum(1)>=1).mean());motion=entry['raw']['pose_span'];reasons=[]
        if reach>.005:reasons.append('contact target exceeds reach')
        if corr['rms']>.08:reasons.append('cleanup RMS above 0.08')
        if total['rms']>.18:reasons.append('raw-to-final RMS above 0.18')
        if check['min_ring_limb_capsule_clearance']<0:reasons.append('ring proxy intersection')
        if check['min_interlimb_capsule_clearance']<0:reasons.append('limb proxy intersection')
        if check['min_joint_height']<.025:reasons.append('low limb joint')
        if support<.7:reasons.append('insufficient inferred support')
        if motion<.10:reasons.append('little movement')
        cost=total['rms']+corr['rms']+reach*3+max(0,-check['min_interlimb_capsule_clearance'])+max(0,-check['min_ring_limb_capsule_clearance'])
        results.append(dict(name=name,accepted=not reasons,reasons=reasons,cleanup=corr,total=total,reach=reach,proxy=check,support_fraction=support,body_change=float(np.linalg.norm(clean[:,body]-x[:,body],axis=-1).max()),cost=float(cost),episodes=episodes))
    results.sort(key=lambda r:(not r['accepted'],r['cost']));out=dict(scope='Candidate filter, not final mesh/artistic approval. No body guidance, smoothing, timewarp, hand lane offset or preferred bend sectors applied.',thresholds=dict(cleanup_rms=.08,total_rms=.18,reach=.005,supported_fraction=.7,motion_span=.10),results=results);(p/'cleanup_screen.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(results[:18],indent=2))

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('directory',type=Path);evaluate(a.parse_args().directory)
