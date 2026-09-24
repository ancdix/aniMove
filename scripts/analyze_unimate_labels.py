"""Paired label-only effects; distinguish altered poses from altered motion."""
import json
from pathlib import Path
import numpy as np
from compare_unimate_anytop import ROOT,scale,measure,ends
run=ROOT/'pilgrim_labels_001';manifest=json.loads((run/'run.json').read_text());assert manifest['status']=='generated_verified_label_only_requires_visual_review';records=[];lookup={}
for r in manifest['runs']:
    x=np.load(Path(r['path'])/'raw_fk.xyz.npy')/scale;lookup[r['variant'],r['prompt_id'],r['seed']]=x
    m=measure(x,30);v=np.gradient(x,1/30,axis=0);tip=x[:,ends];contact=(np.abs(tip[:,:,1])<.06)&(np.linalg.norm(v[:,ends],axis=-1)<.30);m['AB_candidate_fraction']=float(contact[:,:2].mean());m['CD_candidate_fraction']=float(contact[:,2:].mean());m['AB_min_height_m']=float(tip[:,:2,1].min());m['AB_mean_height_m']=float(tip[:,:2,1].mean());m['four_candidate_fraction']=float(contact.all(1).mean())
    records.append(dict(variant=r['variant'],prompt_id=r['prompt_id'],seed=r['seed'],repeat=r['repeat_control'],path=r['path'],metrics=m))
pairs=[]
rms=lambda d:float(np.sqrt(np.mean(np.sum(d*d,axis=-1))))
for seed in manifest['seeds']:
    for prompt in manifest['prompts']:
        baseline=lookup['arms_legs',prompt,seed]
        for variant in ['front_hind','neutral_limbs']:
            x=lookup[variant,prompt,seed];pairs.append(dict(variant=variant,prompt=prompt,seed=seed,world_position_rms_m=rms(x-baseline),root_relative_pose_rms_m=rms((x-x[:,0:1])-(baseline-baseline[:,0:1])),motion_change_rms_m=rms((x-x[:1])-(baseline-baseline[:1])),root_trajectory_rms_m=rms(x[:,0]-baseline[:,0])))
summary={}
for variant in ['front_hind','neutral_limbs']:
    subset=[p for p in pairs if p['variant']==variant];summary[variant]={k:dict(median=float(np.median([p[k] for p in subset])),min=float(min(p[k] for p in subset)),max=float(max(p[k] for p in subset))) for k in ['world_position_rms_m','root_relative_pose_rms_m','motion_change_rms_m']}
controls=[dict(prompt=p,world_rms_m=rms(lookup['arms_legs_repeat',p,9600]-lookup['arms_legs',p,9600])) for p in manifest['prompts']];assert all(c['world_rms_m']==0 for c in controls)
report=dict(status='paired_effects_measured',units='design m, same native30fps60frames; no alignment except explicitly named root-relative metric; no cleanup',conditions_verified=manifest['verification'],geometry='Identical in all variants, including upright rest pose and limb attachment points',controls=controls,summary=summary,pairs=pairs,records=records);(run/'paired_analysis.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(summary=summary,controls=controls),indent=2))
