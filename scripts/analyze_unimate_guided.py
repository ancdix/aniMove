"""Combine prompt-word and guided tests, decode own-rest FK, measure raw support."""
import json,hashlib,shutil
from pathlib import Path
import numpy as np
from analyze_unimate_raw import ROOT,decode,intervals,offsets_from_positions,recover_unimate_anim_from_rot,rotations_global
from compare_unimate_anytop import measure,scale,ends
out=ROOT/'pilgrim_guided_001';g=json.loads((out/'run.json').read_text());w=json.loads((ROOT/'pilgrim_animal_words_001/run.json').read_text());prior=json.loads((ROOT/'pilgrim_stance_001/run.json').read_text());c=np.load(out/'condition/cond.npy',allow_pickle=True).item()['Pilgrim'];off=offsets_from_positions(c['tpos_first_frame'],np.asarray(c['parents']));records=[];cases={};entries=[]
for seed in g['seeds']:
    cases['words_'+str(seed)]={'prompt':'Prompt wording: same quadrupedal skeleton and noise; stock adaptive solver','actions':[],'titles':['CREATURE','DOG','CAT']}
    for mode in ['creature','dog','cat']:
        r=next(q for q in prior['runs'] if q['variant']=='quadruped' and q['prompt_id']=='walk' and q['seed']==seed) if mode=='creature' else next(q for q in w['runs'] if q['label']==mode and q['seed']==seed)
        entry=dict(r,label='probe_words_'+mode,variant=mode,study='words',cond_path=str(out/'condition/cond.npy'),feature_sha256=hashlib.sha256(next((Path(r['path'])/'samples/motions').glob('*.npy')).read_bytes()).hexdigest());entries.append(entry);cases['words_'+str(seed)]['actions'].append('UNI_'+entry['label']+'_s'+str(seed))
        if mode!='creature':
            audit=json.loads((Path(r['path'])/'noise_audit.json').read_text());assert audit['draws'][0]['sha256']==next(q for q in prior['runs'] if q['variant']=='quadruped' and q['prompt_id']=='walk' and q['seed']==seed)['noise']['sha256']
    cases['guidance_'+str(seed)]={'prompt':g['prompt']+' | matched stock Euler solver','actions':[],'titles':['UNGUIDED EULER','3 SUPPORT POSES','3 POSES + ROOT PATH']}
    for mode in g['variants']:
        r=next(q for q in g['runs'] if q['variant']==mode and q['seed']==seed);entry=dict(r,label='probe_guided_'+mode,study='guidance');entries.append(entry);cases['guidance_'+str(seed)]['actions'].append('UNI_'+entry['label']+'_s'+str(seed))
known=decode(np.load(out/'authored_features.npy'),c)/scale
for r in entries:
    folder=Path(r['path']);feature=np.load(next((folder/'samples/motions').glob('*.npy')));x=decode(feature,c);anim=recover_unimate_anim_from_rot(feature,np.asarray(c['parents']),off)
    # Derived files in previous baseline are already present; don't overwrite its archive.
    dest=out/'review_data'/(r['label']+'_'+str(r['seed']));dest.mkdir(parents=True,exist_ok=True);np.save(dest/'raw_fk.xyz.npy',x);np.savez_compressed(dest/'raw_kinematics.npz',positions=x,global_quaternions_wxyz=rotations_global(anim).qs,parents=c['parents'],names=c['joint_names'],fps=30);r['source_path']=r['path'];r['path']=str(dest)
    y=x/scale;tip=y[:,ends];speed=np.linalg.norm(np.gradient(tip,1/30,axis=0),axis=-1);metric=measure(y,30);supports={}
    for k,h,s in [('strict',.06,.3),('relaxed',.12,.6)]:
        mask=(abs(tip[:,:,1])<h)&(speed<s);iv={v:intervals(mask[:,j],3) for j,v in enumerate('ABCD')};supports[k]=dict(stance_frames=[sum(b-a for a,b in iv[v]) for v in 'ABCD'],lift_frames=(tip[:,:,1]>h+.05).sum(0).tolist(),two_candidates_fraction=float((mask.sum(1)>=2).mean()),intervals=iv)
    z=supports['relaxed'];passed=metric['root_displacement_m']>.15 and min(z['stance_frames'])>=6 and min(z['lift_frames'])>=3 and z['two_candidates_fraction']>=.3
    # Exclude constrained anchor frames and immediate neighbours from free-span grounding metric.
    free=np.ones(60,bool)
    for f in [0,29,59]:free[max(0,f-1):min(60,f+2)]=False
    metric['free_span_tip_penetration_fraction']=float((tip[free,:,1]<-.06).mean());metric['free_span_two_candidates_fraction']=float((((abs(tip[free,:,1])<.12)&(speed[free]<.6)).sum(1)>=2).mean())
    if r['study']=='guidance':
        mask=np.load(out/(r['variant']+'_mask.npy'));delta=abs(feature-np.load(out/'authored_features.npy'));metric['constrained_feature_max_error']=float(delta[mask].max()) if mask.any() else 0.
        metric['anchor_root_relative_max_error_m']=float(np.linalg.norm(((y-y[:,:1])-(known-known[:,:1]))[[0,29,59]],axis=-1).max())
        metric['root_path_max_error_m']=float(np.linalg.norm(y[:,0]-known[:,0],axis=-1).max())
    records.append(dict(label=r['label'],seed=r['seed'],study=r['study'],variant=r['variant'],metrics=metric,support=supports,passes_permissive_screen=bool(passed)))
review=dict(status='measured_requires_visual_review',object='Pilgrim',cfg=3.,frames=60,fps=30,runs=entries,cases=cases,seeds=g['seeds'],cond_path=str(out/'condition/cond.npy'));(out/'review_run.json').write_text(json.dumps(review,indent=2)+'\n');(out/'analysis.json').write_text(json.dumps(dict(status='measured_requires_visual_review',records=records),indent=2)+'\n')
print(json.dumps([dict(label=r['label'],seed=r['seed'],travel=round(r['metrics']['root_displacement_m'],3),stance=r['support']['relaxed']['stance_frames'],passed=r['passes_permissive_screen'],anchor=r['metrics'].get('anchor_root_relative_max_error_m')) for r in records],indent=2))
