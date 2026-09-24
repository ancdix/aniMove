"""Decode each stance in its own bind frame and screen uncorrected support."""
import json
from pathlib import Path
import numpy as np
from analyze_unimate_raw import decode,intervals,recover_unimate_anim_from_rot,offsets_from_positions,rotations_global
from compare_unimate_anytop import ROOT,scale,measure,ends
from unimate.utils.motion_utils import recover_unimate_joint_pos_from_ric
out=ROOT/'pilgrim_stance_001';m=json.loads((out/'run.json').read_text());assert len(m['runs'])==18
conds={v:np.load(out/'conditions'/v/'cond.npy',allow_pickle=True).item()['Pilgrim'] for v in m['variants']};records=[];lookup={}
for r in m['runs']:
    folder=Path(r['path']);f=next((folder/'samples/motions').glob('*.npy'));features=np.load(f);c=conds[r['variant']];assert features.shape==(60,23,12) and np.isfinite(features).all();x=decode(features,c);off=offsets_from_positions(np.asarray(c['tpos_first_frame']),np.asarray(c['parents']));anim=recover_unimate_anim_from_rot(features,np.asarray(c['parents']),off);q=rotations_global(anim).qs
    np.save(folder/'raw_fk.xyz.npy',x);np.savez_compressed(folder/'raw_kinematics.npz',positions=x,global_quaternions_wxyz=q,parents=c['parents'],names=c['joint_names'],fps=30)
    design=x/scale;lookup[r['variant'],r['prompt_id'],r['seed']]=design;metric=measure(design,30);tip=design[:,ends];speed=np.linalg.norm(np.gradient(design,1/30,axis=0)[:,ends],axis=-1);support={}
    for name,h,s in [('strict',.06,.30),('relaxed',.12,.60)]:
        mask=(abs(tip[:,:,1])<h)&(speed<s);ints={letter:intervals(mask[:,j],3) for j,letter in enumerate('ABCD')};support[name]=dict(intervals=ints,stance_frames=[sum(b-a for a,b in ints[k]) for k in 'ABCD'],lift_frames=(tip[:,:,1]>h+.05).sum(0).tolist(),two_candidates_fraction=float((mask.sum(1)>=2).mean()),four_candidates_fraction=float(mask.all(1).mean()))
    z=support['relaxed'];candidate=bool(metric['root_displacement_m']>.15 and min(z['stance_frames'])>=6 and min(z['lift_frames'])>=3 and z['two_candidates_fraction']>=.3)
    ric=recover_unimate_joint_pos_from_ric(features)/scale;metric['ric_vs_fk_joint_rms_m']=float(np.sqrt(np.mean(np.sum((ric-design)**2,axis=-1))));metric['AB_mean_height_m']=float(tip[:,:2,1].mean());metric['CD_mean_height_m']=float(tip[:,2:,1].mean())
    records.append(dict(**{k:r[k] for k in ['label','variant','prompt_id','prompt','seed','path','feature_sha256','cond_path']},metrics=metric,support=support,passes_permissive_walk_screen=candidate))
pairs=[]
for seed in m['seeds']:
    for pid in m['prompts']:
        a=lookup['upright',pid,seed];b=lookup['quadruped',pid,seed];r=next(r for r in m['runs'] if r['variant']=='upright' and r['seed']==seed and r['prompt_id']==pid);feature=np.load(next((Path(r['path'])/'samples/motions').glob('*.npy')))
        # Diagnostic counterfactual: identical upright rotations decoded in changed rest.
        counter=decode(feature,conds['quadruped'])/scale
        rms=lambda d:float(np.sqrt(np.mean(np.sum(d*d,axis=-1))))
        pairs.append(dict(seed=seed,prompt_id=pid,world_joint_rms_m=rms(b-a),root_relative_rms_m=rms((b-b[:,:1])-(a-a[:,:1])),quadruped_vs_redecode_upright_rms_m=rms(b-counter),counterfactual_note='Re-decoding upright features in quadruped rest is only a representation control, not another model-generated sample.'))
report=dict(status='measured_requires_visual_review',units='design meters, same scale, native30fps60frames',postprocessing='none',condition_audit='Only tpos_first_frame, tpos_first_frame_parents and offsets differ at generation; exact noise, text/name embeddings and topology match. Nine upright outputs reproduce prior baseline hashes exactly.',screen_note='Permissive heuristic is triage only. It can accept tumbling falsely; all candidates require visual review. No force/balance claims.',records=records,pairs=pairs,passes=[r['label']+'_'+str(r['seed']) for r in records if r['passes_permissive_walk_screen']]);(out/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passes=report['passes'],rows=[dict(variant=r['variant'],prompt=r['prompt_id'],seed=r['seed'],travel=round(r['metrics']['root_displacement_m'],2),stance=r['support']['relaxed']['stance_frames'],root=round(r['metrics']['root_height_mean_m'],2)) for r in records]),indent=2))
